# @scoutai/validation

Zod schemas for inbound API payloads aligned with `@scoutai/contracts` DTOs.

Validates registration and login requests, including password rules (minimum length,
letter and number required). Used at API boundaries before business logic runs.
