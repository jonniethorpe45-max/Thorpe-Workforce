# Releasing Thorpe

This guide explains how to build Windows, macOS, and Linux installers via GitHub Actions.

## Option 1: Tag a release (recommended)

1. Merge production-ready changes into `main`.
2. Run version alignment: `bash scripts/check-versions.sh`
3. Create and push a version tag:

```bash
git tag v1.1.0
git push origin v1.1.0
```

4. GitHub Actions runs **Thorpe Release** automatically.
5. When all three platform jobs finish, installers appear on:
   **GitHub → Releases → v1.1.0**
6. Verify artifacts: `bash scripts/verify-release.sh v1.1.0`

### Artifacts per platform

| Job | Output (v1.1.0 example) |
|-----|-------------------------|
| `windows-x64` | `Thorpe_1.1.0_x64-setup.exe`, `Thorpe_1.1.0_x64_en-US.msi` |
| `macos-arm64` | `Thorpe_1.1.0_aarch64.dmg` |
| `linux-x64` | `Thorpe_1.1.0_amd64.AppImage`, `Thorpe_1.1.0_amd64.deb` |

Artifact names follow `Thorpe_<version>_<target>` from `src-tauri/tauri.conf.json` `version`.

## Option 2: Manual workflow (no tag)

1. Open **GitHub → Actions → Thorpe Release → Run workflow**.
2. Choose branch (e.g. `main`).
3. Leave **Create a GitHub Release** unchecked.
4. Run workflow.
5. Download installers from each job’s **Artifacts** section:
   - `thorpe-windows-x64`
   - `thorpe-macos-arm64`
   - `thorpe-linux-x64`

Artifacts are kept for 30 days.

> **Note:** Cross-compiled bundles are written under `src-tauri/target/<triple>/release/bundle/`. The release workflow paths must match the Rust target triple for each platform.

## Option 3: Manual workflow + draft release

1. **Actions → Thorpe Release → Run workflow**
2. Check **Create a GitHub Release and attach installers**
3. Set **Tag name** (e.g. `v1.1.0`) — the tag must not exist yet, or the release step may fail
4. Run workflow
5. Review the **draft release** on GitHub and publish when ready
6. Run `bash scripts/verify-release.sh v1.1.0` before publishing

## Option 4: Build on your own machine

| Platform | Command |
|----------|---------|
| Windows | `scripts\build-windows.bat` |
| macOS / Linux | `bash scripts/build.sh` |

See [BUILD.md](../BUILD.md).

## macOS Intel builds

CI builds **Apple Silicon (arm64)** on `macos-latest`. Intel Mac users can often run the arm64 build via Rosetta, or you can add a `macos-13` / `x86_64-apple-darwin` matrix entry later.

## Code signing (optional)

Unsigned builds work for testing. For public distribution, configure secrets in **GitHub → Settings → Secrets and variables → Actions**:

| Secret | Platform | Purpose |
|--------|----------|---------|
| `TAURI_SIGNING_PRIVATE_KEY` | Windows | Authenticode signing key (`.pfx` base64 or Tauri key format) |
| `TAURI_SIGNING_PRIVATE_KEY_PASSWORD` | Windows | Key password |
| `APPLE_CERTIFICATE` | macOS | Developer ID certificate (base64 `.p12`) |
| `APPLE_CERTIFICATE_PASSWORD` | macOS | Certificate password |
| `APPLE_SIGNING_IDENTITY` | macOS | e.g. `Developer ID Application: Your Org (TEAMID)` |
| `APPLE_ID` | macOS | Apple ID for notarization |
| `APPLE_PASSWORD` | macOS | App-specific password |
| `APPLE_TEAM_ID` | macOS | Apple Developer Team ID |

The **Thorpe Release** workflow passes these to `tauri build` when present. If secrets are unset, builds complete unsigned (suitable for internal testing).

See [Tauri signing docs](https://v2.tauri.app/distribute/sign/) for key generation and notarization setup.

### Tauri auto-updater (after signing)

The desktop app checks GitHub Releases via **Update Manager** today. For in-app delta updates:

1. Generate updater signing keys: `npm run tauri signer generate -- -w ~/.tauri/thorpe.key`
2. Add `TAURI_SIGNING_PRIVATE_KEY` to CI (same key used for bundles)
3. Install `tauri-plugin-updater` and enable in `tauri.conf.json`
4. Publish `latest.json` alongside release assets

Until signing keys are configured, users install updates by downloading installers from Update Manager.

### License server (production)

For commercial deployments, set `THORPE_LICENSE_API_URL` to your HTTPS license activation endpoint at build or runtime. When set, activation requires the server; offline HMAC validation is used only when the variable is unset (development and air-gapped pilots).

See [tools/license-server/README.md](../tools/license-server/README.md) for deploying the reference activation server (Docker, Fly.io, or Railway).

For release builds, set `THORPE_LICENSE_SIGNING_SECRET` in CI and generate keys with `npm run license-key`.

## Troubleshooting CI builds

- **Linux job fails on webkit**: Ensure `ubuntu-22.04` and apt packages in the workflow match [Tauri prerequisites](https://v2.tauri.app/start/prerequisites/).
- **Windows job fails on linker**: The `windows-latest` runner includes MSVC; ensure `package-lock.json` is committed.
- **Release empty**: All three matrix jobs must succeed; check failed jobs in Actions.
- **Duplicate release assets**: Each platform job uploads its bundles; partial failures may produce incomplete releases.
- **verify-release.sh fails**: Confirm the release is published (not draft) and all five bundle filenames match `Thorpe_<version>_*`.
