# ScoutAI Privacy Model

**Architectural principles only.** This document describes privacy-by-design intent for ScoutAI. It does **not** constitute legal advice. **Legal counsel is required** before collecting real user data, especially data relating to minors, in any jurisdiction.

## Purpose

ScoutAI serves United States high school athletes (many of whom are minors), guardians, coaches, recruiters, and organizations. The privacy model ensures the platform:

1. Collects only data needed for stated product purposes.
2. Separates public profile display from restricted identity and contact data.
3. Respects guardian authority over minor accounts.
4. Supports future regulatory workflows (access, export, deletion) without architectural rework.

## Principles

### 1. Minimal collection

- Every field in the data model must have a documented purpose tied to a product capability.
- Prefer derived or user-supplied optional fields over invasive defaults (e.g., do not require full date of birth when graduation year suffices for recruiting context).
- Do not collect government IDs, precise geolocation, or biometric data in the foundation model unless a future feature explicitly requires them and counsel approves.
- Analytics and observability use pseudonymous identifiers; avoid shipping raw PII to third-party analytics without consent and DPA review.

### 2. Minor sensitivity

- Accounts may represent minors. The system assumes **minor-by-default** for high school athlete roles until age or guardian attestation indicates otherwise (**Future** verification).
- Restricted fields (contact info, guardian details, internal notes referencing minors) receive heightened access controls and audit logging.
- Marketing communications to minors require guardian consent where applicable (**Future** workflow).
- Public search and discovery features must not expose restricted fields by default (**Future**).

### 3. Guardian relationships

- A **Guardian** account links to one or more **Athlete** accounts through an explicit relationship record (not inferred from shared email).
- Link creation requires approval from both sides or org-mediated invitation (**Future** UX).
- Guardians can view and manage restricted settings for linked minors within policy bounds (**Future**).
- Athletes approaching majority may request independent control of their account per policy and law (**Future**).

### 4. Profile visibility foundation

Profile data is classified into visibility tiers at the schema and API layer:

| Tier | Examples | Default visibility |
| --- | --- | --- |
| **Public** | Sport, position, graduation year, public stats summaries | Entitled viewers per product rules |
| **Org** | Roster status, coach notes (non-recruiter) | Organization members |
| **Restricted** | Email, phone, address, guardian contact | Owner, linked guardian, entitled verified recruiter |
| **Private** | Recruiter private notes, internal admin flags | Owner only (see below) |

Stage 3 establishes user/role/org schema foundations; visibility enforcement on athlete profiles is **Future** (Stage 4+).

### 5. Future deletion and export

Architecture reserves:

- **Data export:** Machine-readable export of user-owned data per account (**Future**; GDPR/CCPA-style portability).
- **Deletion:** Soft-delete with tombstone + hard-delete worker job for erasure requests (**Future**).
- **Retention:** Configurable retention for audit logs and media; legal hold overrides erasure (**Future**).

Deletion must cascade or anonymize related records per counsel-approved schedule. Stage 3 does not implement self-service export/deletion endpoints.

### 6. Private recruiter notes

- Recruiter notes about athletes are **private to the creating recruiter** unless a future team-sharing feature is explicitly designed and consented to.
- Notes are not visible to athletes, guardians, coaches, or other recruiters by default.
- ScoutAI Admin access to notes is **support/legal only**, audit-logged, and discouraged for routine operations (**Future** policy).

### 7. Restricted contact info

- Contact fields are never included in public API DTOs or unauthenticated responses.
- Revealing contact info to a recruiter requires:
  1. Recruiter verification (**Future**),
  2. Active entitlement,
  3. Athlete/guardian consent or platform policy allowance,
  4. Audit event `contact.revealed` (**Future**).
- Bulk export of contact info is prohibited for non-admin roles.

## Data Residency and Processors

Stage 3 does not select production cloud regions or subprocessors. Before launch:

- Inventory third-party processors (hosting, email, AI, video CDN).
- Execute DPAs where required.
- Document subprocessor list in public privacy policy (**Future**).

## Engineering Obligations

1. Map Prisma models to API DTOs explicitly; never expose `restricted` columns via generic serializers.
2. Log access to restricted fields without logging field values.
3. Document new PII fields in this file or a domain addendum before merge.
4. Feature flags for discovery/search must default to off until privacy review passes.

## Legal Counsel Required

The following require qualified legal review before production use with real users:

- Terms of Service and Privacy Policy
- Minor consent and guardian verification flows
- FERPA-adjacent school data handling (if org integrations store educational records)
- State privacy laws (e.g., COPPA-aligned practices, state student data privacy statutes)
- Recruiter contact and NCAA/compliance messaging (product copy, not just engineering)

**This document guides engineering architecture only.** It does not satisfy regulatory compliance on its own.

## Related Documents

- `SECURITY.md` — technical controls
- `AUTHORIZATION_MATRIX.md` — role and entitlement matrix
- `AI_POLICY.md` — AI output labeling and data access limits
