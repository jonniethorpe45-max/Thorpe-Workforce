# Changelog

All notable changes to Thorpe are documented in this file.

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
