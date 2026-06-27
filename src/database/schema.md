# Thorpe SQLite Database Schema

All tables are created automatically on first launch via migrations in `src-tauri/src/db/mod.rs`.

## Tables

### profiles
User profile information.

| Column | Type | Description |
|--------|------|-------------|
| id | TEXT PK | UUID |
| display_name | TEXT | User's display name |
| email | TEXT | Optional email |
| skill_level | TEXT | `beginner` or `advanced` |
| created_at | TEXT | ISO 8601 timestamp |
| updated_at | TEXT | ISO 8601 timestamp |

### devices
Registered devices (for multi-device management).

### scan_history
System scan results stored as JSON.

| Column | Type | Description |
|--------|------|-------------|
| id | TEXT PK | UUID |
| scan_data | TEXT | JSON serialized SystemScanResult |
| health_score | INTEGER | 0-100 |
| created_at | TEXT | ISO 8601 timestamp |

### diagnostic_reports
AI-generated diagnostic reports.

### technician_notes
Notes attached to cases or reports.

### repair_history
Log of all repair actions executed.

### knowledge_base
Troubleshooting articles (seeded on first launch).

### settings
Key-value application settings.

### licensing
License tier and activation info (single row, id=1).

### clients
Client records for technician workspace.

### cases
Support case tracking.

### chat_history
Jonathan conversation history.

## Data Location

- **Windows**: `%APPDATA%\app.thorpe.desktop\`
- **macOS**: `~/Library/Application Support/app.thorpe.desktop/`
- **Linux**: `~/.local/share/app.thorpe.desktop/`
