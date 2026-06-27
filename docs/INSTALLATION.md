# Installation Guide

## System Requirements

| Platform | Minimum Version | RAM | Disk |
|----------|----------------|-----|------|
| Windows | 10 (1809+) | 4 GB | 200 MB |
| macOS | 10.15 Catalina | 4 GB | 200 MB |
| Linux | Ubuntu 20.04+ / equivalent | 4 GB | 200 MB |

## Windows

1. Download `Thorpe_1.0.0_x64-setup.exe` from the releases page
2. Run the installer
3. Follow the setup wizard
4. Launch Thorpe from the Start Menu

**Alternative:** Use the MSI installer for enterprise deployment via Group Policy.

## macOS

1. Download `Thorpe_1.0.0_universal.dmg`
2. Open the DMG file
3. Drag Thorpe to Applications
4. Right-click → Open on first launch (if Gatekeeper prompts)

## Linux

### AppImage (recommended)

```bash
chmod +x Thorpe_1.0.0_amd64.AppImage
./Thorpe_1.0.0_amd64.AppImage
```

### Debian/Ubuntu (.deb)

```bash
sudo dpkg -i thorpe_1.0.0_amd64.deb
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
