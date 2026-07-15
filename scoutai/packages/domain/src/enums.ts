export const UserStatus = {
  ACTIVE: 'ACTIVE',
  DISABLED: 'DISABLED',
  PENDING: 'PENDING',
} as const;
export type UserStatus = (typeof UserStatus)[keyof typeof UserStatus];

export const UserRoleType = {
  ATHLETE: 'ATHLETE',
  GUARDIAN: 'GUARDIAN',
  RECRUITER: 'RECRUITER',
  COACH: 'COACH',
  ORGANIZATION_ADMIN: 'ORGANIZATION_ADMIN',
  SCOUTAI_ADMIN: 'SCOUTAI_ADMIN',
} as const;
export type UserRoleType = (typeof UserRoleType)[keyof typeof UserRoleType];

export const OrganizationType = {
  HIGH_SCHOOL: 'HIGH_SCHOOL',
  CLUB: 'CLUB',
  COLLEGE_PROGRAM: 'COLLEGE_PROGRAM',
  OTHER: 'OTHER',
} as const;
export type OrganizationType = (typeof OrganizationType)[keyof typeof OrganizationType];

export const MembershipStatus = {
  ACTIVE: 'ACTIVE',
  INVITED: 'INVITED',
  REMOVED: 'REMOVED',
} as const;
export type MembershipStatus = (typeof MembershipStatus)[keyof typeof MembershipStatus];

export const RecruiterVerificationStatus = {
  UNVERIFIED: 'UNVERIFIED',
  PENDING: 'PENDING',
  VERIFIED: 'VERIFIED',
  REJECTED: 'REJECTED',
} as const;
export type RecruiterVerificationStatus =
  (typeof RecruiterVerificationStatus)[keyof typeof RecruiterVerificationStatus];

export const GuardianRelationshipStatus = {
  PENDING: 'PENDING',
  ACTIVE: 'ACTIVE',
  REVOKED: 'REVOKED',
} as const;
export type GuardianRelationshipStatus =
  (typeof GuardianRelationshipStatus)[keyof typeof GuardianRelationshipStatus];
