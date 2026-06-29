use serde::{Deserialize, Serialize};
use std::net::ToSocketAddrs;
use std::process::Command;

use crate::db::ConnectivityDiagnosticRecord;
use crate::AppState;
use chrono::Utc;
use tauri::State;
use uuid::Uuid;

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "lowercase")]
pub enum CheckStatus {
    Pass,
    Fail,
    Warn,
    Skipped,
}

impl CheckStatus {
    fn as_str(&self) -> &'static str {
        match self {
            Self::Pass => "pass",
            Self::Fail => "fail",
            Self::Warn => "warn",
            Self::Skipped => "skipped",
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ConnectivityCheck {
    pub name: String,
    pub status: String,
    pub detail: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ConnectivityReport {
    pub checks: Vec<ConnectivityCheck>,
    pub overall_status: String,
    pub recommended_actions: Vec<String>,
    pub playbook_summary: String,
    pub offline_capable: bool,
}

pub fn is_connectivity_issue(message: &str) -> bool {
    let msg = message.to_lowercase();
    [
        "wifi", "wi-fi", "internet", "network", "dns", "connect", "online", "offline",
        "ethernet", "broadband", "no connection", "can't connect", "cannot connect",
        "web page", "website", "browser won't", "slow internet",
    ]
    .iter()
    .any(|term| msg.contains(term))
}

pub fn run_connectivity_suite() -> ConnectivityReport {
    let mut checks = Vec::new();

    let adapter = check_network_adapter();
    checks.push(adapter.clone());

    let gateway_ip = detect_default_gateway();
    let gateway = check_ping(
        "Default gateway",
        gateway_ip.as_deref(),
        "No default gateway detected — Wi-Fi or Ethernet may be disconnected.",
    );
    checks.push(gateway.clone());

    let dns_resolution = check_dns_resolution();
    checks.push(dns_resolution.clone());

    let cloudflare = check_ping("Internet (1.1.1.1)", Some("1.1.1.1"), "Could not reach Cloudflare DNS.");
    checks.push(cloudflare.clone());

    let google_dns = check_ping("Internet (8.8.8.8)", Some("8.8.8.8"), "Could not reach Google DNS.");
    checks.push(google_dns.clone());

    let (recommended_actions, playbook_summary, overall_status) =
        evaluate_playbook(&checks, &adapter, &gateway, &dns_resolution, &cloudflare, &google_dns);

    ConnectivityReport {
        checks,
        overall_status,
        recommended_actions,
        playbook_summary,
        offline_capable: true,
    }
}

fn check_network_adapter() -> ConnectivityCheck {
    #[cfg(target_os = "windows")]
    {
        if let Ok(output) = Command::new("powershell")
            .args([
                "-NoProfile",
                "-Command",
                "Get-NetAdapter | Where-Object Status -eq 'Up' | Select-Object -First 1 -ExpandProperty Name",
            ])
            .output()
        {
            let name = String::from_utf8_lossy(&output.stdout).trim().to_string();
            if output.status.success() && !name.is_empty() {
                return ConnectivityCheck {
                    name: "Network adapter".into(),
                    status: CheckStatus::Pass.as_str().into(),
                    detail: format!("Active adapter: {name}"),
                };
            }
        }
        return ConnectivityCheck {
            name: "Network adapter".into(),
            status: CheckStatus::Fail.as_str().into(),
            detail: "No active network adapter found. Check Wi-Fi or Ethernet is enabled.".into(),
        };
    }

    #[cfg(any(target_os = "linux", target_os = "macos"))]
    {
        if let Ok(output) = Command::new("sh")
            .arg("-c")
            .arg("ip -o link show up 2>/dev/null | grep -v 'lo:' | head -1 | awk -F': ' '{print $2}'")
            .output()
        {
            let name = String::from_utf8_lossy(&output.stdout).trim().to_string();
            if !name.is_empty() {
                return ConnectivityCheck {
                    name: "Network adapter".into(),
                    status: CheckStatus::Pass.as_str().into(),
                    detail: format!("Active interface: {name}"),
                };
            }
        }
        return ConnectivityCheck {
            name: "Network adapter".into(),
            status: CheckStatus::Warn.as_str().into(),
            detail: "Could not confirm an active network interface. Verify Wi-Fi or Ethernet is connected."
                .into(),
        };
    }

    #[cfg(not(any(target_os = "windows", target_os = "linux", target_os = "macos")))]
    ConnectivityCheck {
        name: "Network adapter".into(),
        status: CheckStatus::Skipped.as_str().into(),
        detail: "Adapter check not available on this platform.".into(),
    }
}

pub fn detect_default_gateway() -> Option<String> {
    #[cfg(target_os = "windows")]
    {
        let output = Command::new("powershell")
            .args([
                "-NoProfile",
                "-Command",
                "(Get-NetRoute -DestinationPrefix '0.0.0.0/0' | Sort-Object RouteMetric | Select-Object -First 1).NextHop",
            ])
            .output()
            .ok()?;
        let gw = String::from_utf8_lossy(&output.stdout).trim().to_string();
        if gw.is_empty() || gw == "0.0.0.0" {
            return None;
        }
        return Some(gw);
    }

    #[cfg(target_os = "linux")]
    {
        let output = Command::new("sh")
            .arg("-c")
            .arg("ip route | awk '/default/ {print $3; exit}'")
            .output()
            .ok()?;
        let gw = String::from_utf8_lossy(&output.stdout).trim().to_string();
        return if gw.is_empty() { None } else { Some(gw) };
    }

    #[cfg(target_os = "macos")]
    {
        let output = Command::new("sh")
            .arg("-c")
            .arg("route -n get default 2>/dev/null | awk '/gateway:/ {print $2; exit}'")
            .output()
            .ok()?;
        let gw = String::from_utf8_lossy(&output.stdout).trim().to_string();
        return if gw.is_empty() { None } else { Some(gw) };
    }

    #[cfg(not(any(target_os = "windows", target_os = "linux", target_os = "macos")))]
    None
}

fn check_ping(name: &str, target: Option<&str>, fail_detail: &str) -> ConnectivityCheck {
    let Some(host) = target.filter(|h| !h.is_empty()) else {
        return ConnectivityCheck {
            name: name.to_string(),
            status: CheckStatus::Skipped.as_str().into(),
            detail: fail_detail.to_string(),
        };
    };

    let output = {
        let mut cmd = Command::new("ping");
        if cfg!(target_os = "windows") {
            cmd.args(["-n", "2", host]);
        } else {
            cmd.args(["-c", "2", "-W", "2", host]);
        }
        cmd.output()
    };

    match output {
        Ok(out) if out.status.success() => ConnectivityCheck {
            name: name.to_string(),
            status: CheckStatus::Pass.as_str().into(),
            detail: format!("Reachable: {host}"),
        },
        Ok(out) => ConnectivityCheck {
            name: name.to_string(),
            status: CheckStatus::Fail.as_str().into(),
            detail: format!(
                "{fail_detail} (host: {host}){}",
                truncate_stderr(&out.stderr)
            ),
        },
        Err(e) => ConnectivityCheck {
            name: name.to_string(),
            status: CheckStatus::Warn.as_str().into(),
            detail: format!("Ping unavailable: {e}"),
        },
    }
}

fn check_dns_resolution() -> ConnectivityCheck {
    let host = "example.com";
    let resolved = (host, 80).to_socket_addrs();

    match resolved {
        Ok(mut addrs) => {
            if let Some(addr) = addrs.next() {
                ConnectivityCheck {
                    name: "DNS resolution".into(),
                    status: CheckStatus::Pass.as_str().into(),
                    detail: format!("Resolved {host} → {addr}"),
                }
            } else {
                ConnectivityCheck {
                    name: "DNS resolution".into(),
                    status: CheckStatus::Fail.as_str().into(),
                    detail: format!("No addresses returned for {host}"),
                }
            }
        }
        Err(e) => ConnectivityCheck {
            name: "DNS resolution".into(),
            status: CheckStatus::Fail.as_str().into(),
            detail: format!("Could not resolve {host}: {e}"),
        },
    }
}

fn evaluate_playbook(
    checks: &[ConnectivityCheck],
    adapter: &ConnectivityCheck,
    gateway: &ConnectivityCheck,
    dns: &ConnectivityCheck,
    cloudflare: &ConnectivityCheck,
    google_dns: &ConnectivityCheck,
) -> (Vec<String>, String, String) {
    let mut actions = Vec::new();
    let mut push = |id: &str| {
        if !actions.iter().any(|a| a == id) {
            actions.push(id.to_string());
        }
    };

    let adapter_fail = adapter.status == "fail";
    let gateway_fail = gateway.status == "fail";
    let gateway_skip = gateway.status == "skipped";
    let dns_fail = dns.status == "fail";
    let internet_fail = cloudflare.status == "fail" && google_dns.status == "fail";
    let internet_ok = cloudflare.status == "pass" || google_dns.status == "pass";

    let summary = if adapter_fail {
        push("connectivity-suite");
        "Your network adapter appears offline. Enable Wi-Fi or plug in Ethernet, then run diagnostics again."
    } else if gateway_fail || gateway_skip {
        push("connectivity-suite");
        push("network-diagnostics");
        "Your device cannot reach the local router/gateway. Restart your modem and router, then reconnect to Wi-Fi."
    } else if internet_fail {
        push("connectivity-suite");
        push("network-diagnostics");
        "The gateway responds but the internet does not. This often indicates ISP outage, captive portal, or VPN interference. Try another network (mobile hotspot) to compare."
    } else if dns_fail && internet_ok {
        push("dns-flush");
        push("connectivity-suite");
        "Internet reachability looks OK but DNS resolution failed. Flushing the DNS cache is the next step."
    } else if internet_ok && dns.status == "pass" {
        push("connectivity-suite");
        "Core connectivity checks passed. If websites still fail, check VPN, firewall, proxy, or browser extensions."
    } else {
        push("connectivity-suite");
        push("network-diagnostics");
        "Connectivity is degraded. Review each check below and apply the recommended actions."
    };

    let overall = if adapter_fail || gateway_fail || internet_fail {
        "offline"
    } else if dns_fail {
        "degraded"
    } else {
        "healthy"
    };

    let _ = checks;
    (actions, summary.to_string(), overall.to_string())
}

pub fn format_report_text(report: &ConnectivityReport) -> String {
    let mut lines = vec![
        format!("Overall status: {}", report.overall_status),
        String::new(),
        "Checks:".to_string(),
    ];
    for check in &report.checks {
        let icon = match check.status.as_str() {
            "pass" => "✓",
            "fail" => "✗",
            "warn" => "!",
            _ => "–",
        };
        lines.push(format!("  {icon} {} — {}", check.name, check.detail));
    }
    lines.push(String::new());
    lines.push(format!("Assessment: {}", report.playbook_summary));
    if !report.recommended_actions.is_empty() {
        lines.push(format!(
            "Recommended next steps: {}",
            report.recommended_actions.join(", ")
        ));
    }
    lines.join("\n")
}

fn truncate_stderr(stderr: &[u8]) -> String {
    let text = String::from_utf8_lossy(stderr).trim().to_string();
    if text.is_empty() {
        return String::new();
    }
    if text.len() > 120 {
        format!(" — {}", &text[..120])
    } else {
        format!(" — {text}")
    }
}

#[tauri::command]
pub fn run_connectivity_diagnostics(
    state: State<AppState>,
    user_message: Option<String>,
    session_id: Option<String>,
) -> Result<ConnectivityReport, String> {
    let report = run_connectivity_suite();
    let db = state.lock_db()?;
    let record = ConnectivityDiagnosticRecord {
        id: Uuid::new_v4().to_string(),
        session_id,
        user_message,
        overall_status: report.overall_status.clone(),
        playbook_summary: report.playbook_summary.clone(),
        results_json: serde_json::to_string(&report.checks).map_err(|e| e.to_string())?,
        recommended_actions_json: serde_json::to_string(&report.recommended_actions)
            .map_err(|e| e.to_string())?,
        created_at: Utc::now().to_rfc3339(),
    };
    db.save_connectivity_diagnostic(&record)
        .map_err(|e| e.to_string())?;
    Ok(report)
}

#[tauri::command]
pub fn list_connectivity_diagnostics(
    state: State<AppState>,
    limit: Option<i64>,
) -> Result<Vec<ConnectivityDiagnosticRecord>, String> {
    let db = state.lock_db()?;
    db.list_connectivity_diagnostics(limit.unwrap_or(20))
        .map_err(|e| e.to_string())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn detects_connectivity_keywords() {
        assert!(is_connectivity_issue("My wifi is not working"));
        assert!(is_connectivity_issue("No internet connection"));
        assert!(!is_connectivity_issue("printer jam"));
    }

    #[test]
    fn playbook_recommends_dns_flush_when_dns_fails() {
        let adapter = ConnectivityCheck {
            name: "adapter".into(),
            status: "pass".into(),
            detail: String::new(),
        };
        let gateway = ConnectivityCheck {
            name: "gw".into(),
            status: "pass".into(),
            detail: String::new(),
        };
        let dns = ConnectivityCheck {
            name: "dns".into(),
            status: "fail".into(),
            detail: String::new(),
        };
        let cf = ConnectivityCheck {
            name: "cf".into(),
            status: "pass".into(),
            detail: String::new(),
        };
        let g = ConnectivityCheck {
            name: "g".into(),
            status: "pass".into(),
            detail: String::new(),
        };
        let (actions, summary, status) = evaluate_playbook(&[], &adapter, &gateway, &dns, &cf, &g);
        assert!(actions.contains(&"dns-flush".to_string()));
        assert!(summary.contains("DNS"));
        assert_eq!(status, "degraded");
    }

    #[test]
    fn suite_produces_checks() {
        let report = run_connectivity_suite();
        assert!(!report.checks.is_empty());
        assert!(!report.playbook_summary.is_empty());
        assert!(report.offline_capable);
    }
}
