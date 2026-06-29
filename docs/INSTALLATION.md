# Installation Guide

## Download

**Use the latest published release only:**  
https://github.com/jonniethorpe45-max/Thorpe-Workforce/releases/latest

Direct download links for **v1.0.8** (current latest):

| Platform | File | Link |
|----------|------|------|
| Windows | `.exe` installer | [Thorpe_1.0.8_x64-setup.exe](https://github.com/jonniethorpe45-max/Thorpe-Workforce/releases/download/v1.0.8/Thorpe_1.0.8_x64-setup.exe) |
| Windows | `.msi` installer | [Thorpe_1.0.8_x64_en-US.msi](https://github.com/jonniethorpe45-max/Thorpe-Workforce/releases/download/v1.0.8/Thorpe_1.0.8_x64_en-US.msi) |
| macOS (Apple Silicon) | `.dmg` | [Thorpe_1.0.8_aarch64.dmg](https://github.com/jonniethorpe45-max/Thorpe-Workforce/releases/download/v1.0.8/Thorpe_1.0.8_aarch64.dmg) |
| Linux | `.AppImage` | [Thorpe_1.0.8_amd64.AppImage](https://github.com/jonniethorpe45-max/Thorpe-Workforce/releases/download/v1.0.8/Thorpe_1.0.8_amd64.AppImage) |
| Linux | `.deb` | [Thorpe_1.0.8_amd64.deb](https://github.com/jonniethorpe45-max/Thorpe-Workforce/releases/download/v1.0.8/Thorpe_1.0.8_amd64.deb) |

> **“No permissions” when downloading?** This usually means the **filename does not exist** on the latest release (GitHub shows a permissions-style error for missing assets). Use the version-specific links above, open the **[Latest release](https://github.com/jonniethorpe45-max/Thorpe-Workforce/releases/latest)** page and click the asset directly, or use Thorpe → **Updates** (links load from GitHub automatically). Draft releases are not public.

## System Requirements

| Platform | Minimum Version | RAM | Disk |
|----------|----------------|-----|------|
| Windows | 10 (1809+) | 4 GB | 200 MB |
| macOS | 11+ (Apple Silicon build) | 4 GB | 200 MB |
| Linux | Ubuntu 20.04+ / equivalent | 4 GB | 200 MB |

## Windows

1. Download `Thorpe_1.0.8_x64-setup.exe` using the link above
2. Run the installer
3. If Windows SmartScreen appears, choose **More info → Run anyway** (the build is unsigned)
4. Launch Thorpe from the Start Menu

**Alternative:** Use the MSI installer for enterprise deployment via Group Policy.

## macOS

1. Download `Thorpe_1.0.8_aarch64.dmg`
2. Open the DMG file
3. Drag Thorpe to Applications
4. Right-click → Open on first launch (if Gatekeeper prompts)

## Linux

### AppImage (recommended)

```bash
chmod +x Thorpe_1.0.8_amd64.AppImage
./Thorpe_1.0.8_amd64.AppImage
```

### Debian/Ubuntu (.deb)

```bash
sudo dpkg -i Thorpe_1.0.8_amd64.deb
sudo apt-get install -f  # resolve dependencies if needed
```

## Building from Source

See [BUILD.md](../BUILD.md) for developer build instructions.

## First Launch

1. Review the privacy notice
2. Set up your profile in Settings
3. Run your first System Health Scan
4. Meet Jonathan, your AI IT technician

## Optional: Cloud AI

To enable enhanced AI responses:

1. Obtain an OpenAI API key
2. Go to Settings → Jonathan AI
3. Enable cloud AI and enter your API key

Cloud AI is optional. Jonathan provides local guidance without it.
