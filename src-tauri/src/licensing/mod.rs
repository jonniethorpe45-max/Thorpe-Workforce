mod keys;

pub use keys::{DEMO_ENT_LICENSE, DEMO_PRO_LICENSE};

use crate::db::Database;
use crate::AppState;
use serde::{Deserialize, Serialize};
use tauri::State;

pub const FREE_REPORT_LIMIT: i64 = 3;

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
            "enterprise_ai_console".into(),
            "intelligence_console".into(),
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
            "jonathan_auto_repair".into(),
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
        "jonathan_ai" | "jonathan_auto_repair" | "basic_scans" | "limited_reports" => "free",
        "full_diagnostics" | "repair_center" | "pdf_export" | "unlimited_reports" => "professional",
        "technician_workspace" | "multi_device" | "branding" | "advanced_reporting" | "team_management" | "enterprise_ai_console" | "intelligence_console" => "enterprise",
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

pub fn has_feature(db: &Database, feature: &str) -> Result<bool, String> {
    let record = db.get_license().map_err(|e| e.to_string())?;
    let user_features = tier_features(&record.tier);
    let required = feature_required_tier(feature);
    Ok(user_features.contains(&feature.to_string()) || tier_level(&record.tier) >= tier_level(required))
}

pub fn require_feature(db: &Database, feature: &str) -> Result<(), String> {
    if has_feature(db, feature)? {
        Ok(())
    } else {
        let required = feature_required_tier(feature);
        Err(format!(
            "This feature requires a {} license. Upgrade in Licensing settings.",
            tier_display(required)
        ))
    }
}

pub fn require_report_generation(db: &Database) -> Result<(), String> {
    if has_feature(db, "unlimited_reports")? {
        return Ok(());
    }
    let count = db.count_reports().map_err(|e| e.to_string())?;
    if count >= FREE_REPORT_LIMIT {
        return Err(format!(
            "Free tier is limited to {} diagnostic reports. Upgrade to Professional for unlimited reports.",
            FREE_REPORT_LIMIT
        ));
    }
    Ok(())
}

#[tauri::command]
pub fn get_license_info(state: State<AppState>) -> Result<LicenseInfo, String> {
    let record = state.lock_db()?.get_license().map_err(|e| e.to_string())?;
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
    let (tier, normalized_key) = keys::validate_license_key(&request.license_key)?;

    let record = state
        .lock_db()?
        .activate_license(&normalized_key, tier, request.organization.as_deref())
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
    let record = state.lock_db()?.get_license().map_err(|e| e.to_string())?;
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
    use crate::db::Database;
    use std::path::Path;

    fn test_db() -> Database {
        Database::new(Path::new(":memory:")).expect("in-memory db")
    }

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

    #[test]
    fn free_tier_blocks_repair_center() {
        let db = test_db();
        assert!(!has_feature(&db, "repair_center").unwrap());
        assert!(require_feature(&db, "repair_center").is_err());
    }

    #[test]
    fn professional_license_unlocks_repairs() {
        let db = test_db();
        let key = keys::signed_key("PRO", "TEST", "0001", "DEMO");
        db.activate_license(&key, "professional", None)
            .expect("activate");
        assert!(has_feature(&db, "repair_center").unwrap());
        assert!(require_feature(&db, "repair_center").is_ok());
    }

    #[test]
    fn free_tier_enforces_report_limit() {
        let db = test_db();
        for i in 0..FREE_REPORT_LIMIT {
            db.save_report(&crate::db::DiagnosticReport {
                id: format!("report-{i}"),
                scan_id: None,
                title: format!("Report {i}"),
                summary: "summary".into(),
                findings: "[]".into(),
                recommendations: "[]".into(),
                health_score: 80,
                risk_level: "low".into(),
                technician_notes: None,
                plain_language: "plain".into(),
                created_at: chrono::Utc::now().to_rfc3339(),
            })
            .expect("save report");
        }
        assert!(require_report_generation(&db).is_err());
    }
}
