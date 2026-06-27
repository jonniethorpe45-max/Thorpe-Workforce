use hmac::{Hmac, Mac};
use sha2::Sha256;

type HmacSha256 = Hmac<Sha256>;

const LICENSE_SECRET: &[u8] = b"thorpe-license-signing-key-v1";

/// Demo Professional license for evaluation builds.
pub const DEMO_PRO_LICENSE: &str = "PRO-DEMO-1234-KEYS-B65C";

/// Demo Enterprise license for evaluation builds.
pub const DEMO_ENT_LICENSE: &str = "ENT-DEMO-5678-KEYS-F20C";

pub fn license_checksum(body: &str) -> String {
    let mut mac = HmacSha256::new_from_slice(LICENSE_SECRET).expect("HMAC key length");
    mac.update(body.as_bytes());
    let digest = mac.finalize().into_bytes();
    hex::encode(&digest[..2]).to_uppercase()
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
    let expected = license_checksum(&body);
    if parts[4] != expected {
        return Err("Invalid license key. The checksum does not match.".to_string());
    }

    Ok((tier, normalized))
}

#[cfg(test)]
pub fn signed_key(tier_prefix: &str, g1: &str, g2: &str, g3: &str) -> String {
    let body = format!("{tier_prefix}-{g1}-{g2}-{g3}");
    format!("{}-{}", body, license_checksum(&body))
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
}
