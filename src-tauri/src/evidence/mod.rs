use crate::scanner::SystemScanResult;
use serde::{Deserialize, Serialize};
use std::process::Command;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SystemEvidence {
    pub platform: String,
    pub collected_at: String,
    pub event_log_excerpt: Option<String>,
    pub service_summary: Option<String>,
    pub network_summary: Option<String>,
}

pub fn collect_system_evidence(scan: Option<&SystemScanResult>) -> SystemEvidence {
    let network_summary = scan.map(|s| {
        format!(
            "Interfaces: {}; RX {} MB / TX {} MB",
            s.network.interfaces.len(),
            s.network.total_received_mb,
            s.network.total_transmitted_mb
        )
    });

    SystemEvidence {
        platform: std::env::consts::OS.to_string(),
        collected_at: chrono::Utc::now().to_rfc3339(),
        event_log_excerpt: collect_event_log_excerpt(),
        service_summary: collect_service_summary(),
        network_summary,
    }
}

fn run_shell(cmd: &str) -> Option<String> {
    Command::new("sh")
        .args(["-c", cmd])
        .output()
        .ok()
        .map(|o| String::from_utf8_lossy(&o.stdout).trim().to_string())
        .filter(|s| !s.is_empty())
}

fn collect_event_log_excerpt() -> Option<String> {
    #[cfg(target_os = "windows")]
    {
        return Command::new("powershell")
            .args([
                "-NoProfile",
                "-Command",
                "Get-EventLog -LogName System -Newest 8 -EntryType Error,Warning | Format-Table -AutoSize | Out-String -Width 120",
            ])
            .output()
            .ok()
            .map(|o| String::from_utf8_lossy(&o.stdout).chars().take(2000).collect());
    }

    #[cfg(target_os = "linux")]
    {
        return run_shell("journalctl -p 3 -n 12 --no-pager 2>/dev/null | tail -20");
    }

    #[cfg(target_os = "macos")]
    {
        return run_shell("log show --predicate 'eventType == logEvent' --last 2m --style compact 2>/dev/null | tail -15");
    }

    #[allow(unreachable_code)]
    None
}

fn collect_service_summary() -> Option<String> {
    #[cfg(target_os = "windows")]
    {
        return Command::new("sc")
            .args(["query", "state=", "all"])
            .output()
            .ok()
            .map(|o| {
                String::from_utf8_lossy(&o.stdout)
                    .lines()
                    .filter(|l| l.contains("SERVICE_NAME") || l.contains("STATE"))
                    .take(20)
                    .collect::<Vec<_>>()
                    .join("\n")
            })
            .filter(|s| !s.is_empty());
    }

    #[cfg(target_os = "linux")]
    {
        return run_shell("systemctl list-units --failed --no-pager 2>/dev/null | head -15");
    }

    #[cfg(target_os = "macos")]
    {
        return run_shell("launchctl list 2>/dev/null | head -15");
    }

    #[allow(unreachable_code)]
    None
}
