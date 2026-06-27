# Administrator Guide

## Deployment

### Windows

Deploy via NSIS `.exe` installer or MSI package. Use Group Policy or MDM for enterprise rollout.

```powershell
# Silent install (NSIS)
Thorpe_1.0.0_x64-setup.exe /S
```

### macOS

Deploy `.dmg` via MDM (Jamf, Kandji) or manual installation. Code signing required for Gatekeeper.

### Linux

- **AppImage**: No installation required, chmod +x and run
- **.deb**: `sudo dpkg -i thorpe_1.0.0_amd64.deb`

## License Management

### Activating Licenses

Distribute license keys to users. Keys follow the format:

- Professional: `PRO-XXXX-XXXX-XXXX-CCCC`
- Enterprise: `ENT-XXXX-XXXX-XXXX-CCCC`

Users activate in **Licensing & Subscription**.

### Feature Gating

| Feature Key | Tier Required |
|-------------|--------------|
| `jonathan_ai` | Free |
| `basic_scans` | Free |
| `limited_reports` | Free |
| `full_diagnostics` | Professional |
| `repair_center` | Professional |
| `pdf_export` | Professional |
| `technician_workspace` | Enterprise |
| `multi_device` | Enterprise |

## Data Management

- All data stored locally per device
- Data directory: OS app data folder (`app.thorpe.desktop`)
- Users can delete all data via Settings
- No central data collection

## AI Configuration

For organizations using cloud AI:

1. Provide OpenAI API key or compatible endpoint
2. Users configure in Settings > Jonathan AI
3. Keys stored locally, never on Thorpe servers

## Security Considerations

- No remote access or monitoring capabilities
- Repair actions require user confirmation
- Review SECURITY.md for full security architecture
- Keep Thorpe updated via Update Manager

## Technician Workspace

Enterprise feature for IT teams:

- Create and manage support cases
- Maintain client records
- Add technician notes to cases and reports
- Search report history

## Updates

Configure update endpoint in `.env`:

```
VITE_UPDATE_ENDPOINT=https://updates.yourcompany.com/v1/check
```

Users check for updates in **Update Manager**.
