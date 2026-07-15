import { PrismaClient } from '@prisma/client';

export {
  PrismaClient,
  Prisma,
  UserStatus,
  UserRoleType,
  OrganizationType,
  MembershipStatus,
  RecruiterVerificationStatus,
  GuardianRelationshipStatus,
  OrganizationMemberRole,
} from '@prisma/client';

export type {
  User,
  UserRole,
  Session,
  AuditEvent,
  Organization,
  OrganizationMember,
  Athlete,
  Recruiter,
  GuardianRelationship,
} from '@prisma/client';

const globalForPrisma = globalThis as unknown as { scoutaiPrisma?: PrismaClient };

export function createPrismaClient(databaseUrl?: string): PrismaClient {
  return new PrismaClient(
    databaseUrl
      ? {
          datasources: {
            db: { url: databaseUrl },
          },
        }
      : undefined,
  );
}

export function getPrismaClient(): PrismaClient {
  if (!globalForPrisma.scoutaiPrisma) {
    globalForPrisma.scoutaiPrisma = createPrismaClient();
  }
  return globalForPrisma.scoutaiPrisma;
}

export async function checkDatabaseConnectivity(
  client: PrismaClient = getPrismaClient(),
): Promise<boolean> {
  await client.$queryRaw`SELECT 1`;
  return true;
}
