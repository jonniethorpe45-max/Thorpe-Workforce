# Thorpe Desktop

**Thorpe Desktop** is an enterprise-grade, AI-powered IT support application for Windows, macOS, and Linux. **Jonathan** is the built-in AI technician who diagnoses issues, runs safe repairs, and explains results in plain language.

## Features

- **Jonathan AI Assistant** — Autonomous local repairs with optional cloud AI
- **Offline connectivity diagnostics** — Layered network checks without internet
- **System Health Scanner** — OS, CPU, memory, disk, network, and process diagnostics
- **Diagnostic Reports** — AI-generated reports with health scores and PDF export
- **Repair Center** — Safe maintenance tools with explicit confirmation (Professional+)
- **Technician Workspace** — Cases, clients, and notes (Enterprise)
- **Enterprise AI Console** — Provider keys, budgets, and audit (Enterprise)
- **Intelligence Console** — Intel feed, repair packs, and org playbooks (Enterprise)
- **Licensing & Stripe billing** — Free, Professional, and Enterprise tiers

## Quick Start

### Prerequisites

- [Node.js](https://nodejs.org/) 18+
- [Rust](https://rustup.rs/) 1.70+
- [Tauri prerequisites](https://v2.tauri.app/start/prerequisites/)

### Development

```bash
npm install
bash scripts/generate-icons.sh   # first run
npm run tauri:dev
```

### Web preview (mock backend)

```bash
npm run dev
```

### Build installers

```bash
bash scripts/build.sh          # macOS / Linux
scripts\build-windows.bat      # Windows
```

See [BUILD.md](BUILD.md) and [docs/INSTALLATION.md](docs/INSTALLATION.md).

## Project structure

```text
src/                 React frontend (TypeScript + Tailwind)
src-tauri/           Rust backend (Tauri 2)
docs/                User and administrator guides
tools/license-server Stripe checkout + online activation
scripts/             Build, version checks, release verification
tests/               Unit and browser E2E tests
```

## Documentation

| Doc | Purpose |
|-----|---------|
| [THORPE.md](THORPE.md) | Product overview |
| [docs/API.md](docs/API.md) | Tauri command reference |
| [docs/INSTALLATION.md](docs/INSTALLATION.md) | Install and upgrade |
| [docs/ADMINISTRATOR_GUIDE.md](docs/ADMINISTRATOR_GUIDE.md) | Deployment and licensing |
| [docs/GA_CHECKLIST.md](docs/GA_CHECKLIST.md) | Release checklist |

## Quality gates

```bash
npm run lint
npm run test
npm run test:e2e
cd src-tauri && cargo test --lib
bash scripts/check-versions.sh
```

## License

Proprietary — see [LICENSE](LICENSE).
