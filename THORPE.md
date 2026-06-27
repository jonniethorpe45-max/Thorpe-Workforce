# Thorpe

**Thorpe** is an enterprise-grade, AI-powered IT support desktop application. **Jonathan** is the built-in AI technician who helps users diagnose, understand, and resolve computer issues across Windows, macOS, and Linux.

## Features

- **Jonathan AI Assistant** — Knowledgeable IT technician with local and cloud AI modes
- **System Health Scanner** — Consent-based diagnostics for OS, CPU, memory, disk, network, and processes
- **Diagnostic Reports** — AI-generated reports with health scores, findings, and PDF export
- **Repair Center** — Safe maintenance tools with explicit user confirmation
- **Technician Workspace** — Case management, client records, and technician notes (Enterprise)
- **Knowledge Base** — Expandable library of troubleshooting guides
- **Licensing** — Free, Professional, and Enterprise tiers with feature gating
- **Update Manager** — Check for application updates

## Quick Start

### Prerequisites

- [Node.js](https://nodejs.org/) 18+
- [Rust](https://rustup.rs/) 1.70+
- Platform dependencies for [Tauri](https://v2.tauri.app/start/prerequisites/)

### Development

```bash
# Install dependencies
npm install

# Generate app icons
bash scripts/generate-icons.sh

# Run in development mode
npm run tauri:dev
```

### Web Preview (without Tauri)

```bash
npm install
npm run dev
```

The web preview uses mock data for UI development.

### Build Installers

```bash
bash scripts/build.sh
```

See [BUILD.md](BUILD.md) for platform-specific build instructions.

## Project Structure

```
src/                  React frontend (TypeScript + Tailwind)
  components/         UI components
  pages/              Application pages (10 modules)
  services/           API layer and state management
  prompts/            Jonathan AI prompt templates
  database/           Frontend database types and helpers
src-tauri/            Rust backend (Tauri)
  src/                Scanner, repairs, AI, SQLite, PDF
docs/                 User and developer documentation
scripts/              Build and utility scripts
tests/                Test suite
```

## Technology Stack

- **Tauri 2** — Cross-platform desktop framework
- **React 18** — UI framework
- **TypeScript** — Type safety
- **Tailwind CSS** — Styling
- **Rust** — System diagnostics and backend
- **SQLite** — Local data storage
- **OpenAI API** — Optional cloud AI (with provider abstraction)

## Security & Privacy

Thorpe is local-first by design:

- All data stored locally in SQLite
- Explicit consent before scans and repairs
- No credential harvesting, keylogging, or spyware
- No hidden monitoring or remote control
- User-controlled data deletion

See [SECURITY.md](SECURITY.md) and [PRIVACY.md](PRIVACY.md).

## License Tiers

| Feature | Free | Professional | Enterprise |
|---------|------|-------------|------------|
| Jonathan AI | ✓ | ✓ | ✓ |
| Basic Scans | ✓ | ✓ | ✓ |
| Full Diagnostics | | ✓ | ✓ |
| Repair Center | | ✓ | ✓ |
| PDF Export | | ✓ | ✓ |
| Technician Workspace | | | ✓ |
| Multi-device | | | ✓ |

Demo license keys: `PRO-DEMO-1234`, `ENT-DEMO-5678`

## Documentation

- [BUILD.md](BUILD.md) — Build instructions
- [docs/USER_GUIDE.md](docs/USER_GUIDE.md) — User guide
- [docs/DEVELOPER_GUIDE.md](docs/DEVELOPER_GUIDE.md) — Developer guide
- [docs/ADMINISTRATOR_GUIDE.md](docs/ADMINISTRATOR_GUIDE.md) — Administrator guide
- [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) — Troubleshooting
- [docs/API.md](docs/API.md) — Tauri command API reference

## Testing

```bash
npm run test
bash scripts/test.sh
```

## Related

This repository also contains the Thorpe Workforce SaaS platform in `backend/` and `frontend/`. The Thorpe desktop IT support application is the primary deliverable at the repository root.
