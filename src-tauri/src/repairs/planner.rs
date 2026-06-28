use crate::scanner::SystemScanResult;

/// Map a user issue (and optional scan) to repair actions Jonathan should run automatically.
pub fn plan_repairs(message: &str, scan: Option<&SystemScanResult>) -> Vec<String> {
    let msg = message.to_lowercase();
    let mut actions: Vec<String> = Vec::new();

    fn push_unique(actions: &mut Vec<String>, id: &str) {
        if !actions.iter().any(|a| a == id) {
            actions.push(id.to_string());
        }
    }

    if msg.contains("wifi")
        || msg.contains("wi-fi")
        || msg.contains("internet")
        || msg.contains("network")
        || msg.contains("dns")
        || msg.contains("connect")
    {
        push_unique(&mut actions, "dns-flush");
        push_unique(&mut actions, "network-diagnostics");
    }

    if msg.contains("slow")
        || msg.contains("performance")
        || msg.contains("lag")
        || msg.contains("freeze")
        || msg.contains("boot")
    {
        push_unique(&mut actions, "high-resource-id");
        push_unique(&mut actions, "startup-review");
        push_unique(&mut actions, "temp-cleanup");
        push_unique(&mut actions, "restart-recommend");
    }

    if msg.contains("disk")
        || msg.contains("storage")
        || msg.contains("space")
        || msg.contains("full")
    {
        push_unique(&mut actions, "disk-analysis");
        push_unique(&mut actions, "temp-cleanup");
    }

    if msg.contains("print") || msg.contains("printer") {
        #[cfg(target_os = "windows")]
        push_unique(&mut actions, "print-spooler-restart");
        push_unique(&mut actions, "network-diagnostics");
    }

    if msg.contains("update") || msg.contains("patch") || msg.contains("security") {
        push_unique(&mut actions, "update-check");
    }

    if let Some(scan) = scan {
        for issue in &scan.issues {
            match issue.category.as_str() {
                "storage" => {
                    push_unique(&mut actions, "temp-cleanup");
                    push_unique(&mut actions, "disk-analysis");
                }
                "performance" | "process" => {
                    push_unique(&mut actions, "high-resource-id");
                    push_unique(&mut actions, "startup-review");
                    push_unique(&mut actions, "temp-cleanup");
                }
                "network" => {
                    push_unique(&mut actions, "dns-flush");
                    push_unique(&mut actions, "network-diagnostics");
                }
                _ => {}
            }
        }

        if scan.memory.usage_percent > 85.0 {
            push_unique(&mut actions, "high-resource-id");
        }
    }

    if actions.is_empty()
        || msg.contains("fix")
        || msg.contains("repair")
        || msg.contains("help")
        || msg.contains("issue")
        || msg.contains("problem")
        || msg.contains("broken")
    {
        push_unique(&mut actions, "network-diagnostics");
        push_unique(&mut actions, "high-resource-id");
        push_unique(&mut actions, "disk-analysis");
        push_unique(&mut actions, "update-check");
        push_unique(&mut actions, "temp-cleanup");
    }

    actions
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::scanner::{CpuInfo, HardwareSummary, MemoryInfo, NetworkInfo, OsInfo, SystemScanResult};

    fn sample_scan() -> SystemScanResult {
        SystemScanResult {
            id: "scan-1".into(),
            timestamp: "2026-01-01".into(),
            health_score: 70,
            os: OsInfo {
                name: "Windows".into(),
                version: "11".into(),
                hostname: "pc".into(),
                kernel_version: "".into(),
                arch: "x86_64".into(),
            },
            cpu: CpuInfo {
                brand: "Intel".into(),
                cores: 4,
                usage_percent: 20.0,
            },
            memory: MemoryInfo {
                total_gb: 16.0,
                used_gb: 14.0,
                available_gb: 2.0,
                usage_percent: 87.5,
            },
            disks: vec![],
            battery: None,
            network: NetworkInfo {
                interfaces: vec![],
                total_received_mb: 0,
                total_transmitted_mb: 0,
            },
            processes: vec![],
            startup_apps: vec![],
            installed_software: vec![],
            hardware_summary: HardwareSummary {
                cpu_brand: "Intel".into(),
                total_memory_gb: 16.0,
                total_disk_gb: 256.0,
                disk_count: 1,
            },
            issues: vec![],
            updates_available: false,
        }
    }

    #[test]
    fn plans_network_repairs_for_wifi_issue() {
        let planned = plan_repairs("My wifi is not working", None);
        assert!(planned.contains(&"dns-flush".to_string()));
        assert!(planned.contains(&"network-diagnostics".to_string()));
    }

    #[test]
    fn plans_performance_repairs_from_scan() {
        let scan = sample_scan();
        let planned = plan_repairs("fix my computer", Some(&scan));
        assert!(planned.contains(&"high-resource-id".to_string()));
    }
}
