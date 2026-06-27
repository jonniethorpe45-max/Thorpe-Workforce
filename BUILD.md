# Build Instructions

## Prerequisites

### All Platforms

- Node.js 18 or later
- Rust 1.70 or later (via [rustup](https://rustup.rs/))
- npm 9+

### Windows

- Microsoft Visual Studio C++ Build Tools
- WebView2 (pre-installed on Windows 10/11)

### macOS

- Xcode Command Line Tools: `xcode-select --install`

### Linux (Debian/Ubuntu)

```bash
sudo apt update
sudo apt install -y \
  libwebkit2gtk-4.1-dev \
  build-essential \
  curl \
  wget \
  file \
  libssl-dev \
  libayatana-appindicator3-dev \
  librsvg2-dev
```

## Development Build

```bash
npm install
bash scripts/generate-icons.sh
npm run tauri:dev
```

## Production Build

```bash
bash scripts/build.sh
```

Or step by step:

```bash
npm install
bash scripts/generate-icons.sh
npm run build          # Build React frontend
npm run tauri:build    # Build Tauri app + installers
```

## Output Artifacts

After a successful build, installers are located in:

```
src-tauri/target/release/bundle/
├── deb/          # Linux .deb package
├── appimage/     # Linux AppImage
├── dmg/          # macOS disk image
├── msi/          # Windows MSI installer
└── nsis/         # Windows NSIS .exe installer
```

## Platform-Specific Notes

### Windows

- NSIS installer is the default `.exe` installer
- MSI is also generated (optional)
- Some repair actions (Print Spooler restart) require administrator privileges

### macOS

- Universal builds require building on macOS
- Code signing and notarization are required for distribution outside the App Store
- Set `APPLE_SIGNING_IDENTITY` for signed builds

### Linux

- AppImage works on most distributions without installation
- `.deb` package for Debian/Ubuntu-based systems
- Ensure WebKit2GTK 4.1 is available on target systems

## Environment Variables

Copy `.env.example` to `.env` for optional configuration:

```bash
cp .env.example .env
```

| Variable | Description |
|----------|-------------|
| `OPENAI_API_KEY` | OpenAI API key for cloud AI |
| `OPENAI_MODEL` | Model name (default: gpt-4o-mini) |
| `OPENAI_BASE_URL` | API base URL |

## Cross-Compilation

Tauri supports cross-compilation via GitHub Actions. See `.github/workflows/` for CI build configurations.

## Troubleshooting Builds

- **Rust not found**: Run `rustup update stable`
- **WebView2 missing (Windows)**: Install from Microsoft
- **webkit2gtk not found (Linux)**: Install dev package listed above
- **Icon errors**: Run `bash scripts/generate-icons.sh`
