use crate::agent::plan_with_rules;
use crate::db::WatchdogEvent;
use crate::scanner::{self, ScanIssue, SystemScanResult};
use crate::AppState;
use chrono::Utc;
use serde::{Deserialize, Serialize};
use std::sync::atomic::{AtomicBool, Ordering};
use tauri::{AppHandle, Emitter, Manager};
use uuid::Uuid;

static WATCHDOG_RUNNING: AtomicBool = AtomicBool::new(false);

#[derive(Debug, Clone)]
struct MetricAlert {
    event_type: String,
    message: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct WatchdogAlertPayload {
    pub id: String,
    pub event_type: String,
    pub health_score: i32,
    pub message: String,
    pub plan_json: Option<String>,
    pub issues_json: Option<String>,
}

pub fn start_watchdog(app: AppHandle) {
    if WATCHDOG_RUNNING.swap(true, Ordering::SeqCst) {
        return;
    }

    tauri::async_runtime::spawn(async move {
        loop {
            let interval_mins = app
                .state::<AppState>()
                .lock_db()
                .ok()
                .and_then(|db| db.get_watchdog_config().ok())
                .map(|c| if c.enabled { c.interval_minutes.max(5) } else { 0 })
                .unwrap_or(0);

            if interval_mins == 0 {
                tokio::time::sleep(std::time::Duration::from_secs(60)).await;
                continue;
            }

            tokio::time::sleep(std::time::Duration::from_secs((interval_mins * 60) as u64)).await;

            if let Err(e) = run_watchdog_tick(&app).await {
                eprintln!("Watchdog tick error: {e}");
            }
        }
    });
}

fn detect_metric_alerts(scan: &SystemScanResult, health_threshold: i32) -> Vec<MetricAlert> {
    let mut alerts = Vec::new();

    if scan.health_score < health_threshold {
        alerts.push(MetricAlert {
            event_type: "health_threshold".into(),
            message: format!(
                "Overall system health is {}/100 (threshold {}).",
                scan.health_score, health_threshold
            ),
        });
    }

    if scan.cpu.usage_percent > 80.0 {
        alerts.push(MetricAlert {
            event_type: "high_cpu".into(),
            message: format!(
                "CPU usage is {:.1}% — a process may be spiking or overloading the system.",
                scan.cpu.usage_percent
            ),
        });
    }

    if scan.memory.usage_percent > 85.0 {
        alerts.push(MetricAlert {
            event_type: "high_memory".into(),
            message: format!(
                "Memory usage is {:.1}% — available RAM is {:.1} GB.",
                scan.memory.usage_percent, scan.memory.available_gb
            ),
        });
    }

    for disk in &scan.disks {
        if disk.usage_percent > 90.0 {
            alerts.push(MetricAlert {
                event_type: format!("low_disk:{}", disk.mount_point),
                message: format!(
                    "Disk {} is {:.1}% full with only {:.1} GB free.",
                    disk.mount_point, disk.usage_percent, disk.available_gb
                ),
            });
        }
    }

    for issue in &scan.issues {
        if issue.category == "process" && !alerts.iter().any(|a| a.event_type == "high_cpu") {
            alerts.push(MetricAlert {
                event_type: "high_cpu_process".into(),
                message: issue.title.clone(),
            });
        }
    }

    alerts
}

fn plan_for_alert(scan: &SystemScanResult, alert: &MetricAlert, auto_plan: bool) -> Option<String> {
    if !auto_plan {
        return None;
    }

    let message = match alert.event_type.as_str() {
        t if t.starts_with("low_disk") => {
            "Proactive watchdog: low disk space detected".to_string()
        }
        "high_cpu" | "high_cpu_process" => {
            "Proactive watchdog: high CPU usage detected".to_string()
        }
        "high_memory" => "Proactive watchdog: high memory usage detected".to_string(),
        _ => format!("Proactive watchdog: {}", alert.message),
    };

    let plan = plan_with_rules(&message, Some(scan));
    serde_json::to_string(&plan).ok()
}

async fn run_watchdog_tick(app: &AppHandle) -> Result<(), String> {
    let state = app.state::<AppState>();
    let config = {
        let db = state.lock_db()?;
        db.get_watchdog_config().map_err(|e| e.to_string())?
    };

    if !config.enabled {
        return Ok(());
    }

    let scan = scanner::quick_system_scan();
    let alerts = detect_metric_alerts(&scan, config.health_threshold);
    if alerts.is_empty() {
        return Ok(());
    }

    let issues_json = serde_json::to_string(&scan.issues).ok();
    let dedupe_mins = config.interval_minutes.max(5);

    for alert in alerts {
        {
            let db = state.lock_db()?;
            if db
                .has_recent_unacked_watchdog_event_of_type(&alert.event_type, dedupe_mins)
                .map_err(|e| e.to_string())?
            {
                continue;
            }
        }

        let plan_json = plan_for_alert(&scan, &alert, config.auto_plan);
        let event = WatchdogEvent {
            id: Uuid::new_v4().to_string(),
            event_type: alert.event_type.clone(),
            health_score: scan.health_score,
            message: if config.auto_plan && plan_json.is_some() {
                format!("{} Jonathan prepared a response plan.", alert.message)
            } else {
                alert.message.clone()
            },
            plan_json,
            issues_json: issues_json.clone(),
            acknowledged: false,
            created_at: Utc::now().to_rfc3339(),
        };

        {
            let db = state.lock_db()?;
            db.save_watchdog_event(&event).map_err(|e| e.to_string())?;
        }

        if config.auto_notify {
            let payload = WatchdogAlertPayload {
                id: event.id.clone(),
                event_type: event.event_type.clone(),
                health_score: event.health_score,
                message: event.message.clone(),
                plan_json: event.plan_json.clone(),
                issues_json: event.issues_json.clone(),
            };
            let _ = app.emit("watchdog-alert", &payload);
        }
    }

    Ok(())
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct WatchdogStatus {
    pub config: crate::db::WatchdogConfig,
    pub recent_events: Vec<WatchdogEvent>,
}

#[tauri::command]
pub fn get_watchdog_status(state: tauri::State<AppState>) -> Result<WatchdogStatus, String> {
    let db = state.lock_db()?;
    Ok(WatchdogStatus {
        config: db.get_watchdog_config().map_err(|e| e.to_string())?,
        recent_events: db.list_watchdog_events(20).map_err(|e| e.to_string())?,
    })
}

#[tauri::command]
pub fn update_watchdog_config(
    state: tauri::State<AppState>,
    enabled: bool,
    interval_minutes: i64,
    health_threshold: i32,
    auto_notify: bool,
    auto_plan: bool,
) -> Result<crate::db::WatchdogConfig, String> {
    let db = state.lock_db()?;
    db.update_watchdog_config(&crate::db::WatchdogConfig {
        enabled,
        interval_minutes,
        health_threshold,
        auto_notify,
        auto_plan,
        updated_at: Utc::now().to_rfc3339(),
    })
    .map_err(|e| e.to_string())
}

#[tauri::command]
pub fn acknowledge_watchdog_event(state: tauri::State<AppState>, event_id: String) -> Result<(), String> {
    let db = state.lock_db()?;
    db.conn()
        .execute(
            "UPDATE watchdog_events SET acknowledged = 1 WHERE id = ?1",
            rusqlite::params![event_id],
        )
        .map_err(|e| e.to_string())?;
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::scanner::{
        CpuInfo, DiskInfo, HardwareSummary, MemoryInfo, NetworkInfo, OsInfo, ProcessInfo,
        SystemScanResult,
    };

    fn sample_scan(health: i32, cpu: f32, mem: f64, disk_pct: f64) -> SystemScanResult {
        SystemScanResult {
            id: "scan-1".into(),
            timestamp: "2026-01-01".into(),
            health_score: health,
            os: OsInfo {
                name: "Linux".into(),
                version: "6.1".into(),
                hostname: "pc".into(),
                kernel_version: "".into(),
                arch: "x86_64".into(),
            },
            cpu: CpuInfo {
                brand: "Intel".into(),
                cores: 4,
                usage_percent: cpu,
            },
            memory: MemoryInfo {
                total_gb: 16.0,
                used_gb: 16.0 * mem / 100.0,
                available_gb: 16.0 * (100.0 - mem) / 100.0,
                usage_percent: mem,
            },
            disks: vec![DiskInfo {
                name: "/dev/sda1".into(),
                mount_point: "/".into(),
                total_gb: 256.0,
                used_gb: 256.0 * disk_pct / 100.0,
                available_gb: 256.0 * (100.0 - disk_pct) / 100.0,
                usage_percent: disk_pct,
                file_system: "ext4".into(),
            }],
            battery: None,
            network: NetworkInfo {
                interfaces: vec![],
                total_received_mb: 0,
                total_transmitted_mb: 0,
            },
            processes: vec![ProcessInfo {
                pid: 1,
                name: "chrome".into(),
                cpu_usage: 55.0,
                memory_mb: 512.0,
            }],
            startup_apps: vec![],
            installed_software: vec![],
            hardware_summary: HardwareSummary {
                cpu_brand: "Intel".into(),
                total_memory_gb: 16.0,
                total_disk_gb: 256.0,
                disk_count: 1,
            },
            issues: vec![ScanIssue {
                id: "high-cpu".into(),
                title: "High CPU usage".into(),
                description: "CPU hot".into(),
                severity: "medium".into(),
                category: "performance".into(),
            }],
            updates_available: false,
        }
    }

    #[test]
    fn detects_cpu_memory_disk_and_health_alerts() {
        let scan = sample_scan(62, 88.0, 90.0, 93.0);
        let alerts = detect_metric_alerts(&scan, 70);
        let types: Vec<_> = alerts.iter().map(|a| a.event_type.as_str()).collect();
        assert!(types.contains(&"health_threshold"));
        assert!(types.contains(&"high_cpu"));
        assert!(types.contains(&"high_memory"));
        assert!(types.iter().any(|t| t.starts_with("low_disk:")));
    }

    #[test]
    fn healthy_scan_produces_no_alerts() {
        let scan = sample_scan(95, 20.0, 40.0, 50.0);
        let alerts = detect_metric_alerts(&scan, 70);
        assert!(alerts.is_empty());
    }
}
