# Thorpe Desktop GA Checklist

Use this checklist before tagging a commercial release (e.g. `v1.1.0`).

## Version alignment

- [ ] Run `bash scripts/check-versions.sh` — all sources report the same version
- [ ] Update `CHANGELOG.md` with release notes
- [ ] Confirm download URLs in `src/config/downloads.ts` match artifact names from Tauri bundle

## Security & licensing

- [ ] Set `THORPE_LICENSE_SIGNING_SECRET` in CI/release environment (never commit)
- [ ] Deploy `tools/license-server/` (Docker or host) behind HTTPS
- [ ] Set `THORPE_BILLING_API_URL` and `THORPE_LICENSE_API_URL` on distributed builds
- [ ] Configure Stripe prices + webhook → `/webhooks/stripe`
- [ ] Generate production keys with `npm run license-key -- --tier PRO --group1 ...`
- [ ] Verify demo keys are rejected in release builds (`cargo build --release`)

## Code signing

- [ ] Windows: `TAURI_SIGNING_PRIVATE_KEY` + password in GitHub secrets
- [ ] macOS: Apple Developer ID certificate + notarization secrets
- [ ] Test signed installer on a clean VM before publishing

## Quality gates

- [ ] `npm run lint`
- [ ] `npm run test:e2e` (38 tests — all pages, API commands, user flows)
- [ ] `npm run test:all` or `bash scripts/e2e.sh` for full stack verification
- [ ] `cd src-tauri && cargo test`
- [ ] `cd src-tauri && cargo build --release`
- [ ] `cd tools/license-server && python3 test_server.py`
- [ ] `bash scripts/verify-release.sh v<version>` (after release is published)
- [ ] `npm audit --audit-level=high` and `cargo audit` (CI runs these; review advisories)
- [ ] Manual smoke: Jonathan chat, system scan, repair approval, Intelligence Console (Enterprise)

## Release

1. Merge production-ready PR to `main`
2. Tag: `git tag v1.1.0 && git push origin v1.1.0`
3. Verify **Thorpe Release** workflow completes for all three platforms
4. Run `bash scripts/verify-release.sh v1.1.0`
5. Publish GitHub Release (remove draft if applicable)
6. Smoke-test installers from the release page
7. Share [PILOT_ONBOARDING.md](./PILOT_ONBOARDING.md) with pilot customers

## Post-release

- [ ] Confirm Update Manager detects the new release on an older installed version
- [ ] Monitor license activation logs (if using online server)
- [ ] Document known limitations for pilot customers

## Known pilot limitations

| Item | Status |
|------|--------|
| Multi-device management | Not shipped — removed from tier marketing |
| Custom branding | Not shipped |
| Team management | Not shipped |
| Stripe billing UI | Subscribe flow + checkout polling (requires license server + Stripe) |
| Tauri WebDriver E2E | 38 browser E2E tests (pages, flows, API); native WebDriver optional |
