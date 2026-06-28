# Administrator Guide

## Deployment

### Windows

Deploy via NSIS `.exe` installer or MSI package. Use Group Policy or MDM for enterprise rollout.

```powershell
# Silent install (NSIS) — replace version with your release tag
Thorpe_1.1.0_x64-setup.exe /S
```

### macOS

Deploy `.dmg` via MDM (Jamf, Kandji) or manual installation. Code signing required for Gatekeeper.

### Linux

- **AppImage**: No installation required, chmod +x and run
- **.deb**: `sudo dpkg -i Thorpe_1.1.0_amd64.deb`

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

Thorpe checks **GitHub Releases** for new versions (Update Manager). Optional custom endpoint via `THORPE_UPDATE_API_URL` at build/runtime.

After publishing a release, verify artifacts:

```bash
bash scripts/verify-release.sh v1.1.0
```

Users check for updates in **Update Manager**.

## License server deployment

Deploy `tools/license-server/` for online activation and Stripe billing. See:

- [tools/license-server/README.md](../tools/license-server/README.md)
- [PILOT_ONBOARDING.md](./PILOT_ONBOARDING.md)

Set on distributed builds:

- `THORPE_LICENSE_API_URL=https://<host>/activate`
- `THORPE_BILLING_API_URL=https://<host>`
