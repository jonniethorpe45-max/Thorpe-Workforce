# macOS Launch Assistant + DMG Builder

This folder provides a one-click macOS helper for final Thorpe Workforce setup and launch checks.

## Files

- `ThorpeWorkforceLaunchAssistant.command`
  - Interactive menu-driven assistant
  - Preflight checks
  - Env template generation
  - Local startup trigger
  - Deployed smoke checks
  - Opens Railway/Vercel/Stripe dashboards

- `build_launch_assistant_dmg.sh`
  - macOS-only script that packages the assistant into a `.dmg`

## Build the DMG on macOS

From repo root:

```bash
chmod +x scripts/macos/build_launch_assistant_dmg.sh scripts/macos/ThorpeWorkforceLaunchAssistant.command
./scripts/macos/build_launch_assistant_dmg.sh
```

Output:

```text
./ThorpeWorkforceLaunchAssistant.dmg
```

## Run the assistant

1. Open `ThorpeWorkforceLaunchAssistant.dmg`
2. Double-click `ThorpeWorkforceLaunchAssistant.command`
3. Follow menu options to complete remaining launch steps.
