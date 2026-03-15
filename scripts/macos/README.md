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

- `launch-assistant.profile.example`
  - Copy to `launch-assistant.profile` and set your exact domains/dashboards
  - Auto-loaded by the assistant at startup
  - You can also use menu option **Save current config to profile file**

- `build_launch_assistant_dmg.sh`
  - macOS-only script that packages the assistant into a `.dmg`

## Build the DMG on macOS

From repo root:

```bash
chmod +x scripts/macos/build_launch_assistant_dmg.sh scripts/macos/ThorpeWorkforceLaunchAssistant.command
cp scripts/macos/launch-assistant.profile.example scripts/macos/launch-assistant.profile
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

## Recommended profile values for your setup

If you are using the domains discussed in setup:

```bash
THORPE_FRONTEND_URL=https://thorpeworkforce.ai
THORPE_API_URL=https://api.thorpeworkforce.ai
```

You can also set staging URLs for one-click staging smoke tests.
