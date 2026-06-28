use super::packs::RepairPackManifest;
use base64::{engine::general_purpose::STANDARD as BASE64, Engine};
use ed25519_dalek::{Signature, Signer, SigningKey, Verifier, VerifyingKey};
use hmac::{Hmac, Mac};
use sha2::Sha256;

type HmacSha256 = Hmac<Sha256>;

/// Thorpe OTA repair pack Ed25519 public key (hex-encoded, 32 bytes).
/// Replace when rotating signing keys; pair with `thorpe-pack-sign` CLI.
pub const THORPE_PACK_PUBLIC_KEY_HEX: &str =
    "838618846ae377f4fbb0208f0a2a380220787dd7a74b102d6518dea5639810b3";

const LEGACY_HMAC_SECRET: &[u8] = b"thorpe-official-repair-pack-signing-v1";
pub const ED25519_SIGNATURE_PREFIX: &str = "ed25519:";

pub fn canonical_manifest_json(manifest: &RepairPackManifest) -> Result<String, String> {
    let mut unsigned = manifest.clone();
    unsigned.signature = None;
    serde_json::to_string(&unsigned).map_err(|e| e.to_string())
}

pub fn public_key_bytes() -> Result<[u8; 32], String> {
    let hex = THORPE_PACK_PUBLIC_KEY_HEX.trim();
    if hex == "PLACEHOLDER_WILL_BE_SET_AFTER_KEYGEN" || hex.len() != 64 {
        return Err("Thorpe pack public key is not configured.".into());
    }
    let bytes = hex::decode(hex).map_err(|e| format!("Invalid public key hex: {e}"))?;
    bytes
        .try_into()
        .map_err(|_| "Public key must be 32 bytes.".to_string())
}

pub fn verifying_key() -> Result<VerifyingKey, String> {
    VerifyingKey::from_bytes(&public_key_bytes()?).map_err(|e| e.to_string())
}

pub fn signing_key_from_seed_hex(hex: &str) -> Result<SigningKey, String> {
    let bytes = hex::decode(hex.trim()).map_err(|e| format!("Invalid key hex: {e}"))?;
    let seed: [u8; 32] = bytes
        .try_into()
        .map_err(|_| "Signing key seed must be exactly 32 bytes (64 hex chars).".to_string())?;
    Ok(SigningKey::from_bytes(&seed))
}

pub fn sign_manifest_ed25519(
    manifest: &RepairPackManifest,
    signing_key: &SigningKey,
) -> Result<String, String> {
    let payload = canonical_manifest_json(manifest)?;
    let signature = signing_key.sign(payload.as_bytes());
    Ok(format!("{ED25519_SIGNATURE_PREFIX}{}", BASE64.encode(signature.to_bytes())))
}

pub fn verify_ed25519_signature(manifest: &RepairPackManifest, signature: &str) -> Result<(), String> {
    let sig_b64 = signature
        .strip_prefix(ED25519_SIGNATURE_PREFIX)
        .ok_or_else(|| "Expected ed25519: signature prefix.".to_string())?;
    let sig_bytes = BASE64
        .decode(sig_b64.trim())
        .map_err(|e| format!("Invalid signature base64: {e}"))?;
    let sig_array: [u8; 64] = sig_bytes
        .try_into()
        .map_err(|_| "Ed25519 signature must be 64 bytes.".to_string())?;
    let signature = Signature::from_bytes(&sig_array);
    let payload = canonical_manifest_json(manifest)?;
    verifying_key()?
        .verify(payload.as_bytes(), &signature)
        .map_err(|_| "Invalid Ed25519 repair pack signature.".to_string())
}

fn verify_legacy_hmac_signature(manifest: &RepairPackManifest, signature: &str) -> Result<(), String> {
    let payload = canonical_manifest_json(manifest)?;
    let mut mac = HmacSha256::new_from_slice(LEGACY_HMAC_SECRET).map_err(|e| e.to_string())?;
    mac.update(payload.as_bytes());
    let expected = BASE64.encode(mac.finalize().into_bytes());
    if signature.trim() != expected {
        return Err("Invalid legacy HMAC repair pack signature.".into());
    }
    Ok(())
}

pub fn verify_pack_signature_if_present(manifest: &RepairPackManifest) -> Result<(), String> {
    let Some(signature) = manifest.signature.as_ref() else {
        return Ok(());
    };
    if signature.starts_with(ED25519_SIGNATURE_PREFIX) {
        verify_ed25519_signature(manifest, signature)
    } else {
        verify_legacy_hmac_signature(manifest, signature)
    }
}

pub fn generate_keypair_hex() -> (String, String) {
    let signing_key = SigningKey::generate(&mut rand::rngs::OsRng);
    let verifying_key = signing_key.verifying_key();
    (
        hex::encode(signing_key.to_bytes()),
        hex::encode(verifying_key.to_bytes()),
    )
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::repairs::packs::RepairPackTool;

    fn sample_manifest() -> RepairPackManifest {
        RepairPackManifest {
            pack_id: "test-pack".into(),
            name: "Test".into(),
            version: "1.0.0".into(),
            description: "Test pack".into(),
            tools: vec![RepairPackTool {
                id: "t1".into(),
                name: "Tool".into(),
                description: "d".into(),
                action_kind: "diagnostic".into(),
                risk_level: "low".into(),
                requires_confirmation: false,
                platform: vec!["linux".into()],
                maps_to_action: Some("dns-flush".into()),
            }],
            signature: None,
        }
    }

    #[test]
    fn ed25519_sign_and_verify_roundtrip() {
        let (seed_hex, pub_hex) = generate_keypair_hex();
        // Temporarily use generated pubkey for this test
        let signing_key = signing_key_from_seed_hex(&seed_hex).unwrap();
        let verifying_key =
            VerifyingKey::from_bytes(&hex::decode(&pub_hex).unwrap().try_into().unwrap()).unwrap();

        let mut manifest = sample_manifest();
        let sig = sign_manifest_ed25519(&manifest, &signing_key).unwrap();
        manifest.signature = Some(sig.clone());

        let payload = canonical_manifest_json(&manifest).unwrap();
        let sig_bytes = BASE64
            .decode(sig.strip_prefix(ED25519_SIGNATURE_PREFIX).unwrap())
            .unwrap();
        let sig_array: [u8; 64] = sig_bytes.try_into().unwrap();
        let signature = Signature::from_bytes(&sig_array);
        verifying_key
            .verify(payload.as_bytes(), &signature)
            .expect("signature should verify");
    }

    #[test]
    fn verifies_pack_with_embedded_public_key() {
        let private_path = std::path::Path::new(env!("CARGO_MANIFEST_DIR"))
            .join("../tools/pack-signing/thorpe-pack-private.hex");
        if !private_path.exists() {
            return;
        }
        let seed = std::fs::read_to_string(&private_path).expect("read private key");
        let signing_key = signing_key_from_seed_hex(seed.trim()).expect("parse key");
        let manifest = RepairPackManifest {
            pack_id: "embed-test".into(),
            name: "Embed Test".into(),
            version: "1.0.0".into(),
            description: "Uses committed public key".into(),
            tools: vec![],
            signature: None,
        };
        let mut signed = manifest.clone();
        signed.signature = Some(sign_manifest_ed25519(&manifest, &signing_key).unwrap());
        verify_pack_signature_if_present(&signed).expect("embedded pubkey should verify");
    }
}
