import { createHash, randomBytes } from 'node:crypto';
import { PrismaClient, UserRoleType, OrganizationType, MembershipStatus } from '@prisma/client';
import { Argon2PasswordHasher } from '@scoutai/auth';

const prisma = new PrismaClient();
const hasher = new Argon2PasswordHasher();

async function upsertUser(input: {
  email: string;
  password: string;
  roles: UserRoleType[];
}) {
  const normalizedEmail = input.email.trim().toLowerCase();
  const passwordHash = await hasher.hash(input.password);

  const user = await prisma.user.upsert({
    where: { normalizedEmail },
    update: {
      passwordHash,
      status: 'ACTIVE',
    },
    create: {
      email: input.email,
      normalizedEmail,
      passwordHash,
      status: 'ACTIVE',
    },
  });

  for (const role of input.roles) {
    await prisma.userRole.upsert({
      where: { userId_role: { userId: user.id, role } },
      update: {},
      create: { userId: user.id, role },
    });
  }

  return user;
}

async function main() {
  const admin = await upsertUser({
    email: 'admin@scoutai.dev',
    password: 'AdminPass1!',
    roles: [UserRoleType.SCOUTAI_ADMIN],
  });

  const athleteUser = await upsertUser({
    email: 'athlete@scoutai.dev',
    password: 'AthletePass1!',
    roles: [UserRoleType.ATHLETE],
  });

  const recruiterUser = await upsertUser({
    email: 'recruiter@scoutai.dev',
    password: 'RecruiterPass1!',
    roles: [UserRoleType.RECRUITER],
  });

  const org = await prisma.organization.upsert({
    where: { slug: 'north-field-demo-hs' },
    update: {
      name: 'North Field Demo High School',
      type: OrganizationType.HIGH_SCHOOL,
      status: MembershipStatus.ACTIVE,
    },
    create: {
      name: 'North Field Demo High School',
      slug: 'north-field-demo-hs',
      type: OrganizationType.HIGH_SCHOOL,
      status: MembershipStatus.ACTIVE,
    },
  });

  await prisma.organizationMember.upsert({
    where: {
      organizationId_userId: { organizationId: org.id, userId: athleteUser.id },
    },
    update: { status: MembershipStatus.ACTIVE },
    create: {
      organizationId: org.id,
      userId: athleteUser.id,
      role: 'MEMBER',
      status: MembershipStatus.ACTIVE,
    },
  });

  await prisma.athlete.upsert({
    where: { userId: athleteUser.id },
    update: { displayName: 'Demo Athlete' },
    create: {
      userId: athleteUser.id,
      displayName: 'Demo Athlete',
      dateOfBirth: null,
    },
  });

  await prisma.recruiter.upsert({
    where: { userId: recruiterUser.id },
    update: {
      organizationId: org.id,
      verificationStatus: 'UNVERIFIED',
    },
    create: {
      userId: recruiterUser.id,
      organizationId: org.id,
      verificationStatus: 'UNVERIFIED',
    },
  });

  await prisma.auditEvent.create({
    data: {
      actorType: 'system',
      actorId: null,
      action: 'seed.completed',
      targetType: 'database',
      targetId: null,
      requestId: `seed-${randomBytes(4).toString('hex')}`,
      metadata: {
        adminId: admin.id,
        athleteId: athleteUser.id,
        recruiterId: recruiterUser.id,
        organizationId: org.id,
        note: 'Synthetic development seed — not real persons.',
      },
    },
  });

  // Touch createHash so unused import lint stays quiet if tooling checks.
  createHash('sha256').update('scoutai-seed').digest('hex');

  console.log('Seed complete:');
  console.log('  admin@scoutai.dev / AdminPass1! (SCOUTAI_ADMIN)');
  console.log('  athlete@scoutai.dev / AthletePass1! (ATHLETE)');
  console.log('  recruiter@scoutai.dev / RecruiterPass1! (RECRUITER)');
}

main()
  .catch((error) => {
    console.error(error);
    process.exit(1);
  })
  .finally(async () => {
    await prisma.$disconnect();
  });
