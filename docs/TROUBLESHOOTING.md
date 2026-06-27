# Troubleshooting Guide

## Download Says "No Permissions"

**On GitHub**
- Download only from the **[Latest release](https://github.com/jonniethorpe45-max/Thorpe-Workforce/releases/latest)** page
- Draft releases (e.g. older v1.0.1) are **not public** — GitHub shows a permissions error for anonymous users
- Use the direct links in [INSTALLATION.md](INSTALLATION.md) or Thorpe → **Updates**

**After download (Windows)**
- Unsigned builds may show SmartScreen: click **More info → Run anyway**
- If the browser blocked the file, check Downloads → **Keep** or **Allow**

**After download (macOS)**
- Right-click the app → **Open** the first time to bypass Gatekeeper

## Application Won't Start

### Windows
- Ensure WebView2 Runtime is installed
- Run as administrator if permission errors occur
- Check Windows Event Viewer for crash logs

### macOS
- Right-click → Open if Gatekeeper blocks the app
- Ensure minimum macOS 10.15+

### Linux
- Install WebKit2GTK 4.1: `sudo apt install libwebkit2gtk-4.1-0`
- For AppImage: `chmod +x Thorpe*.AppImage`

## System Scan Issues

**"Consent Required"**
- Check the consent checkbox before scanning

**Scan returns incomplete data**
- Some data requires elevated permissions
- Run Thorpe with appropriate privileges for full diagnostics

## Jonathan AI Not Responding

**Local mode only**
- Cloud AI is disabled by default
- Enable in Settings > Jonathan AI with a valid API key

**API errors**
- Verify API key is correct
- Check network connectivity
- Verify base URL for custom providers

## Repair Actions Fail

**"Administrator privileges required"**
- Some repairs (Print Spooler, DNS flush) need elevated permissions
- On Windows: Run Thorpe as Administrator
- On Linux: Some actions may need sudo

## PDF Export Fails

- Requires Professional license
- Ensure write permissions to output directory
- Check disk space

## Database Issues

**Reset database**
1. Close Thorpe
2. Delete `thorpe.db` from app data directory
3. Restart Thorpe (database will be recreated)

**Or use Settings > Delete All User Data**

## Build Issues

See [BUILD.md](../BUILD.md) for build troubleshooting.

## Getting Further Help

- Ask Jonathan in the app
- Browse the Knowledge Base
- Open a GitHub issue for bugs
