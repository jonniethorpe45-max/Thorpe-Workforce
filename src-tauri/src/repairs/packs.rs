use crate::db::{Database, RepairPackRecord};
use base64::{engine::general_purpose::STANDARD as BASE64, Engine};
use chrono::Utc;
use hmac::{Hmac, Mac};
use serde::{Deserialize, Serialize};
use sha2::Sha256;

type HmacSha256 = Hmac<Sha256>;

/// Embedded verification key for official Thorpe OTA repair packs.
const THORPE_PACK_SIGNING_SECRET: &[u8] = b"thorpe-official-repair-pack-signing-v1";

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RepairPackManifest {
    pub pack_id: String,
    pub name: String,
    pub version: String,
    pub description: String,
    pub tools: Vec<RepairPackTool>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub signature: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RepairPackTool {
    pub id: String,
    pub name: String,
    pub description: String,
    pub action_kind: String,
    pub risk_level: String,
    pub requires_confirmation: bool,
    pub platform: Vec<String>,
    pub maps_to_action: Option<String>,
}

pub fn builtin_packs() -> Vec<RepairPackManifest> {
    vec![
        RepairPackManifest {
            pack_id: "thorpe-core".into(),
            name: "Thorpe Core".into(),
            version: "1.0.0".into(),
            description: "Built-in safe diagnostics and maintenance tools.".into(),
            tools: vec![],
            signature: None,
        },
        RepairPackManifest {
            pack_id: "thorpe-network".into(),
            name: "Thorpe Network".into(),
            version: "1.1.0".into(),
            description: "Network diagnostics and DNS repair pack.".into(),
            tools: vec![
                RepairPackTool {
                    id: "dns-flush".into(),
                    name: "Flush DNS Cache".into(),
                    description: "Clear DNS resolver cache.".into(),
                    action_kind: "mutating".into(),
                    risk_level: "low".into(),
                    requires_confirmation: true,
                    platform: vec!["windows".into(), "macos".into(), "linux".into()],
                    maps_to_action: Some("dns-flush".into()),
                },
                RepairPackTool {
                    id: "network-diagnostics".into(),
                    name: "Network Diagnostics".into(),
                    description: "Ping and connectivity tests.".into(),
                    action_kind: "diagnostic".into(),
                    risk_level: "low".into(),
                    requires_confirmation: false,
                    platform: vec!["windows".into(), "macos".into(), "linux".into()],
                    maps_to_action: Some("network-diagnostics".into()),
                },
            ],
            signature: None,
        },
        RepairPackManifest {
            pack_id: "thorpe-performance".into(),
            name: "Thorpe Performance".into(),
            version: "1.1.0".into(),
            description: "Performance analysis and cleanup.".into(),
            tools: vec![
                RepairPackTool {
                    id: "temp-cleanup".into(),
                    name: "Temp Cleanup".into(),
                    description: "Remove stale temporary files.".into(),
                    action_kind: "mutating".into(),
                    risk_level: "low".into(),
                    requires_confirmation: true,
                    platform: vec!["windows".into(), "macos".into(), "linux".into()],
                    maps_to_action: Some("temp-cleanup".into()),
                },
                RepairPackTool {
                    id: "high-resource-id".into(),
                    name: "High Resource ID".into(),
                    description: "Identify heavy processes.".into(),
                    action_kind: "diagnostic".into(),
                    risk_level: "low".into(),
                    requires_confirmation: false,
                    platform: vec!["windows".into(), "macos".into(), "linux".into()],
                    maps_to_action: Some("high-resource-id".into()),
                },
            ],
            signature: None,
        },
    ]
}

pub fn ensure_packs_installed(db: &Database) -> Result<(), String> {
    for manifest in builtin_packs() {
        let existing = db.list_repair_packs().map_err(|e| e.to_string())?;
        if existing.iter().any(|p| p.id == manifest.pack_id) {
            continue;
        }
        let now = Utc::now().to_rfc3339();
        db.upsert_repair_pack(&RepairPackRecord {
            id: manifest.pack_id.clone(),
            name: manifest.name.clone(),
            version: manifest.version.clone(),
            description: manifest.description.clone(),
            enabled: true,
            builtin: true,
            manifest_json: serde_json::to_string(&manifest).map_err(|e| e.to_string())?,
            installed_at: now,
        })
        .map_err(|e| e.to_string())?;
    }
    Ok(())
}

pub fn install_pack_from_json(db: &Database, json: &str) -> Result<RepairPackRecord, String> {
    let manifest: RepairPackManifest = serde_json::from_str(json).map_err(|e| e.to_string())?;
    if manifest.pack_id.trim().is_empty() || manifest.name.trim().is_empty() {
        return Err("Pack id and name are required.".into());
    }
    if builtin_packs().iter().any(|p| p.pack_id == manifest.pack_id) {
        return Err("Cannot install over a built-in repair pack.".into());
    }
    for tool in &manifest.tools {
        if let Some(ref action) = tool.maps_to_action {
            if !is_known_repair_action(action) {
                return Err(format!(
                    "Repair pack references unknown action '{action}'. Only whitelisted Thorpe repairs are allowed."
                ));
            }
        }
    }
    verify_pack_signature_if_present(&manifest)?;
    let now = Utc::now().to_rfc3339();
    let record = RepairPackRecord {
        id: manifest.pack_id.clone(),
        name: manifest.name.clone(),
        version: manifest.version.clone(),
        description: manifest.description.clone(),
        enabled: true,
        builtin: false,
        manifest_json: json.to_string(),
        installed_at: now,
    };
    db.upsert_repair_pack(&record).map_err(|e| e.to_string())?;
    Ok(record)
}

pub fn allowed_tool_ids(db: &Database) -> Result<Vec<String>, String> {
    ensure_packs_installed(db)?;
    let packs = db.list_repair_packs().map_err(|e| e.to_string())?;
    let mut ids = Vec::new();
    for pack in packs.into_iter().filter(|p| p.enabled) {
        if let Ok(manifest) = serde_json::from_str::<RepairPackManifest>(&pack.manifest_json) {
            for tool in manifest.tools {
                if let Some(action) = tool.maps_to_action {
                    if !ids.contains(&action) {
                        ids.push(action);
                    }
                }
            }
        }
    }
    if ids.is_empty() {
        ids = vec![
            "dns-flush".into(),
            "network-diagnostics".into(),
            "disk-analysis".into(),
            "high-resource-id".into(),
            "temp-cleanup".into(),
            "startup-review".into(),
            "update-check".into(),
            "restart-recommend".into(),
        ];
    }
    Ok(ids)
}

fn is_known_repair_action(action_id: &str) -> bool {
    const KNOWN: &[&str] = &[
        "temp-cleanup",
        "dns-flush",
        "disk-analysis",
        "startup-review",
        "high-resource-id",
        "network-diagnostics",
        "update-check",
        "restart-recommend",
        "print-spooler-restart",
        "software-inventory",
    ];
    KNOWN.contains(&action_id)
}

fn verify_pack_signature_if_present(manifest: &RepairPackManifest) -> Result<(), String> {
    let Some(signature) = manifest.signature.as_ref() else {
        return Ok(());
    };
    let mut unsigned = manifest.clone();
    unsigned.signature = None;
    let payload = serde_json::to_string(&unsigned).map_err(|e| e.to_string())?;
    let mut mac = HmacSha256::new_from_slice(THORPE_PACK_SIGNING_SECRET).map_err(|e| e.to_string())?;
    mac.update(payload.as_bytes());
    let expected = BASE64.encode(mac.finalize().into_bytes());
    if signature.trim() != expected {
        return Err("Invalid repair pack signature.".into());
    }
    Ok(())
}

#[cfg(test)]
mod signing_tests {
    use super::*;

    #[test]
    fn rejects_tampered_signed_pack() {
        let mut manifest = RepairPackManifest {
            pack_id: "custom-pack".into(),
            name: "Custom".into(),
            version: "1.0.0".into(),
            description: "Test".into(),
            tools: vec![],
            signature: Some("invalid".into()),
        };
        assert!(verify_pack_signature_if_present(&manifest).is_err());
        manifest.signature = None;
        assert!(verify_pack_signature_if_present(&manifest).is_ok());
    }
}
