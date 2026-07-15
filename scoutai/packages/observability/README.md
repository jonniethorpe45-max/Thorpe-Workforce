# @scoutai/observability

Structured logging and request correlation utilities for ScoutAI services.

Emits JSON log lines with timestamp, level, service, requestId, event, and optional userId.
Sensitive fields such as passwords and secrets are redacted before serialization.
