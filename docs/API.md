# Thorpe Tauri Command API

All commands are invoked from the frontend via `@tauri-apps/api/core` `invoke()`.

## Application

| Command | Args | Returns | Description |
|---------|------|---------|-------------|
| `get_app_info` | — | `AppInfo` | Application name, version, platform |
| `check_for_updates` | — | `UpdateInfo` | Check for available updates |
| `run_connectivity_diagnostics` | `user_message?`, `session_id?` | `ConnectivityReport` | Offline layered network diagnostics (adapter, gateway, DNS, internet) |
| `list_connectivity_diagnostics` | `limit?` | `ConnectivityDiagnosticRecord[]` | History of connectivity diagnostic runs |

## Profile & Settings

| Command | Args | Returns | Description |
|---------|------|---------|-------------|
| `get_profile` | — | `Profile` | Get user profile |
| `update_profile` | `displayName`, `email?`, `skillLevel` | `Profile` | Update profile |
| `get_settings` | — | `[key, value][]` | Get all settings |
| `update_settings` | `key`, `value` | — | Set a setting |
| `delete_all_user_data` | — | — | Delete all user data |

## System Scanner

| Command | Args | Returns | Description |
|---------|------|---------|-------------|
| `run_system_scan` | — | `SystemScanResult` | Run full system scan |
| `get_last_scan` | — | `SystemScanResult?` | Get most recent scan |
| `list_scans` | `limit?` | `ScanRecord[]` | List scan history |

## Reports

| Command | Args | Returns | Description |
|---------|------|---------|-------------|
| `generate_diagnostic_report` | `scanId?` | `DiagnosticReport` | Generate AI report |
| `list_reports` | `limit?` | `DiagnosticReport[]` | List reports |
| `get_report` | `id` | `DiagnosticReport` | Get report by ID |
| `delete_report` | `id` | — | Delete a report |
| `search_reports` | `query` | `DiagnosticReport[]` | Search reports |
| `export_report_pdf` | `reportId`, `outputPath` | `string` | Export PDF |

## Repair Center

| Command | Args | Returns | Description |
|---------|------|---------|-------------|
| `list_repair_actions` | — | `RepairAction[]` | List available repairs |
| `execute_repair` | `actionId`, `confirmed` | `RepairResult` | Execute a repair |
| `list_repair_history` | `limit?` | `RepairRecord[]` | List repair log |

## Jonathan AI

| Command | Args | Returns | Description |
|---------|------|---------|-------------|
| `chat_with_jonathan` | `request: ChatRequest` | `ChatResponse` | Send chat message |
| `get_ai_config` | — | `AiConfig` | Get AI configuration |
| `set_ai_config` | `config: AiConfig` | — | Set AI configuration |

## Knowledge Base

| Command | Args | Returns | Description |
|---------|------|---------|-------------|
| `list_knowledge_articles` | `category?` | `KnowledgeArticle[]` | List articles |
| `get_knowledge_article` | `id` | `KnowledgeArticle` | Get article |

## Technician Workspace

| Command | Args | Returns | Description |
|---------|------|---------|-------------|
| `list_clients` | — | `Client[]` | List clients |
| `create_client` | `client` | `Client` | Create client |
| `update_client` | `id`, `client` | `Client` | Update client |
| `list_cases` | — | `SupportCase[]` | List cases |
| `create_case` | `case` | `SupportCase` | Create case |
| `update_case` | `id`, `case` | `SupportCase` | Update case |
| `add_technician_note` | `note` | `TechnicianNote` | Add note |
| `list_technician_notes` | `caseId?`, `reportId?` | `TechnicianNote[]` | List notes |

## Licensing

| Command | Args | Returns | Description |
|---------|------|---------|-------------|
| `get_license_info` | — | `LicenseInfo` | Get license info |
| `activate_license` | `request` | `LicenseInfo` | Activate license |
| `check_feature` | `feature` | `FeatureCheck` | Check feature access |
