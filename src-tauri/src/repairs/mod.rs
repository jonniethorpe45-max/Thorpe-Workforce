use crate::db::RepairRecord;
use crate::licensing;
use crate::AppState;
use chrono::Utc;
use serde::{Deserialize, Serialize};
use std::process::Command;
use tauri::State;
use uuid::Uuid;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RepairAction {
    pub id: String,
    pub name: String,
    pub description: String,
    pub purpose: String,
    pub risk_level: String,
    pub category: String,
    pub requires_confirmation: bool,
    pub platform: Vec<String>,
}

fn get_available_actions() -> Vec<RepairAction> {
    let mut actions = vec![
        RepairAction {
            id: "temp-cleanup".to_string(),
            name: "Clean Temporary Files".to_string(),
            description: "Remove temporary files and caches to free disk space.".to_string(),
            purpose: "Frees disk space by removing non-essential temporary files.".to_string(),
            risk_level: "low".to_string(),
            category: "storage".to_string(),
            requires_confirmation: true,
            platform: vec!["windows".to_string(), "macos".to_string(), "linux".to_string()],
        },
        RepairAction {
            id: "dns-flush".to_string(),
            name: "Flush DNS Cache".to_string(),
            description: "Clear the DNS resolver cache to fix connectivity issues.".to_string(),
            purpose: "Resolves DNS-related connectivity problems.".to_string(),
            risk_level: "low".to_string(),
            category: "network".to_string(),
            requires_confirmation: true,
            platform: vec!["windows".to_string(), "macos".to_string(), "linux".to_string()],
        },
        RepairAction {
            id: "disk-analysis".to_string(),
            name: "Disk Space Analysis".to_string(),
            description: "Analyze disk usage and identify large files and folders.".to_string(),
            purpose: "Helps identify what's consuming disk space.".to_string(),
            risk_level: "low".to_string(),
            category: "storage".to_string(),
            requires_confirmation: false,
            platform: vec!["windows".to_string(), "macos".to_string(), "linux".to_string()],
        },
        RepairAction {
            id: "startup-review".to_string(),
            name: "Startup Optimization Review".to_string(),
            description: "Review startup applications and provide optimization recommendations.".to_string(),
            purpose: "Improves boot time by identifying unnecessary startup programs.".to_string(),
            risk_level: "low".to_string(),
            category: "performance".to_string(),
            requires_confirmation: false,
            platform: vec!["windows".to_string(), "macos".to_string(), "linux".to_string()],
        },
        RepairAction {
            id: "high-resource-id".to_string(),
            name: "Identify High Resource Usage".to_string(),
            description: "List processes consuming the most CPU and memory.".to_string(),
            purpose: "Helps identify applications causing performance issues.".to_string(),
            risk_level: "low".to_string(),
            category: "performance".to_string(),
            requires_confirmation: false,
            platform: vec!["windows".to_string(), "macos".to_string(), "linux".to_string()],
        },
        RepairAction {
            id: "network-diagnostics".to_string(),
            name: "Network Troubleshooting".to_string(),
            description: "Run basic network connectivity diagnostics.".to_string(),
            purpose: "Tests network connectivity and identifies common issues.".to_string(),
            risk_level: "low".to_string(),
            category: "network".to_string(),
            requires_confirmation: false,
            platform: vec!["windows".to_string(), "macos".to_string(), "linux".to_string()],
        },
        RepairAction {
            id: "update-check".to_string(),
            name: "Check for Updates".to_string(),
            description: "Check if system updates are available.".to_string(),
            purpose: "Ensures your system has the latest security patches.".to_string(),
            risk_level: "low".to_string(),
            category: "updates".to_string(),
            requires_confirmation: false,
            platform: vec!["windows".to_string(), "macos".to_string(), "linux".to_string()],
        },
        RepairAction {
            id: "restart-recommend".to_string(),
            name: "Restart Recommendation".to_string(),
            description: "Analyze uptime and recommend restart if needed.".to_string(),
            purpose: "A restart can resolve many transient system issues.".to_string(),
            risk_level: "low".to_string(),
            category: "maintenance".to_string(),
            requires_confirmation: false,
            platform: vec!["windows".to_string(), "macos".to_string(), "linux".to_string()],
        },
    ];

    #[cfg(target_os = "windows")]
    actions.push(RepairAction {
        id: "print-spooler-restart".to_string(),
        name: "Restart Print Spooler".to_string(),
        description: "Restart the Windows Print Spooler service to fix printing issues.".to_string(),
        purpose: "Clears stuck print jobs and resets the printing subsystem.".to_string(),
        risk_level: "medium".to_string(),
        category: "printers".to_string(),
        requires_confirmation: true,
        platform: vec!["windows".to_string()],
    });

    let current_os = std::env::consts::OS.to_string();
    actions.retain(|a| a.platform.contains(&current_os));
    actions
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RepairResult {
    pub success: bool,
    pub message: String,
    pub details: Option<String>,
    pub record_id: String,
}

fn execute_action(action_id: &str) -> (bool, String, Option<String>) {
    match action_id {
        "temp-cleanup" => cleanup_temp_files(),
        "dns-flush" => flush_dns(),
        "disk-analysis" => analyze_disk(),
        "startup-review" => review_startup(),
        "high-resource-id" => identify_high_resource(),
        "network-diagnostics" => network_diagnostics(),
        "update-check" => check_updates(),
        "restart-recommend" => restart_recommendation(),
        #[cfg(target_os = "windows")]
        "print-spooler-restart" => restart_print_spooler(),
        _ => (false, "Unknown repair action".to_string(), None),
    }
}

fn cleanup_temp_files() -> (bool, String, Option<String>) {
    let mut cleaned = Vec::new();
    if let Some(temp_dir) = std::env::var_os("TEMP").or_else(|| std::env::var_os("TMP")) {
        let path = std::path::Path::new(&temp_dir);
        if path.exists() {
            let mut count = 0u32;
            let cutoff = std::time::SystemTime::now()
                .checked_sub(std::time::Duration::from_secs(3600))
                .unwrap_or(std::time::SystemTime::UNIX_EPOCH);
            if let Ok(entries) = std::fs::read_dir(path) {
                for entry in entries.flatten().take(200) {
                    let entry_path = entry.path();
                    if !entry_path.is_file() {
                        continue;
                    }
                    let ext = entry_path
                        .extension()
                        .and_then(|e| e.to_str())
                        .unwrap_or("")
                        .to_ascii_lowercase();
                    if ext != "tmp" && ext != "temp" && ext != "log" {
                        continue;
                    }
                    let modified = entry
                        .metadata()
                        .and_then(|m| m.modified())
                        .unwrap_or(std::time::SystemTime::UNIX_EPOCH);
                    if modified > cutoff {
                        continue;
                    }
                    if std::fs::remove_file(&entry_path).is_ok() {
                        count += 1;
                    }
                }
            }
            cleaned.push(format!("Removed {} old temporary files from {:?}", count, path));
        }
    }
    #[cfg(target_os = "linux")]
    {
        if let Ok(output) = Command::new("sh").args(["-c", "du -sh /tmp 2>/dev/null"]).output() {
            cleaned.push(String::from_utf8_lossy(&output.stdout).trim().to_string());
        }
    }
    let details = if cleaned.is_empty() {
        "No temporary files found to clean.".to_string()
    } else {
        cleaned.join("\n")
    };
    (true, "Temporary file cleanup completed.".to_string(), Some(details))
}

fn flush_dns() -> (bool, String, Option<String>) {
    let result = if cfg!(target_os = "windows") {
        Command::new("ipconfig").args(["/flushdns"]).output()
    } else if cfg!(target_os = "macos") {
        Command::new("dscacheutil").args(["-flushcache"]).output()
    } else if cfg!(target_os = "linux") {
        Command::new("sh")
            .args(["-c", "resolvectl flush-caches 2>/dev/null || systemd-resolve --flush-caches 2>/dev/null || true"])
            .output()
    } else {
        Err(std::io::Error::new(std::io::ErrorKind::Unsupported, "Unsupported platform"))
    };

    match result {
        Ok(output) => {
            let msg = if output.status.success() {
                "DNS cache flushed successfully.".to_string()
            } else {
                "DNS flush attempted. Some systems require administrator privileges.".to_string()
            };
            (true, msg, Some(String::from_utf8_lossy(&output.stdout).to_string()))
        }
        Err(e) => (false, format!("Failed to flush DNS: {}", e), None),
    }
}

fn analyze_disk() -> (bool, String, Option<String>) {
    use sysinfo::Disks;
    let disks = Disks::new_with_refreshed_list();
    let mut report = String::new();
    for disk in disks.list() {
        let total = disk.total_space() as f64 / 1_073_741_824.0;
        let avail = disk.available_space() as f64 / 1_073_741_824.0;
        let used = total - avail;
        let pct = if total > 0.0 { (used / total) * 100.0 } else { 0.0 };
        report.push_str(&format!(
            "{}: {:.1} GB used / {:.1} GB total ({:.1}%)\n",
            disk.mount_point().to_string_lossy(),
            used,
            total,
            pct
        ));
    }
    (true, "Disk analysis complete.".to_string(), Some(report))
}

fn review_startup() -> (bool, String, Option<String>) {
    let advice = match std::env::consts::OS {
        "windows" => "Open Task Manager (Ctrl+Shift+Esc) > Startup tab. Disable programs you don't need at boot.",
        "macos" => "Go to System Settings > General > Login Items. Remove unnecessary startup items.",
        "linux" => "Check ~/.config/autostart/ and system-wide /etc/xdg/autostart/ for startup entries.",
        _ => "Review your system's startup application settings.",
    };
    (true, "Startup review recommendations generated.".to_string(), Some(advice.to_string()))
}

fn identify_high_resource() -> (bool, String, Option<String>) {
    use sysinfo::System;
    let mut sys = System::new_all();
    sys.refresh_all();
    std::thread::sleep(std::time::Duration::from_millis(200));
    sys.refresh_cpu_usage();

    let mut procs: Vec<_> = sys
        .processes()
        .iter()
        .map(|(pid, p)| (pid.as_u32(), p.name().to_string_lossy().to_string(), p.cpu_usage(), p.memory() as f64 / 1_048_576.0))
        .collect();
    procs.sort_by(|a, b| b.2.partial_cmp(&a.2).unwrap_or(std::cmp::Ordering::Equal));

    let mut report = String::from("Top resource-consuming processes:\n\n");
    for (pid, name, cpu, mem) in procs.iter().take(10) {
        report.push_str(&format!("  {} (PID {}) — CPU: {:.1}%, RAM: {:.0} MB\n", name, pid, cpu, mem));
    }
    (true, "High resource usage analysis complete.".to_string(), Some(report))
}

fn network_diagnostics() -> (bool, String, Option<String>) {
    let mut results = Vec::new();

    let ping = Command::new("ping")
        .args(if cfg!(target_os = "windows") {
            vec!["-n", "3", "1.1.1.1"]
        } else {
            vec!["-c", "3", "1.1.1.1"]
        })
        .output();

    match ping {
        Ok(output) => {
            let success = output.status.success();
            results.push(format!(
                "Ping to 1.1.1.1: {}",
                if success { "Success" } else { "Failed" }
            ));
        }
        Err(_) => results.push("Ping test: Unable to run (ping may not be available)".to_string()),
    }

    (true, "Network diagnostics complete.".to_string(), Some(results.join("\n")))
}

fn check_updates() -> (bool, String, Option<String>) {
    let msg = match std::env::consts::OS {
        "windows" => "Open Settings > Windows Update to check for available updates.",
        "macos" => "Open System Settings > General > Software Update to check for updates.",
        "linux" => "Use your package manager (apt, dnf, pacman) to check for system updates.",
        _ => "Check your system settings for available updates.",
    };
    (true, "Update check guidance provided.".to_string(), Some(msg.to_string()))
}

fn restart_recommendation() -> (bool, String, Option<String>) {
    use sysinfo::System;
    let uptime_secs = System::uptime();
    let days = uptime_secs / 86400;
    let hours = (uptime_secs % 86400) / 3600;

    let recommendation = if days > 7 {
        format!(
            "System uptime: {} days, {} hours. A restart is recommended to clear memory leaks and apply pending updates.",
            days, hours
        )
    } else if days > 3 {
        format!(
            "System uptime: {} days, {} hours. Consider restarting soon for optimal performance.",
            days, hours
        )
    } else {
        format!(
            "System uptime: {} days, {} hours. No immediate restart needed.",
            days, hours
        )
    };
    (true, "Restart analysis complete.".to_string(), Some(recommendation))
}

#[cfg(target_os = "windows")]
fn restart_print_spooler() -> (bool, String, Option<String>) {
    let stop = Command::new("net").args(["stop", "spooler"]).output();
    let start = Command::new("net").args(["start", "spooler"]).output();

    match (stop, start) {
        (Ok(_), Ok(start_out)) => {
            if start_out.status.success() {
                (true, "Print Spooler restarted successfully.".to_string(), None)
            } else {
                (
                    false,
                    "Failed to restart Print Spooler. Administrator privileges may be required.".to_string(),
                    Some(String::from_utf8_lossy(&start_out.stderr).to_string()),
                )
            }
        }
        _ => (
            false,
            "Failed to restart Print Spooler. Run Thorpe as Administrator.".to_string(),
            None,
        ),
    }
}

#[tauri::command]
pub fn list_repair_actions() -> Result<Vec<RepairAction>, String> {
    Ok(get_available_actions())
}

#[tauri::command]
pub fn execute_repair(state: State<AppState>, action_id: String, confirmed: bool) -> Result<RepairResult, String> {
    {
        let db = state.lock_db()?;
        licensing::require_feature(&db, "repair_center")?;
    }

    let actions = get_available_actions();
    let action = actions
        .iter()
        .find(|a| a.id == action_id)
        .ok_or_else(|| "Repair action not found".to_string())?;

    if action.requires_confirmation && !confirmed {
        return Err("This action requires explicit user confirmation.".to_string());
    }

    let (success, message, details) = execute_action(&action_id);
    let record = RepairRecord {
        id: Uuid::new_v4().to_string(),
        action_id: action.id.clone(),
        action_name: action.name.clone(),
        status: if success { "completed" } else { "failed" }.to_string(),
        details: details.clone(),
        risk_level: action.risk_level.clone(),
        created_at: Utc::now().to_rfc3339(),
    };
    let record_id = record.id.clone();
    state.lock_db()?.save_repair(&record).map_err(|e| e.to_string())?;

    Ok(RepairResult {
        success,
        message,
        details,
        record_id,
    })
}

#[tauri::command]
pub fn list_repair_history(state: State<AppState>, limit: Option<i64>) -> Result<Vec<RepairRecord>, String> {
    state
        .db
        .lock()
        .unwrap()
        .list_repairs(limit.unwrap_or(50))
        .map_err(|e| e.to_string())
}
