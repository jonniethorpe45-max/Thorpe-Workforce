# Thorpe Repair Pack Signing

Official OTA repair packs are signed with **Ed25519**. Thorpe Desktop embeds only the **public key** and verifies signatures on install.

## Generate a keypair (once per environment)

```bash
cd src-tauri
cargo run --bin thorpe-pack-sign -- --gen-keypair --out-dir ../tools/pack-signing
```

Copy the printed public key hex into `src-tauri/src/repairs/pack_signing.rs` (`THORPE_PACK_PUBLIC_KEY_HEX`).

**Never commit** `thorpe-pack-private.hex`.

## Sign a manifest

```bash
cargo run --bin thorpe-pack-sign -- \
  --manifest my-pack.json \
  --key ../tools/pack-signing/thorpe-pack-private.hex \
  --output signed-pack.json
```

Or set `THORPE_PACK_SIGNING_KEY` to the 64-char hex seed.

## Manifest format

```json
{
  "pack_id": "acme-network-tools",
  "name": "ACME Network Tools",
  "version": "1.0.0",
  "description": "Approved network diagnostics",
  "tools": [
    {
      "id": "dns-flush-tool",
      "name": "Flush DNS",
      "description": "Maps to Thorpe dns-flush",
      "action_kind": "mutating",
      "risk_level": "low",
      "requires_confirmation": true,
      "platform": ["windows", "macos", "linux"],
      "maps_to_action": "dns-flush"
    }
  ],
  "signature": "ed25519:<base64>"
}
```

- `maps_to_action` must reference a **whitelisted** Thorpe repair action ID.
- Unsigned packs may still install for org testing; signed packs are verified against the embedded public key.
- Legacy HMAC signatures (no `ed25519:` prefix) remain supported for backward compatibility.

## Install in Thorpe

Intelligence Console → Repair Packs → paste signed JSON or load file.
