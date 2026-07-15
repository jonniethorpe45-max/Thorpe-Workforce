# @scoutai/billing

Billing and entitlement provider abstraction for ScoutAI feature gating.

Defines `BillingProvider` stubs and `Entitlement` types. `MockBillingProvider` returns
empty entitlements for local development until a real billing integration is wired.
