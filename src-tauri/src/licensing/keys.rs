use hmac::{Hmac, Mac};
use sha2::Sha256;
use std::sync::OnceLock;

type HmacSha256 = Hmac<Sha256>;

const DEFAULT_LICENSE_SECRET: &[u8] = b"thorpe-license-signing-key-v1";

/// Demo Professional license for evaluation builds.
pub const DEMO_PRO_LICENSE: &str = "PRO-DEMO-1234-KEYS-B65C";

/// Demo Enterprise license for evaluation builds.
pub const DEMO_ENT_LICENSE: &str = "ENT-DEMO-5678-KEYS-F20C";

fn signing_secret() -> Result<Vec<u8>, String> {
    static SECRET: OnceLock<Result<Vec<u8>, String>> = OnceLock::new();
    SECRET
        .get_or_init(|| {
            if let Ok(secret) = std::env::var("THORPE_LICENSE_SIGNING_SECRET") {
                let secret = secret.trim();
                if !secret.is_empty() {
                    return Ok(secret.as_bytes().to_vec());
                }
            }
            if cfg!(debug_assertions) {
                Ok(DEFAULT_LICENSE_SECRET.to_vec())
            } else {
                Err(
                    "THORPE_LICENSE_SIGNING_SECRET must be set for release builds. \
                     Configure the secret in your environment or CI before distributing installers."
                        .to_string(),
                )
            }
        })
        .clone()
}

pub fn license_checksum(body: &str) -> Result<String, String> {
    let secret = signing_secret()?;
    let mut mac = HmacSha256::new_from_slice(&secret).map_err(|e| e.to_string())?;
    mac.update(body.as_bytes());
    let digest = mac.finalize().into_bytes();
    Ok(hex::encode(&digest[..2]).to_uppercase())
}

pub fn generate_license_key(tier_prefix: &str, g1: &str, g2: &str, g3: &str) -> Result<String, String> {
    let prefix = tier_prefix.trim().to_uppercase();
    if prefix != "PRO" && prefix != "ENT" {
        return Err("Tier prefix must be PRO or ENT.".to_string());
    }
    let body = format!(
        "{prefix}-{}-{}-{}",
        g1.trim().to_uppercase(),
        g2.trim().to_uppercase(),
        g3.trim().to_uppercase()
    );
    Ok(format!("{}-{}", body, license_checksum(&body)?))
}

pub fn validate_license_key(key: &str) -> Result<(&'static str, String), String> {
    let normalized = key.trim().to_uppercase();
    let parts: Vec<&str> = normalized.split('-').collect();

    if parts.len() != 5 {
        return Err(
            "Invalid license key format. Expected TIER-XXXX-XXXX-XXXX-CCCC (e.g. PRO-DEMO-1234-KEYS-8F2A)."
                .to_string(),
        );
    }

    let tier = match parts[0] {
        "PRO" => "professional",
        "ENT" => "enterprise",
        _ => {
            return Err(
                "Invalid license tier prefix. Keys must start with PRO- or ENT-.".to_string(),
            );
        }
    };

    let body = format!("{}-{}-{}-{}", parts[0], parts[1], parts[2], parts[3]);
    let expected = license_checksum(&body)?;
    if parts[4] != expected {
        return Err("Invalid license key. The checksum does not match.".to_string());
    }

    if !cfg!(debug_assertions) && is_demo_key(&normalized) {
        return Err(
            "Demo license keys are not valid in production builds. Contact sales for a license key."
                .to_string(),
        );
    }

    Ok((tier, normalized))
}

pub fn is_demo_key(key: &str) -> bool {
    let normalized = key.trim().to_uppercase();
    normalized == DEMO_PRO_LICENSE || normalized == DEMO_ENT_LICENSE
}

#[cfg(test)]
pub fn signed_key(tier_prefix: &str, g1: &str, g2: &str, g3: &str) -> String {
    generate_license_key(tier_prefix, g1, g2, g3).expect("test key generation")
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn demo_keys_are_valid() {
        assert!(validate_license_key(DEMO_PRO_LICENSE).is_ok());
        assert!(validate_license_key(DEMO_ENT_LICENSE).is_ok());
        assert_eq!(validate_license_key(DEMO_PRO_LICENSE).unwrap().0, "professional");
        assert_eq!(validate_license_key(DEMO_ENT_LICENSE).unwrap().0, "enterprise");
    }

    #[test]
    fn rejects_invalid_checksum() {
        assert!(validate_license_key("PRO-DEMO-1234-KEYS-0000").is_err());
    }

    #[test]
    fn rejects_prefix_only_keys() {
        assert!(validate_license_key("PRO-TEST-KEY").is_err());
    }

    #[test]
    fn signed_helper_produces_valid_keys() {
        let key = signed_key("PRO", "TEST", "0001", "DEMO");
        assert!(validate_license_key(&key).is_ok());
    }

    #[test]
    fn generate_matches_validate_roundtrip() {
        let key = generate_license_key("ENT", "ACME", "2026", "UNIT").unwrap();
        assert_eq!(validate_license_key(&key).unwrap().0, "enterprise");
    }
}
