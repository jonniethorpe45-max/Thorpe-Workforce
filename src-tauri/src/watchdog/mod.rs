use crate::agent::{plan_with_rules, PlannerContext};
use crate::db::WatchdogEvent;
use crate::scanner;
use crate::AppState;
use chrono::Utc;
use serde::{Deserialize, Serialize};
use std::sync::atomic::{AtomicBool, Ordering};
use tauri::{AppHandle, Emitter, Manager};
use uuid::Uuid;

static WATCHDOG_RUNNING: AtomicBool = AtomicBool::new(false);

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
    if scan.health_score >= config.health_threshold {
        return Ok(());
    }

    {
        let db = state.lock_db()?;
        if db
            .has_recent_unacked_watchdog_event(config.interval_minutes.max(5))
            .map_err(|e| e.to_string())?
        {
            return Ok(());
        }
    }

    let plan_json = if config.auto_plan {
        let ctx = PlannerContext {
            message: format!(
                "Proactive watchdog: health score {} below threshold {}",
                scan.health_score, config.health_threshold
            ),
            scan_json: serde_json::to_string(&scan).ok(),
            evidence_json: None,
            kb_excerpts: vec![],
            intel_excerpts: vec![],
            available_tools: vec![
                "disk-analysis".into(),
                "high-resource-id".into(),
                "temp-cleanup".into(),
                "network-diagnostics".into(),
            ],
        };
        let plan = plan_with_rules(&ctx.message, Some(&scan));
        Some(serde_json::to_string(&plan).map_err(|e| e.to_string())?)
    } else {
        None
    };

    let event = WatchdogEvent {
        id: Uuid::new_v4().to_string(),
        event_type: "health_threshold_breach".into(),
        health_score: scan.health_score,
        message: format!(
            "System health dropped to {}/100 (threshold {}).{}",
            scan.health_score,
            config.health_threshold,
            if config.auto_plan {
                " Jonathan prepared a response plan."
            } else {
                ""
            }
        ),
        plan_json,
        acknowledged: false,
        created_at: Utc::now().to_rfc3339(),
    };

    {
        let db = state.lock_db()?;
        db.save_watchdog_event(&event).map_err(|e| e.to_string())?;
    }

    if config.auto_notify {
        let _ = app.emit("watchdog-alert", &event);
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
