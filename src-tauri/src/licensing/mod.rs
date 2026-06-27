use crate::AppState;
use serde::{Deserialize, Serialize};
use tauri::State;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LicenseInfo {
    pub tier: String,
    pub tier_display: String,
    pub features: Vec<String>,
    pub license_key: Option<String>,
    pub activated_at: Option<String>,
    pub expires_at: Option<String>,
    pub organization: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FeatureCheck {
    pub feature: String,
    pub allowed: bool,
    pub required_tier: String,
}

fn tier_features(tier: &str) -> Vec<String> {
    match tier {
        "enterprise" => vec![
            "jonathan_ai".into(),
            "basic_scans".into(),
            "full_diagnostics".into(),
            "repair_center".into(),
            "pdf_export".into(),
            "unlimited_reports".into(),
            "technician_workspace".into(),
            "multi_device".into(),
            "branding".into(),
            "advanced_reporting".into(),
            "team_management".into(),
        ],
        "professional" => vec![
            "jonathan_ai".into(),
            "basic_scans".into(),
            "full_diagnostics".into(),
            "repair_center".into(),
            "pdf_export".into(),
            "unlimited_reports".into(),
        ],
        _ => vec![
            "jonathan_ai".into(),
            "basic_scans".into(),
            "limited_reports".into(),
        ],
    }
}

fn tier_display(tier: &str) -> &str {
    match tier {
        "enterprise" => "Enterprise",
        "professional" => "Professional",
        _ => "Free",
    }
}

fn feature_required_tier(feature: &str) -> &str {
    match feature {
        "jonathan_ai" | "basic_scans" | "limited_reports" => "free",
        "full_diagnostics" | "repair_center" | "pdf_export" | "unlimited_reports" => "professional",
        "technician_workspace" | "multi_device" | "branding" | "advanced_reporting" | "team_management" => "enterprise",
        _ => "enterprise",
    }
}

fn tier_level(tier: &str) -> u8 {
    match tier {
        "enterprise" => 3,
        "professional" => 2,
        _ => 1,
    }
}

#[tauri::command]
pub fn get_license_info(state: State<AppState>) -> Result<LicenseInfo, String> {
    let record = state.db.lock().unwrap().get_license().map_err(|e| e.to_string())?;
    Ok(LicenseInfo {
        tier: record.tier.clone(),
        tier_display: tier_display(&record.tier).to_string(),
        features: tier_features(&record.tier),
        license_key: record.license_key,
        activated_at: record.activated_at,
        expires_at: record.expires_at,
        organization: record.organization,
    })
}

#[derive(Debug, Deserialize)]
pub struct ActivateLicenseRequest {
    pub license_key: String,
    pub organization: Option<String>,
}

#[tauri::command]
pub fn activate_license(state: State<AppState>, request: ActivateLicenseRequest) -> Result<LicenseInfo, String> {
    let tier = if request.license_key.starts_with("ENT-") {
        "enterprise"
    } else if request.license_key.starts_with("PRO-") {
        "professional"
    } else if request.license_key.starts_with("THORPE-") {
        "professional"
    } else {
        return Err("Invalid license key format. Keys should start with PRO-, ENT-, or THORPE-.".to_string());
    };

    let record = state
        .db
        .lock()
        .unwrap()
        .activate_license(&request.license_key, tier, request.organization.as_deref())
        .map_err(|e| e.to_string())?;

    Ok(LicenseInfo {
        tier: record.tier.clone(),
        tier_display: tier_display(&record.tier).to_string(),
        features: tier_features(&record.tier),
        license_key: record.license_key,
        activated_at: record.activated_at,
        expires_at: record.expires_at,
        organization: record.organization,
    })
}

#[tauri::command]
pub fn check_feature(state: State<AppState>, feature: String) -> Result<FeatureCheck, String> {
    let record = state.db.lock().unwrap().get_license().map_err(|e| e.to_string())?;
    let user_features = tier_features(&record.tier);
    let required = feature_required_tier(&feature);
    let allowed = user_features.contains(&feature)
        || tier_level(&record.tier) >= tier_level(required);

    Ok(FeatureCheck {
        feature: feature.clone(),
        allowed,
        required_tier: required.to_string(),
    })
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn free_tier_has_basic_features() {
        let features = tier_features("free");
        assert!(features.contains(&"jonathan_ai".to_string()));
        assert!(!features.contains(&"repair_center".to_string()));
    }

    #[test]
    fn professional_tier_has_repairs() {
        let features = tier_features("professional");
        assert!(features.contains(&"repair_center".to_string()));
    }

    #[test]
    fn feature_gating_works() {
        assert_eq!(feature_required_tier("repair_center"), "professional");
        assert_eq!(feature_required_tier("technician_workspace"), "enterprise");
    }

    #[test]
    fn tier_levels_order_correctly() {
        assert!(tier_level("enterprise") > tier_level("professional"));
        assert!(tier_level("professional") > tier_level("free"));
    }
}
