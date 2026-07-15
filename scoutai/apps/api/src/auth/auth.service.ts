import {
  ConflictException,
  Inject,
  Injectable,
  UnauthorizedException,
} from '@nestjs/common';
import { Argon2PasswordHasher } from '@scoutai/auth';
import { Prisma } from '@scoutai/database';
import { AuditService } from '../audit/audit.service';
import { toPublicUser } from '../common/user.mapper';
import { PrismaService } from '../database/prisma.service';
import { normalizeEmail } from './auth.utils';
import { SessionService } from './session.service';

@Injectable()
export class AuthService {
  private readonly passwordHasher = new Argon2PasswordHasher();

  constructor(
    @Inject(PrismaService) private readonly prisma: PrismaService,
    @Inject(SessionService) private readonly sessionService: SessionService,
    @Inject(AuditService) private readonly auditService: AuditService,
  ) {}

  async register(input: {
    email: string;
    password: string;
    requestId: string;
    ipAddress?: string;
    userAgent?: string;
  }) {
    const normalizedEmail = normalizeEmail(input.email);
    const passwordHash = await this.passwordHasher.hash(input.password);

    let user;
    try {
      user = await this.prisma.client.user.create({
        data: {
          email: input.email.trim(),
          normalizedEmail,
          passwordHash,
          status: 'ACTIVE',
        },
        include: { roles: true },
      });
    } catch (error) {
      if (
        error instanceof Prisma.PrismaClientKnownRequestError &&
        error.code === 'P2002'
      ) {
        throw new ConflictException({
          code: 'EMAIL_ALREADY_EXISTS',
          message: 'A user with this email already exists',
        });
      }
      throw error;
    }

    const session = await this.sessionService.createSession(user.id, {
      ipAddress: input.ipAddress,
      userAgent: input.userAgent,
    });

    await this.auditService.record({
      actorType: 'user',
      actorId: user.id,
      action: 'user.registered',
      targetType: 'user',
      targetId: user.id,
      requestId: input.requestId,
    });

    return {
      user: toPublicUser(user),
      sessionToken: session.rawToken,
    };
  }

  async login(input: {
    email: string;
    password: string;
    requestId: string;
    ipAddress?: string;
    userAgent?: string;
  }) {
    const normalizedEmail = normalizeEmail(input.email);
    const user = await this.prisma.client.user.findUnique({
      where: { normalizedEmail },
      include: { roles: true },
    });

    if (!user || user.status !== 'ACTIVE') {
      throw new UnauthorizedException({
        code: 'INVALID_CREDENTIALS',
        message: 'Invalid email or password',
      });
    }

    const valid = await this.passwordHasher.verify(input.password, user.passwordHash);
    if (!valid) {
      throw new UnauthorizedException({
        code: 'INVALID_CREDENTIALS',
        message: 'Invalid email or password',
      });
    }

    const session = await this.sessionService.createSession(user.id, {
      ipAddress: input.ipAddress,
      userAgent: input.userAgent,
    });

    await this.auditService.record({
      actorType: 'user',
      actorId: user.id,
      action: 'user.login.success',
      targetType: 'user',
      targetId: user.id,
      requestId: input.requestId,
    });

    return {
      user: toPublicUser(user),
      sessionToken: session.rawToken,
    };
  }

  async logout(input: { rawToken: string | null; requestId: string; actorId?: string }) {
    if (!input.rawToken) {
      return { revoked: false };
    }

    const session = await this.sessionService.findValidSession(input.rawToken);
    const revoked = await this.sessionService.revokeSession(input.rawToken);

    if (revoked && session) {
      await this.auditService.record({
        actorType: 'user',
        actorId: session.user.id,
        action: 'user.logout',
        targetType: 'session',
        targetId: session.id,
        requestId: input.requestId,
      });
    }

    return { revoked };
  }
}
