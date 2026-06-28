# Changelog

All notable changes to Thorpe are documented in this file.

## [1.1.0] - 2026-06-27

### Added

- **Senior Engineer Platform**: Jonathan agent planner, evidence collectors, intel/RAG, repair packs, watchdog, PSA webhooks, Intelligence Console
- **Ed25519 repair pack signing** with `thorpe-pack-sign` CLI (legacy HMAC still supported)
- **Real update checker** via GitHub Releases API
- Optional online license activation via `THORPE_LICENSE_API_URL`
- Per-message repair approval in Jonathan chat

### Changed

- Enterprise tier marketing aligned to shipped features (Technician Workspace, AI Console, Intelligence Console)
- Demo license keys restricted to debug builds with 30-day evaluation expiry
- Version alignment across `package.json`, `Cargo.toml`, and `tauri.conf.json`

### Security

- License gates on intelligence commands
- SSRF protection for outbound HTTPS
- Repair pack whitelist validation

## [1.0.8] - 2026-06-28

### Fixed

- Jonathan page now correctly shows **Cloud AI mode** when enabled (banner no longer always says autonomous mode)
- Cloud AI requires a saved API key when enabling in Settings
- Clearer chat labels: Cloud AI, Cloud AI (local fallback), or Cloud AI not configured
- Settings page shows live Cloud AI activation status

## [1.0.7] - 2026-06-28

### Added

- Jonathan addresses the logged-in user by **first name** in chat, dashboard, and cloud AI responses
- First name is derived from the profile **Display Name** in Settings

## [1.0.6] - 2026-06-28

### Changed

- Updated logo and imagery to match the official Thorpe brand style guide
- Shield logo with metallic 3D **T**, horizontal/stacked lockups, and rounded-square app icon
- Jonathan avatar redesigned as circular line-art portrait with glasses and headset
- Brand palette aligned to Deep Navy (`#0B1220`); display font switched to **Sora**

## [1.0.5] - 2026-06-28

### Added

- Jonathan chat replies now type out **one word at a time** with a speaking-style cursor for a more conversational feel
- Repair results and source labels appear after typing completes

## [1.0.4] - 2026-06-28

### Changed

- **Jonathan AI** now acts as an autonomous IT technician — diagnoses issues and executes repairs automatically instead of providing manual troubleshooting steps
- Repair planner maps user messages and scan data to appropriate repair actions (Wi-Fi, performance, disk, printer, etc.)
- Chat responses report completed fixes in past tense with a repairs-executed summary in the UI
- Free tier includes `jonathan_auto_repair` for autonomous chat repairs

### Fixed

- CI Rust job now builds the frontend before `cargo check` so Tauri context generation succeeds

## [1.0.0] - 2026-06-27

### Added

- Initial release of Thorpe desktop application
- Jonathan AI Assistant with local and cloud AI modes
- System Health Scanner with consent-based diagnostics
- AI Diagnostic Reports with health scores and PDF export
- Repair Center with safe maintenance tools
- Technician Workspace for case and client management
- Knowledge Base with 10 seeded troubleshooting articles
- Settings with profile, AI configuration, and data deletion
- Licensing system with Free, Professional, and Enterprise tiers
- Update Manager for version checking
- SQLite database with full schema
- Cross-platform support (Windows, macOS, Linux)
- Dark mode premium UI with sidebar navigation
- Notification center
- Comprehensive documentation
- Test suite for UI, AI, scanner, licensing, and database logic
- Build scripts for all platform installers

### Security

- Local-first data storage
- Explicit consent for all diagnostic and repair operations
- AI security boundaries (no credential requests)
- User-controlled data deletion
- CSP configuration
- Backend license enforcement for repairs, reports, and PDF export
- HMAC-signed license key validation
- API keys stored in OS keyring with encrypted fallback
- Safe chat rendering (no HTML injection)
- PDF export path validation and save dialog
