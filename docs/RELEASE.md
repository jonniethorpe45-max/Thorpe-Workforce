# Releasing Thorpe

This guide explains how to build Windows, macOS, and Linux installers via GitHub Actions.

## Option 1: Tag a release (recommended)

1. Merge the Thorpe desktop branch into `main`.
2. Create and push a version tag:

```bash
git tag v1.0.0
git push origin v1.0.0
```

3. GitHub Actions runs **Thorpe Release** automatically.
4. When all three platform jobs finish, installers appear on:
   **GitHub → Releases → v1.0.0**

### Artifacts per platform

| Job | Output |
|-----|--------|
| `windows-x64` | NSIS `.exe` + `.msi` |
| `macos-arm64` | `.dmg` (Apple Silicon) |
| `linux-x64` | `.AppImage` + `.deb` |

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

## Option 3: Manual workflow + draft release

1. **Actions → Thorpe Release → Run workflow**
2. Check **Create a GitHub Release and attach installers**
3. Set **Tag name** (e.g. `v1.0.0`) — the tag must not exist yet, or the release step may fail
4. Run workflow
5. Review the **draft release** on GitHub and publish when ready

## Option 4: Build on your own machine

| Platform | Command |
|----------|---------|
| Windows | `scripts\build-windows.bat` |
| macOS / Linux | `bash scripts/build.sh` |

See [BUILD.md](../BUILD.md).

## macOS Intel builds

CI builds **Apple Silicon (arm64)** on `macos-latest`. Intel Mac users can often run the arm64 build via Rosetta, or you can add a `macos-13` / `x86_64-apple-darwin` matrix entry later.

## Code signing (optional)

Unsigned builds work for testing. For public distribution:

- **Windows**: Authenticode certificate
- **macOS**: Apple Developer ID + notarization (`APPLE_CERTIFICATE`, `APPLE_SIGNING_IDENTITY`, etc.)
- **Linux**: Usually not required

Configure signing secrets in GitHub **Settings → Secrets and variables → Actions**, then extend the workflow env vars per [Tauri’s signing docs](https://v2.tauri.app/distribute/sign/).

## Troubleshooting CI builds

- **Linux job fails on webkit**: Ensure `ubuntu-22.04` and apt packages in the workflow match [Tauri prerequisites](https://v2.tauri.app/start/prerequisites/).
- **Windows job fails on linker**: The `windows-latest` runner includes MSVC; ensure `package-lock.json` is committed.
- **Release empty**: All three matrix jobs must succeed; check failed jobs in Actions.
- **Duplicate release assets**: Each platform job uploads its bundles; partial failures may produce incomplete releases.
