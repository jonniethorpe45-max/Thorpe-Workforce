pub mod agent;
pub mod ai;
pub mod db;
pub mod enterprise_ai;
pub mod evidence;
pub mod integrations;
pub mod intel;
pub mod licensing;
pub mod pdf;
pub mod repairs;
pub mod scanner;
pub mod secrets;
pub mod watchdog;

use db::Database;
use std::path::PathBuf;
use std::sync::{Mutex, MutexGuard};
use tauri::Manager;

pub struct AppState {
    pub db: Mutex<Database>,
    pub data_dir: PathBuf,
}

impl AppState {
    pub fn lock_db(&self) -> Result<MutexGuard<'_, Database>, String> {
        self.db
            .lock()
            .map_err(|_| "Database is temporarily unavailable. Please try again.".to_string())
    }
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_dialog::init())
        .plugin(tauri_plugin_fs::init())
        .plugin(tauri_plugin_shell::init())
        .setup(|app| {
            let data_dir = app
                .path()
                .app_data_dir()
                .expect("Failed to resolve app data directory");
            std::fs::create_dir_all(&data_dir).ok();
            let db_path = data_dir.join("thorpe.db");
            let database = Database::new(&db_path).expect("Failed to initialize database");
            if let Ok(Some(legacy_key)) = database.get_setting("ai_api_key") {
                secrets::migrate_api_key_from_db(&data_dir, Some(legacy_key)).ok();
                let _ = database.delete_setting("ai_api_key");
            }
            let _ = intel::ensure_intel_seeded(&database);
            let _ = repairs::ensure_packs_installed(&database);
            app.manage(AppState {
                db: Mutex::new(database),
                data_dir,
            });
            watchdog::start_watchdog(app.handle().clone());
            Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            scanner::run_system_scan,
            scanner::get_last_scan,
            scanner::list_scans,
            repairs::list_repair_actions,
            repairs::execute_repair,
            repairs::list_repair_history,
            ai::chat_with_jonathan,
            ai::generate_diagnostic_report,
            ai::get_ai_config,
            ai::set_ai_config,
            enterprise_ai::get_enterprise_ai_dashboard,
            enterprise_ai::upsert_ai_provider,
            enterprise_ai::rotate_provider_api_key,
            enterprise_ai::upsert_ai_agent,
            enterprise_ai::update_ai_org_policy,
            enterprise_ai::test_ai_provider_health,
            enterprise_ai::list_ai_audit_log,
            agent::list_agent_sessions,
            agent::sync_intel_feed,
            agent::list_intel_items,
            agent::list_repair_packs,
            agent::install_repair_pack,
            agent::upsert_org_playbook,
            agent::list_org_playbooks,
            watchdog::get_watchdog_status,
            watchdog::update_watchdog_config,
            watchdog::acknowledge_watchdog_event,
            integrations::psa::get_psa_settings,
            integrations::psa::update_psa_settings,
            integrations::psa::test_psa_webhook,
            db::commands::get_settings,
            db::commands::update_settings,
            db::commands::list_reports,
            db::commands::get_report,
            db::commands::delete_report,
            db::commands::list_clients,
            db::commands::create_client,
            db::commands::update_client,
            db::commands::list_cases,
            db::commands::create_case,
            db::commands::update_case,
            db::commands::add_technician_note,
            db::commands::list_technician_notes,
            db::commands::search_reports,
            db::commands::list_knowledge_articles,
            db::commands::get_knowledge_article,
            db::commands::get_profile,
            db::commands::update_profile,
            db::commands::get_chat_history,
            db::commands::delete_all_user_data,
            licensing::get_license_info,
            licensing::activate_license,
            licensing::check_feature,
            pdf::export_report_pdf,
            pdf::export_agent_session_pdf,
            get_app_info,
            check_for_updates,
        ])
        .run(tauri::generate_context!())
        .expect("error while running Thorpe");
}

#[derive(serde::Serialize)]
pub struct AppInfo {
    pub name: String,
    pub version: String,
    pub platform: String,
    pub data_dir: String,
}

#[tauri::command]
fn get_app_info(app: tauri::AppHandle) -> Result<AppInfo, String> {
    let data_dir = app
        .path()
        .app_data_dir()
        .map_err(|e| e.to_string())?
        .to_string_lossy()
        .to_string();

    Ok(AppInfo {
        name: "Thorpe".to_string(),
        version: env!("CARGO_PKG_VERSION").to_string(),
        platform: std::env::consts::OS.to_string(),
        data_dir,
    })
}

#[derive(serde::Serialize)]
pub struct UpdateInfo {
    pub current_version: String,
    pub latest_version: String,
    pub update_available: bool,
    pub release_notes: String,
    pub download_url: String,
}

#[tauri::command]
async fn check_for_updates() -> Result<UpdateInfo, String> {
    let current = env!("CARGO_PKG_VERSION").to_string();
    Ok(UpdateInfo {
        current_version: current.clone(),
        latest_version: current,
        update_available: false,
        release_notes: "You are running the latest version of Thorpe.".to_string(),
        download_url: "https://github.com/jonniethorpe45-max/Thorpe-Workforce/releases/latest".to_string(),
    })
}