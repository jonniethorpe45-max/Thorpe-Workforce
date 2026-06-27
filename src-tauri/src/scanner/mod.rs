use crate::db::ScanRecord;
use crate::AppState;
use serde::{Deserialize, Serialize};
use sysinfo::{Disks, Networks, System};
use tauri::State;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SystemScanResult {
    pub id: String,
    pub timestamp: String,
    pub health_score: i32,
    pub os: OsInfo,
    pub cpu: CpuInfo,
    pub memory: MemoryInfo,
    pub disks: Vec<DiskInfo>,
    pub battery: Option<BatteryInfo>,
    pub network: NetworkInfo,
    pub processes: Vec<ProcessInfo>,
    pub startup_apps: Vec<String>,
    pub installed_software: Vec<String>,
    pub hardware_summary: HardwareSummary,
    pub issues: Vec<ScanIssue>,
    pub updates_available: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct OsInfo {
    pub name: String,
    pub version: String,
    pub hostname: String,
    pub kernel_version: String,
    pub arch: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CpuInfo {
    pub brand: String,
    pub cores: usize,
    pub usage_percent: f32,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MemoryInfo {
    pub total_gb: f64,
    pub used_gb: f64,
    pub available_gb: f64,
    pub usage_percent: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DiskInfo {
    pub name: String,
    pub mount_point: String,
    pub total_gb: f64,
    pub used_gb: f64,
    pub available_gb: f64,
    pub usage_percent: f64,
    pub file_system: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BatteryInfo {
    pub percentage: f32,
    pub charging: bool,
    pub time_remaining_minutes: Option<u32>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct NetworkInfo {
    pub interfaces: Vec<NetworkInterface>,
    pub total_received_mb: u64,
    pub total_transmitted_mb: u64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct NetworkInterface {
    pub name: String,
    pub received_mb: u64,
    pub transmitted_mb: u64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ProcessInfo {
    pub pid: u32,
    pub name: String,
    pub cpu_usage: f32,
    pub memory_mb: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct HardwareSummary {
    pub cpu_brand: String,
    pub total_memory_gb: f64,
    pub total_disk_gb: f64,
    pub disk_count: usize,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ScanIssue {
    pub id: String,
    pub title: String,
    pub description: String,
    pub severity: String,
    pub category: String,
}

fn collect_system_info() -> SystemScanResult {
    let mut sys = System::new_all();
    sys.refresh_all();
    std::thread::sleep(std::time::Duration::from_millis(200));
    sys.refresh_cpu_usage();

    let hostname = System::host_name().unwrap_or_else(|| "unknown".to_string());
    let os_name = System::name().unwrap_or_else(|| std::env::consts::OS.to_string());
    let os_version = System::os_version().unwrap_or_else(|| "unknown".to_string());
    let kernel = System::kernel_version().unwrap_or_else(|| "unknown".to_string());

    let total_mem = sys.total_memory() as f64 / 1_073_741_824.0;
    let used_mem = sys.used_memory() as f64 / 1_073_741_824.0;
    let avail_mem = sys.available_memory() as f64 / 1_073_741_824.0;
    let mem_pct = if total_mem > 0.0 { (used_mem / total_mem) * 100.0 } else { 0.0 };

    let cpu_brand = sys
        .cpus()
        .first()
        .map(|c| c.brand().to_string())
        .unwrap_or_else(|| "Unknown CPU".to_string());
    let cpu_usage: f32 = sys.global_cpu_usage();
    let cpu_cores = sys.cpus().len();

    let disks_data = Disks::new_with_refreshed_list();
    let mut disks = Vec::new();
    let mut total_disk_gb = 0.0;
    for disk in disks_data.list() {
        let total = disk.total_space() as f64 / 1_073_741_824.0;
        let available = disk.available_space() as f64 / 1_073_741_824.0;
        let used = total - available;
        let pct = if total > 0.0 { (used / total) * 100.0 } else { 0.0 };
        total_disk_gb += total;
        disks.push(DiskInfo {
            name: disk.name().to_string_lossy().to_string(),
            mount_point: disk.mount_point().to_string_lossy().to_string(),
            total_gb: (total * 100.0).round() / 100.0,
            used_gb: (used * 100.0).round() / 100.0,
            available_gb: (available * 100.0).round() / 100.0,
            usage_percent: (pct * 10.0).round() / 10.0,
            file_system: disk.file_system().to_string_lossy().to_string(),
        });
    }

    let networks = Networks::new_with_refreshed_list();
    let mut interfaces = Vec::new();
    let mut total_rx = 0u64;
    let mut total_tx = 0u64;
    for (name, data) in networks.list() {
        let rx = data.received() / 1_048_576;
        let tx = data.transmitted() / 1_048_576;
        total_rx += rx;
        total_tx += tx;
        interfaces.push(NetworkInterface {
            name: name.to_string(),
            received_mb: rx,
            transmitted_mb: tx,
        });
    }

    let mut processes: Vec<ProcessInfo> = sys
        .processes()
        .iter()
        .map(|(pid, proc_)| ProcessInfo {
            pid: pid.as_u32(),
            name: proc_.name().to_string_lossy().to_string(),
            cpu_usage: proc_.cpu_usage(),
            memory_mb: proc_.memory() as f64 / 1_048_576.0,
        })
        .collect();
    processes.sort_by(|a, b| b.cpu_usage.partial_cmp(&a.cpu_usage).unwrap_or(std::cmp::Ordering::Equal));
    processes.truncate(15);

    let startup_apps = get_startup_apps();
    let installed_software = get_installed_software_sample();
    let battery = get_battery_info();
    let issues = analyze_issues(&disks, mem_pct, cpu_usage, &processes);
    let health_score = calculate_health_score(&issues, mem_pct, &disks);

    SystemScanResult {
        id: String::new(),
        timestamp: chrono::Utc::now().to_rfc3339(),
        health_score,
        os: OsInfo {
            name: os_name,
            version: os_version,
            hostname,
            kernel_version: kernel,
            arch: std::env::consts::ARCH.to_string(),
        },
        cpu: CpuInfo {
            brand: cpu_brand.clone(),
            cores: cpu_cores,
            usage_percent: cpu_usage,
        },
        memory: MemoryInfo {
            total_gb: (total_mem * 100.0).round() / 100.0,
            used_gb: (used_mem * 100.0).round() / 100.0,
            available_gb: (avail_mem * 100.0).round() / 100.0,
            usage_percent: (mem_pct * 10.0).round() / 10.0,
        },
        disks,
        battery,
        network: NetworkInfo {
            interfaces,
            total_received_mb: total_rx,
            total_transmitted_mb: total_tx,
        },
        processes,
        startup_apps,
        installed_software,
        hardware_summary: HardwareSummary {
            cpu_brand,
            total_memory_gb: (total_mem * 100.0).round() / 100.0,
            total_disk_gb: (total_disk_gb * 100.0).round() / 100.0,
            disk_count: disks_data.list().len(),
        },
        issues: issues.clone(),
        updates_available: check_updates_available(),
    }
}

fn get_startup_apps() -> Vec<String> {
    let mut apps = Vec::new();
    #[cfg(target_os = "windows")]
    {
        apps.push("Windows Startup items — review in Task Manager".to_string());
    }
    #[cfg(target_os = "macos")]
    {
        apps.push("macOS Login Items — review in System Settings > General > Login Items".to_string());
    }
    #[cfg(target_os = "linux")]
    {
        apps.push("Linux autostart entries — review in ~/.config/autostart/".to_string());
    }
    apps
}

fn get_installed_software_sample() -> Vec<String> {
    vec![
        "System software inventory collected at scan time".to_string(),
        format!("Platform: {}", std::env::consts::OS),
    ]
}

fn get_battery_info() -> Option<BatteryInfo> {
    None
}

fn check_updates_available() -> bool {
    false
}

fn analyze_issues(disks: &[DiskInfo], mem_pct: f64, cpu_usage: f32, processes: &[ProcessInfo]) -> Vec<ScanIssue> {
    let mut issues = Vec::new();

    for disk in disks {
        if disk.usage_percent > 90.0 {
            issues.push(ScanIssue {
                id: format!("disk-full-{}", disk.mount_point),
                title: format!("Low disk space on {}", disk.mount_point),
                description: format!(
                    "Disk {} is {:.1}% full with only {:.1} GB available.",
                    disk.mount_point, disk.usage_percent, disk.available_gb
                ),
                severity: if disk.usage_percent > 95.0 { "critical" } else { "high" }.to_string(),
                category: "storage".to_string(),
            });
        }
    }

    if mem_pct > 85.0 {
        issues.push(ScanIssue {
            id: "high-memory".to_string(),
            title: "High memory usage".to_string(),
            description: format!("Memory usage is at {:.1}%. Consider closing unused applications.", mem_pct),
            severity: if mem_pct > 95.0 { "critical" } else { "medium" }.to_string(),
            category: "performance".to_string(),
        });
    }

    if cpu_usage > 80.0 {
        issues.push(ScanIssue {
            id: "high-cpu".to_string(),
            title: "High CPU usage".to_string(),
            description: format!("CPU usage is at {:.1}%. A process may be consuming excessive resources.", cpu_usage),
            severity: "medium".to_string(),
            category: "performance".to_string(),
        });
    }

    for proc in processes.iter().take(3) {
        if proc.cpu_usage > 50.0 {
            issues.push(ScanIssue {
                id: format!("proc-{}", proc.pid),
                title: format!("High CPU: {}", proc.name),
                description: format!(
                    "Process '{}' (PID {}) is using {:.1}% CPU and {:.0} MB RAM.",
                    proc.name, proc.pid, proc.cpu_usage, proc.memory_mb
                ),
                severity: "medium".to_string(),
                category: "process".to_string(),
            });
        }
    }

    issues
}

fn calculate_health_score(issues: &[ScanIssue], mem_pct: f64, disks: &[DiskInfo]) -> i32 {
    let mut score = 100i32;

    for issue in issues {
        score -= match issue.severity.as_str() {
            "critical" => 25,
            "high" => 15,
            "medium" => 8,
            _ => 3,
        };
    }

    if mem_pct > 90.0 {
        score -= 10;
    }

    for disk in disks {
        if disk.usage_percent > 95.0 {
            score -= 10;
        }
    }

    score.clamp(0, 100)
}

#[tauri::command]
pub fn run_system_scan(state: State<AppState>) -> Result<SystemScanResult, String> {
    let mut result = collect_system_info();
    let scan_json = serde_json::to_string(&result).map_err(|e| e.to_string())?;
    let scan_id = state
        .db
        .lock()
        .unwrap()
        .save_scan(&scan_json, result.health_score)
        .map_err(|e| e.to_string())?;
    result.id = scan_id;
    Ok(result)
}

#[tauri::command]
pub fn get_last_scan(state: State<AppState>) -> Result<Option<SystemScanResult>, String> {
    let scans = state.db.lock().unwrap().list_scans(1).map_err(|e| e.to_string())?;
    if let Some(scan) = scans.first() {
        let mut result: SystemScanResult =
            serde_json::from_str(&scan.scan_data).map_err(|e| e.to_string())?;
        result.id = scan.id.clone();
        Ok(Some(result))
    } else {
        Ok(None)
    }
}

#[tauri::command]
pub fn list_scans(state: State<AppState>, limit: Option<i64>) -> Result<Vec<ScanRecord>, String> {
    state
        .db
        .lock()
        .unwrap()
        .list_scans(limit.unwrap_or(20))
        .map_err(|e| e.to_string())
}
