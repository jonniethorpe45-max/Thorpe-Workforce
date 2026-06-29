use chrono::Utc;
use rusqlite::{params, Connection};
use serde::{Deserialize, Serialize};
use std::path::Path;
use uuid::Uuid;

#[derive(Debug, thiserror::Error)]
pub enum DbError {
    #[error("Database error: {0}")]
    Sqlite(#[from] rusqlite::Error),
    #[error("Not found: {0}")]
    NotFound(String),
}

pub type DbResult<T> = Result<T, DbError>;

pub struct Database {
    conn: Connection,
}

impl Database {
    pub(crate) fn conn(&self) -> &Connection {
        &self.conn
    }

    pub fn new(path: &Path) -> DbResult<Self> {
        let conn = Connection::open(path)?;
        conn.execute_batch("PRAGMA foreign_keys = ON; PRAGMA journal_mode = WAL;")?;
        let db = Self { conn };
        db.migrate()?;
        db.seed_knowledge_base()?;
        db.seed_connectivity_kb()?;
        Ok(db)
    }

    fn migrate(&self) -> DbResult<()> {
        self.conn.execute_batch(
            r#"
            CREATE TABLE IF NOT EXISTS profiles (
                id TEXT PRIMARY KEY,
                display_name TEXT NOT NULL DEFAULT 'User',
                email TEXT,
                skill_level TEXT NOT NULL DEFAULT 'beginner',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS devices (
                id TEXT PRIMARY KEY,
                profile_id TEXT NOT NULL,
                hostname TEXT NOT NULL,
                os_name TEXT NOT NULL,
                os_version TEXT NOT NULL,
                last_seen_at TEXT NOT NULL,
                FOREIGN KEY (profile_id) REFERENCES profiles(id)
            );

            CREATE TABLE IF NOT EXISTS scan_history (
                id TEXT PRIMARY KEY,
                device_id TEXT,
                scan_data TEXT NOT NULL,
                health_score INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS diagnostic_reports (
                id TEXT PRIMARY KEY,
                scan_id TEXT,
                title TEXT NOT NULL,
                summary TEXT NOT NULL,
                findings TEXT NOT NULL,
                recommendations TEXT NOT NULL,
                health_score INTEGER NOT NULL,
                risk_level TEXT NOT NULL DEFAULT 'low',
                technician_notes TEXT,
                plain_language TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (scan_id) REFERENCES scan_history(id)
            );

            CREATE TABLE IF NOT EXISTS technician_notes (
                id TEXT PRIMARY KEY,
                case_id TEXT,
                report_id TEXT,
                author TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS repair_history (
                id TEXT PRIMARY KEY,
                action_id TEXT NOT NULL,
                action_name TEXT NOT NULL,
                status TEXT NOT NULL,
                details TEXT,
                risk_level TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS knowledge_base (
                id TEXT PRIMARY KEY,
                category TEXT NOT NULL,
                title TEXT NOT NULL,
                symptoms TEXT NOT NULL,
                causes TEXT NOT NULL,
                fixes TEXT NOT NULL,
                prevention TEXT NOT NULL,
                when_to_escalate TEXT NOT NULL,
                tags TEXT NOT NULL DEFAULT '[]',
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS licensing (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                tier TEXT NOT NULL DEFAULT 'free',
                license_key TEXT,
                activated_at TEXT,
                expires_at TEXT,
                organization TEXT
            );

            CREATE TABLE IF NOT EXISTS clients (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT,
                phone TEXT,
                company TEXT,
                notes TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS cases (
                id TEXT PRIMARY KEY,
                client_id TEXT,
                device_id TEXT,
                title TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'open',
                priority TEXT NOT NULL DEFAULT 'medium',
                description TEXT,
                report_id TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                closed_at TEXT,
                FOREIGN KEY (client_id) REFERENCES clients(id)
            );

            CREATE TABLE IF NOT EXISTS chat_history (
                id TEXT PRIMARY KEY,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS ai_providers (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                provider_type TEXT NOT NULL,
                base_url TEXT NOT NULL,
                enabled INTEGER NOT NULL DEFAULT 1,
                health_status TEXT NOT NULL DEFAULT 'unknown',
                health_message TEXT,
                last_health_check_at TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS ai_agents (
                id TEXT PRIMARY KEY,
                agent_key TEXT NOT NULL UNIQUE,
                name TEXT NOT NULL,
                provider_id TEXT,
                model TEXT NOT NULL,
                enabled INTEGER NOT NULL DEFAULT 1,
                allowed_roles TEXT NOT NULL DEFAULT '["admin","technician","user"]',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (provider_id) REFERENCES ai_providers(id)
            );

            CREATE TABLE IF NOT EXISTS ai_org_policy (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                cloud_ai_enabled INTEGER NOT NULL DEFAULT 1,
                default_provider_id TEXT,
                monthly_budget_usd REAL NOT NULL DEFAULT 100.0,
                monthly_token_limit INTEGER NOT NULL DEFAULT 1000000,
                enforce_budget INTEGER NOT NULL DEFAULT 1,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS ai_usage_log (
                id TEXT PRIMARY KEY,
                agent_key TEXT NOT NULL,
                provider_id TEXT,
                model TEXT NOT NULL,
                prompt_tokens INTEGER NOT NULL DEFAULT 0,
                completion_tokens INTEGER NOT NULL DEFAULT 0,
                total_tokens INTEGER NOT NULL DEFAULT 0,
                estimated_cost_usd REAL NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS ai_audit_log (
                id TEXT PRIMARY KEY,
                action TEXT NOT NULL,
                actor TEXT NOT NULL,
                details TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS ai_provider_role_access (
                provider_id TEXT NOT NULL,
                role TEXT NOT NULL,
                allowed INTEGER NOT NULL DEFAULT 1,
                PRIMARY KEY (provider_id, role),
                FOREIGN KEY (provider_id) REFERENCES ai_providers(id)
            );

            CREATE TABLE IF NOT EXISTS evidence_artifacts (
                id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                source TEXT NOT NULL,
                kind TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                collected_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS agent_sessions (
                id TEXT PRIMARY KEY,
                case_id TEXT,
                message TEXT NOT NULL,
                plan_json TEXT NOT NULL,
                evidence_json TEXT,
                status TEXT NOT NULL DEFAULT 'completed',
                confidence REAL NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS intel_items (
                id TEXT PRIMARY KEY,
                source TEXT NOT NULL,
                category TEXT NOT NULL,
                title TEXT NOT NULL,
                summary TEXT NOT NULL,
                url TEXT,
                severity TEXT NOT NULL DEFAULT 'info',
                published_at TEXT NOT NULL,
                fetched_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS org_playbooks (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                category TEXT NOT NULL,
                content TEXT NOT NULL,
                tags TEXT NOT NULL DEFAULT '[]',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS repair_packs (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                version TEXT NOT NULL,
                description TEXT NOT NULL,
                enabled INTEGER NOT NULL DEFAULT 1,
                builtin INTEGER NOT NULL DEFAULT 0,
                manifest_json TEXT NOT NULL,
                installed_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS repair_pack_policy (
                pack_id TEXT NOT NULL,
                role TEXT NOT NULL,
                auto_run INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY (pack_id, role)
            );

            CREATE TABLE IF NOT EXISTS watchdog_config (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                enabled INTEGER NOT NULL DEFAULT 0,
                interval_minutes INTEGER NOT NULL DEFAULT 60,
                health_threshold INTEGER NOT NULL DEFAULT 70,
                auto_notify INTEGER NOT NULL DEFAULT 1,
                auto_plan INTEGER NOT NULL DEFAULT 1,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS watchdog_events (
                id TEXT PRIMARY KEY,
                event_type TEXT NOT NULL,
                health_score INTEGER NOT NULL,
                message TEXT NOT NULL,
                plan_json TEXT,
                issues_json TEXT,
                acknowledged INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS connectivity_diagnostics (
                id TEXT PRIMARY KEY,
                session_id TEXT,
                user_message TEXT,
                overall_status TEXT NOT NULL,
                playbook_summary TEXT NOT NULL,
                results_json TEXT NOT NULL,
                recommended_actions_json TEXT NOT NULL DEFAULT '[]',
                created_at TEXT NOT NULL
            );

            CREATE VIRTUAL TABLE IF NOT EXISTS knowledge_fts USING fts5(
                article_id UNINDEXED,
                title,
                symptoms,
                causes,
                fixes,
                tags,
                tokenize='porter'
            );
            "#,
        )?;

        self.ensure_column("profiles", "role", "TEXT NOT NULL DEFAULT 'admin'")?;
        self.ensure_column("chat_history", "metadata_json", "TEXT")?;
        self.ensure_column("watchdog_events", "issues_json", "TEXT")?;

        let profile_count: i64 = self
            .conn
            .query_row("SELECT COUNT(*) FROM profiles", [], |r| r.get(0))?;
        if profile_count == 0 {
            let now = Utc::now().to_rfc3339();
            self.conn.execute(
                "INSERT INTO profiles (id, display_name, skill_level, role, created_at, updated_at) VALUES (?1, ?2, ?3, ?4, ?5, ?6)",
                params![Uuid::new_v4().to_string(), "User", "beginner", "admin", now, now],
            )?;
        }

        let policy_count: i64 = self
            .conn
            .query_row("SELECT COUNT(*) FROM ai_org_policy", [], |r| r.get(0))?;
        if policy_count == 0 {
            let now = Utc::now().to_rfc3339();
            self.conn.execute(
                "INSERT INTO ai_org_policy (id, cloud_ai_enabled, monthly_budget_usd, monthly_token_limit, enforce_budget, updated_at) VALUES (1, 1, 100.0, 1000000, 1, ?1)",
                params![now],
            )?;
        }

        let license_count: i64 = self
            .conn
            .query_row("SELECT COUNT(*) FROM licensing", [], |r| r.get(0))?;
        if license_count == 0 {
            self.conn.execute(
                "INSERT INTO licensing (id, tier) VALUES (1, 'free')",
                [],
            )?;
        }

        self.seed_watchdog_config()?;
        self.rebuild_knowledge_fts()?;
        Ok(())
    }

    fn seed_watchdog_config(&self) -> DbResult<()> {
        let count: i64 = self
            .conn
            .query_row("SELECT COUNT(*) FROM watchdog_config", [], |r| r.get(0))?;
        if count == 0 {
            self.conn.execute(
                "INSERT INTO watchdog_config (id, enabled, interval_minutes, health_threshold, auto_notify, auto_plan, updated_at) VALUES (1, 1, 15, 70, 1, 1, ?1)",
                params![Utc::now().to_rfc3339()],
            )?;
        }
        Ok(())
    }

    pub fn rebuild_knowledge_fts(&self) -> DbResult<()> {
        self.conn.execute("DELETE FROM knowledge_fts", [])?;
        let articles = self.list_knowledge(None)?;
        for article in articles {
            self.conn.execute(
                "INSERT INTO knowledge_fts (article_id, title, symptoms, causes, fixes, tags) VALUES (?1, ?2, ?3, ?4, ?5, ?6)",
                params![article.id, article.title, article.symptoms, article.causes, article.fixes, article.tags],
            )?;
        }
        Ok(())
    }

    fn ensure_column(&self, table: &str, column: &str, definition: &str) -> DbResult<()> {
        let mut stmt = self.conn.prepare(&format!("PRAGMA table_info({table})"))?;
        let mut rows = stmt.query([])?;
        let mut exists = false;
        while let Some(row) = rows.next()? {
            let name: String = row.get(1)?;
            if name == column {
                exists = true;
                break;
            }
        }
        if !exists {
            self.conn
                .execute(&format!("ALTER TABLE {table} ADD COLUMN {column} {definition}"), [])?;
        }
        Ok(())
    }

    fn seed_knowledge_base(&self) -> DbResult<()> {
        let count: i64 = self
            .conn
            .query_row("SELECT COUNT(*) FROM knowledge_base", [], |r| r.get(0))?;
        if count > 0 {
            return Ok(());
        }

        let articles = knowledge_seed::articles();
        for article in articles {
            self.conn.execute(
                "INSERT INTO knowledge_base (id, category, title, symptoms, causes, fixes, prevention, when_to_escalate, tags, created_at) VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8, ?9, ?10)",
                params![
                    article.id,
                    article.category,
                    article.title,
                    article.symptoms,
                    article.causes,
                    article.fixes,
                    article.prevention,
                    article.when_to_escalate,
                    article.tags,
                    Utc::now().to_rfc3339(),
                ],
            )?;
        }
        Ok(())
    }

    fn seed_connectivity_kb(&self) -> DbResult<()> {
        let articles = connectivity_kb_seed::articles();
        for article in articles {
            self.conn.execute(
                "INSERT OR IGNORE INTO knowledge_base (id, category, title, symptoms, causes, fixes, prevention, when_to_escalate, tags, created_at) VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8, ?9, ?10)",
                params![
                    article.id,
                    article.category,
                    article.title,
                    article.symptoms,
                    article.causes,
                    article.fixes,
                    article.prevention,
                    article.when_to_escalate,
                    article.tags,
                    Utc::now().to_rfc3339(),
                ],
            )?;
        }
        Ok(())
    }

    pub fn get_setting(&self, key: &str) -> DbResult<Option<String>> {
        let result = self.conn.query_row(
            "SELECT value FROM settings WHERE key = ?1",
            params![key],
            |row| row.get(0),
        );
        match result {
            Ok(v) => Ok(Some(v)),
            Err(rusqlite::Error::QueryReturnedNoRows) => Ok(None),
            Err(e) => Err(e.into()),
        }
    }

    pub fn set_setting(&self, key: &str, value: &str) -> DbResult<()> {
        self.conn.execute(
            "INSERT INTO settings (key, value) VALUES (?1, ?2) ON CONFLICT(key) DO UPDATE SET value = ?2",
            params![key, value],
        )?;
        Ok(())
    }

    pub fn delete_setting(&self, key: &str) -> DbResult<()> {
        self.conn
            .execute("DELETE FROM settings WHERE key = ?1", params![key])?;
        Ok(())
    }

    pub fn get_all_settings(&self) -> DbResult<Vec<(String, String)>> {
        let mut stmt = self.conn.prepare("SELECT key, value FROM settings")?;
        let rows = stmt.query_map([], |row| Ok((row.get(0)?, row.get(1)?)))?;
        rows.collect::<Result<Vec<_>, _>>().map_err(Into::into)
    }

    pub fn save_scan(&self, scan_data: &str, health_score: i32) -> DbResult<String> {
        let id = Uuid::new_v4().to_string();
        self.conn.execute(
            "INSERT INTO scan_history (id, scan_data, health_score, created_at) VALUES (?1, ?2, ?3, ?4)",
            params![id, scan_data, health_score, Utc::now().to_rfc3339()],
        )?;
        Ok(id)
    }

    pub fn get_scan(&self, id: &str) -> DbResult<ScanRecord> {
        self.conn
            .query_row(
                "SELECT id, scan_data, health_score, created_at FROM scan_history WHERE id = ?1",
                params![id],
                |row| {
                    Ok(ScanRecord {
                        id: row.get(0)?,
                        scan_data: row.get(1)?,
                        health_score: row.get(2)?,
                        created_at: row.get(3)?,
                    })
                },
            )
            .map_err(|_| DbError::NotFound(id.to_string()))
    }

    pub fn list_scans(&self, limit: i64) -> DbResult<Vec<ScanRecord>> {
        let mut stmt = self
            .conn
            .prepare("SELECT id, scan_data, health_score, created_at FROM scan_history ORDER BY created_at DESC LIMIT ?1")?;
        let rows = stmt.query_map(params![limit], |row| {
            Ok(ScanRecord {
                id: row.get(0)?,
                scan_data: row.get(1)?,
                health_score: row.get(2)?,
                created_at: row.get(3)?,
            })
        })?;
        rows.collect::<Result<Vec<_>, _>>().map_err(Into::into)
    }

    pub fn save_report(&self, report: &DiagnosticReport) -> DbResult<()> {
        self.conn.execute(
            "INSERT INTO diagnostic_reports (id, scan_id, title, summary, findings, recommendations, health_score, risk_level, technician_notes, plain_language, created_at) VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8, ?9, ?10, ?11)",
            params![
                report.id,
                report.scan_id,
                report.title,
                report.summary,
                report.findings,
                report.recommendations,
                report.health_score,
                report.risk_level,
                report.technician_notes,
                report.plain_language,
                report.created_at,
            ],
        )?;
        Ok(())
    }

    pub fn list_reports(&self, limit: i64) -> DbResult<Vec<DiagnosticReport>> {
        let mut stmt = self.conn.prepare(
            "SELECT id, scan_id, title, summary, findings, recommendations, health_score, risk_level, technician_notes, plain_language, created_at FROM diagnostic_reports ORDER BY created_at DESC LIMIT ?1"
        )?;
        let rows = stmt.query_map(params![limit], |row| {
            Ok(DiagnosticReport {
                id: row.get(0)?,
                scan_id: row.get(1)?,
                title: row.get(2)?,
                summary: row.get(3)?,
                findings: row.get(4)?,
                recommendations: row.get(5)?,
                health_score: row.get(6)?,
                risk_level: row.get(7)?,
                technician_notes: row.get(8)?,
                plain_language: row.get(9)?,
                created_at: row.get(10)?,
            })
        })?;
        rows.collect::<Result<Vec<_>, _>>().map_err(Into::into)
    }

    pub fn count_reports(&self) -> DbResult<i64> {
        self.conn
            .query_row("SELECT COUNT(*) FROM diagnostic_reports", [], |row| row.get(0))
            .map_err(Into::into)
    }

    pub fn get_report(&self, id: &str) -> DbResult<DiagnosticReport> {
        self.conn
            .query_row(
                "SELECT id, scan_id, title, summary, findings, recommendations, health_score, risk_level, technician_notes, plain_language, created_at FROM diagnostic_reports WHERE id = ?1",
                params![id],
                |row| {
                    Ok(DiagnosticReport {
                        id: row.get(0)?,
                        scan_id: row.get(1)?,
                        title: row.get(2)?,
                        summary: row.get(3)?,
                        findings: row.get(4)?,
                        recommendations: row.get(5)?,
                        health_score: row.get(6)?,
                        risk_level: row.get(7)?,
                        technician_notes: row.get(8)?,
                        plain_language: row.get(9)?,
                        created_at: row.get(10)?,
                    })
                },
            )
            .map_err(|_| DbError::NotFound(id.to_string()))
    }

    pub fn delete_report(&self, id: &str) -> DbResult<()> {
        self.conn.execute(
            "DELETE FROM diagnostic_reports WHERE id = ?1",
            params![id],
        )?;
        Ok(())
    }

    pub fn search_reports(&self, query: &str) -> DbResult<Vec<DiagnosticReport>> {
        let pattern = format!("%{}%", query);
        let mut stmt = self.conn.prepare(
            "SELECT id, scan_id, title, summary, findings, recommendations, health_score, risk_level, technician_notes, plain_language, created_at FROM diagnostic_reports WHERE title LIKE ?1 OR summary LIKE ?1 OR plain_language LIKE ?1 ORDER BY created_at DESC LIMIT 50"
        )?;
        let rows = stmt.query_map(params![pattern], |row| {
            Ok(DiagnosticReport {
                id: row.get(0)?,
                scan_id: row.get(1)?,
                title: row.get(2)?,
                summary: row.get(3)?,
                findings: row.get(4)?,
                recommendations: row.get(5)?,
                health_score: row.get(6)?,
                risk_level: row.get(7)?,
                technician_notes: row.get(8)?,
                plain_language: row.get(9)?,
                created_at: row.get(10)?,
            })
        })?;
        rows.collect::<Result<Vec<_>, _>>().map_err(Into::into)
    }

    pub fn save_repair(&self, record: &RepairRecord) -> DbResult<()> {
        self.conn.execute(
            "INSERT INTO repair_history (id, action_id, action_name, status, details, risk_level, created_at) VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7)",
            params![
                record.id,
                record.action_id,
                record.action_name,
                record.status,
                record.details,
                record.risk_level,
                record.created_at,
            ],
        )?;
        Ok(())
    }

    pub fn list_repairs(&self, limit: i64) -> DbResult<Vec<RepairRecord>> {
        let mut stmt = self.conn.prepare(
            "SELECT id, action_id, action_name, status, details, risk_level, created_at FROM repair_history ORDER BY created_at DESC LIMIT ?1"
        )?;
        let rows = stmt.query_map(params![limit], |row| {
            Ok(RepairRecord {
                id: row.get(0)?,
                action_id: row.get(1)?,
                action_name: row.get(2)?,
                status: row.get(3)?,
                details: row.get(4)?,
                risk_level: row.get(5)?,
                created_at: row.get(6)?,
            })
        })?;
        rows.collect::<Result<Vec<_>, _>>().map_err(Into::into)
    }

    pub fn save_connectivity_diagnostic(&self, record: &ConnectivityDiagnosticRecord) -> DbResult<()> {
        self.conn.execute(
            "INSERT INTO connectivity_diagnostics (id, session_id, user_message, overall_status, playbook_summary, results_json, recommended_actions_json, created_at) VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8)",
            params![
                record.id,
                record.session_id,
                record.user_message,
                record.overall_status,
                record.playbook_summary,
                record.results_json,
                record.recommended_actions_json,
                record.created_at,
            ],
        )?;
        Ok(())
    }

    pub fn list_connectivity_diagnostics(&self, limit: i64) -> DbResult<Vec<ConnectivityDiagnosticRecord>> {
        let mut stmt = self.conn.prepare(
            "SELECT id, session_id, user_message, overall_status, playbook_summary, results_json, recommended_actions_json, created_at FROM connectivity_diagnostics ORDER BY created_at DESC LIMIT ?1",
        )?;
        let rows = stmt.query_map(params![limit], |row| {
            Ok(ConnectivityDiagnosticRecord {
                id: row.get(0)?,
                session_id: row.get(1)?,
                user_message: row.get(2)?,
                overall_status: row.get(3)?,
                playbook_summary: row.get(4)?,
                results_json: row.get(5)?,
                recommended_actions_json: row.get(6)?,
                created_at: row.get(7)?,
            })
        })?;
        rows.collect::<Result<Vec<_>, _>>().map_err(Into::into)
    }

    pub fn list_knowledge(&self, category: Option<&str>) -> DbResult<Vec<KnowledgeArticle>> {
        let mut articles = Vec::new();
        if let Some(cat) = category {
            let mut stmt = self.conn.prepare(
                "SELECT id, category, title, symptoms, causes, fixes, prevention, when_to_escalate, tags, created_at FROM knowledge_base WHERE category = ?1 ORDER BY title"
            )?;
            let rows = stmt.query_map(params![cat], map_knowledge_row)?;
            for row in rows {
                articles.push(row?);
            }
        } else {
            let mut stmt = self.conn.prepare(
                "SELECT id, category, title, symptoms, causes, fixes, prevention, when_to_escalate, tags, created_at FROM knowledge_base ORDER BY category, title"
            )?;
            let rows = stmt.query_map([], map_knowledge_row)?;
            for row in rows {
                articles.push(row?);
            }
        }
        Ok(articles)
    }

    pub fn get_knowledge(&self, id: &str) -> DbResult<KnowledgeArticle> {
        self.conn
            .query_row(
                "SELECT id, category, title, symptoms, causes, fixes, prevention, when_to_escalate, tags, created_at FROM knowledge_base WHERE id = ?1",
                params![id],
                map_knowledge_row,
            )
            .map_err(|_| DbError::NotFound(id.to_string()))
    }

    pub fn get_profile(&self) -> DbResult<Profile> {
        self.conn.query_row(
            "SELECT id, display_name, email, skill_level, role, created_at, updated_at FROM profiles LIMIT 1",
            [],
            |row| {
                Ok(Profile {
                    id: row.get(0)?,
                    display_name: row.get(1)?,
                    email: row.get(2)?,
                    skill_level: row.get(3)?,
                    role: row.get(4)?,
                    created_at: row.get(5)?,
                    updated_at: row.get(6)?,
                })
            },
        ).map_err(Into::into)
    }

    pub fn update_profile_role(&self, role: &str) -> DbResult<Profile> {
        let profile = self.get_profile()?;
        let now = Utc::now().to_rfc3339();
        self.conn.execute(
            "UPDATE profiles SET role = ?1, updated_at = ?2 WHERE id = ?3",
            params![role, now, profile.id],
        )?;
        self.get_profile()
    }

    pub fn update_profile(&self, display_name: &str, email: Option<&str>, skill_level: &str) -> DbResult<Profile> {
        let profile = self.get_profile()?;
        let now = Utc::now().to_rfc3339();
        self.conn.execute(
            "UPDATE profiles SET display_name = ?1, email = ?2, skill_level = ?3, updated_at = ?4 WHERE id = ?5",
            params![display_name, email, skill_level, now, profile.id],
        )?;
        self.get_profile()
    }

    pub fn get_license(&self) -> DbResult<LicenseRecord> {
        self.conn.query_row(
            "SELECT tier, license_key, activated_at, expires_at, organization FROM licensing WHERE id = 1",
            [],
            |row| {
                Ok(LicenseRecord {
                    tier: row.get(0)?,
                    license_key: row.get(1)?,
                    activated_at: row.get(2)?,
                    expires_at: row.get(3)?,
                    organization: row.get(4)?,
                })
            },
        ).map_err(Into::into)
    }

    pub fn activate_license(
        &self,
        key: &str,
        tier: &str,
        organization: Option<&str>,
        expires_at: Option<&str>,
    ) -> DbResult<LicenseRecord> {
        let now = Utc::now().to_rfc3339();
        self.conn.execute(
            "UPDATE licensing SET tier = ?1, license_key = ?2, activated_at = ?3, organization = ?4, expires_at = ?5 WHERE id = 1",
            params![tier, key, now, organization, expires_at],
        )?;
        self.get_license()
    }

    pub fn list_clients(&self) -> DbResult<Vec<Client>> {
        let mut stmt = self.conn.prepare(
            "SELECT id, name, email, phone, company, notes, created_at, updated_at FROM clients ORDER BY name"
        )?;
        let rows = stmt.query_map([], |row| {
            Ok(Client {
                id: row.get(0)?,
                name: row.get(1)?,
                email: row.get(2)?,
                phone: row.get(3)?,
                company: row.get(4)?,
                notes: row.get(5)?,
                created_at: row.get(6)?,
                updated_at: row.get(7)?,
            })
        })?;
        rows.collect::<Result<Vec<_>, _>>().map_err(Into::into)
    }

    pub fn create_client(&self, client: &CreateClient) -> DbResult<Client> {
        let id = Uuid::new_v4().to_string();
        let now = Utc::now().to_rfc3339();
        self.conn.execute(
            "INSERT INTO clients (id, name, email, phone, company, notes, created_at, updated_at) VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8)",
            params![id, client.name, client.email, client.phone, client.company, client.notes, now, now],
        )?;
        Ok(Client {
            id,
            name: client.name.clone(),
            email: client.email.clone(),
            phone: client.phone.clone(),
            company: client.company.clone(),
            notes: client.notes.clone(),
            created_at: now.clone(),
            updated_at: now,
        })
    }

    pub fn update_client(&self, id: &str, client: &CreateClient) -> DbResult<Client> {
        let now = Utc::now().to_rfc3339();
        self.conn.execute(
            "UPDATE clients SET name = ?1, email = ?2, phone = ?3, company = ?4, notes = ?5, updated_at = ?6 WHERE id = ?7",
            params![client.name, client.email, client.phone, client.company, client.notes, now, id],
        )?;
        self.conn.query_row(
            "SELECT id, name, email, phone, company, notes, created_at, updated_at FROM clients WHERE id = ?1",
            params![id],
            |row| {
                Ok(Client {
                    id: row.get(0)?,
                    name: row.get(1)?,
                    email: row.get(2)?,
                    phone: row.get(3)?,
                    company: row.get(4)?,
                    notes: row.get(5)?,
                    created_at: row.get(6)?,
                    updated_at: row.get(7)?,
                })
            },
        ).map_err(Into::into)
    }

    pub fn list_cases(&self) -> DbResult<Vec<SupportCase>> {
        let mut stmt = self.conn.prepare(
            "SELECT id, client_id, device_id, title, status, priority, description, report_id, created_at, updated_at, closed_at FROM cases ORDER BY updated_at DESC"
        )?;
        let rows = stmt.query_map([], |row| {
            Ok(SupportCase {
                id: row.get(0)?,
                client_id: row.get(1)?,
                device_id: row.get(2)?,
                title: row.get(3)?,
                status: row.get(4)?,
                priority: row.get(5)?,
                description: row.get(6)?,
                report_id: row.get(7)?,
                created_at: row.get(8)?,
                updated_at: row.get(9)?,
                closed_at: row.get(10)?,
            })
        })?;
        rows.collect::<Result<Vec<_>, _>>().map_err(Into::into)
    }

    pub fn create_case(&self, case: &CreateCase) -> DbResult<SupportCase> {
        let id = Uuid::new_v4().to_string();
        let now = Utc::now().to_rfc3339();
        self.conn.execute(
            "INSERT INTO cases (id, client_id, device_id, title, status, priority, description, report_id, created_at, updated_at) VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8, ?9, ?10)",
            params![id, case.client_id, case.device_id, case.title, case.status, case.priority, case.description, case.report_id, now, now],
        )?;
        Ok(SupportCase {
            id,
            client_id: case.client_id.clone(),
            device_id: case.device_id.clone(),
            title: case.title.clone(),
            status: case.status.clone(),
            priority: case.priority.clone(),
            description: case.description.clone(),
            report_id: case.report_id.clone(),
            created_at: now.clone(),
            updated_at: now,
            closed_at: None,
        })
    }

    pub fn update_case(&self, id: &str, case: &UpdateCase) -> DbResult<SupportCase> {
        let now = Utc::now().to_rfc3339();
        let closed_at = if case.status == "closed" { Some(now.clone()) } else { None };
        self.conn.execute(
            "UPDATE cases SET title = ?1, status = ?2, priority = ?3, description = ?4, updated_at = ?5, closed_at = COALESCE(?6, closed_at) WHERE id = ?7",
            params![case.title, case.status, case.priority, case.description, now, closed_at, id],
        )?;
        self.conn.query_row(
            "SELECT id, client_id, device_id, title, status, priority, description, report_id, created_at, updated_at, closed_at FROM cases WHERE id = ?1",
            params![id],
            |row| {
                Ok(SupportCase {
                    id: row.get(0)?,
                    client_id: row.get(1)?,
                    device_id: row.get(2)?,
                    title: row.get(3)?,
                    status: row.get(4)?,
                    priority: row.get(5)?,
                    description: row.get(6)?,
                    report_id: row.get(7)?,
                    created_at: row.get(8)?,
                    updated_at: row.get(9)?,
                    closed_at: row.get(10)?,
                })
            },
        ).map_err(Into::into)
    }

    pub fn add_note(&self, note: &CreateNote) -> DbResult<TechnicianNote> {
        let id = Uuid::new_v4().to_string();
        let now = Utc::now().to_rfc3339();
        self.conn.execute(
            "INSERT INTO technician_notes (id, case_id, report_id, author, content, created_at) VALUES (?1, ?2, ?3, ?4, ?5, ?6)",
            params![id, note.case_id, note.report_id, note.author, note.content, now],
        )?;
        Ok(TechnicianNote {
            id,
            case_id: note.case_id.clone(),
            report_id: note.report_id.clone(),
            author: note.author.clone(),
            content: note.content.clone(),
            created_at: now,
        })
    }

    pub fn list_notes(&self, case_id: Option<&str>, report_id: Option<&str>) -> DbResult<Vec<TechnicianNote>> {
        let mut notes = Vec::new();
        if let Some(cid) = case_id {
            let mut stmt = self.conn.prepare(
                "SELECT id, case_id, report_id, author, content, created_at FROM technician_notes WHERE case_id = ?1 ORDER BY created_at DESC"
            )?;
            let rows = stmt.query_map(params![cid], map_note_row)?;
            for row in rows { notes.push(row?); }
        } else if let Some(rid) = report_id {
            let mut stmt = self.conn.prepare(
                "SELECT id, case_id, report_id, author, content, created_at FROM technician_notes WHERE report_id = ?1 ORDER BY created_at DESC"
            )?;
            let rows = stmt.query_map(params![rid], map_note_row)?;
            for row in rows { notes.push(row?); }
        } else {
            let mut stmt = self.conn.prepare(
                "SELECT id, case_id, report_id, author, content, created_at FROM technician_notes ORDER BY created_at DESC LIMIT 100"
            )?;
            let rows = stmt.query_map([], map_note_row)?;
            for row in rows { notes.push(row?); }
        }
        Ok(notes)
    }

    pub fn save_chat(&self, role: &str, content: &str, metadata_json: Option<&str>) -> DbResult<()> {
        self.conn.execute(
            "INSERT INTO chat_history (id, role, content, metadata_json, created_at) VALUES (?1, ?2, ?3, ?4, ?5)",
            params![
                Uuid::new_v4().to_string(),
                role,
                content,
                metadata_json,
                Utc::now().to_rfc3339()
            ],
        )?;
        Ok(())
    }

    pub fn search_knowledge_for_message(&self, message: &str, limit: i64) -> DbResult<Vec<KnowledgeArticle>> {
        let fts_query: String = message
            .split(|c: char| !c.is_alphanumeric())
            .filter(|t| t.len() >= 3)
            .collect::<Vec<_>>()
            .join(" OR ");

        if !fts_query.is_empty() {
            let mut stmt = self.conn.prepare(
                "SELECT article_id FROM knowledge_fts WHERE knowledge_fts MATCH ?1 ORDER BY rank LIMIT ?2",
            )?;
            let ids: Vec<String> = stmt
                .query_map(params![fts_query, limit], |row| row.get(0))?
                .filter_map(|r| r.ok())
                .collect();
            if !ids.is_empty() {
                let mut articles = Vec::new();
                for id in ids {
                    if let Ok(article) = self.get_knowledge(&id) {
                        articles.push(article);
                    }
                }
                if !articles.is_empty() {
                    return Ok(articles);
                }
            }
        }

        let articles = self.list_knowledge(None)?;
        let msg = message.to_lowercase();
        let terms: Vec<String> = msg
            .split(|c: char| !c.is_alphanumeric())
            .filter(|t| t.len() >= 4)
            .map(|t| t.to_string())
            .collect();

        let mut matches: Vec<(i32, KnowledgeArticle)> = articles
            .into_iter()
            .filter_map(|article| {
                let haystack = format!(
                    "{} {} {} {}",
                    article.title, article.symptoms, article.tags, article.category
                )
                .to_lowercase();
                let score = terms.iter().filter(|t| haystack.contains(t.as_str())).count() as i32;
                if score > 0 {
                    Some((score, article))
                } else {
                    None
                }
            })
            .collect();
        matches.sort_by(|a, b| b.0.cmp(&a.0));
        Ok(matches.into_iter().take(limit as usize).map(|(_, a)| a).collect())
    }

    pub fn save_evidence(&self, session_id: &str, source: &str, kind: &str, payload_json: &str) -> DbResult<String> {
        let id = Uuid::new_v4().to_string();
        self.conn.execute(
            "INSERT INTO evidence_artifacts (id, session_id, source, kind, payload_json, collected_at) VALUES (?1, ?2, ?3, ?4, ?5, ?6)",
            params![id, session_id, source, kind, payload_json, Utc::now().to_rfc3339()],
        )?;
        Ok(id)
    }

    pub fn list_evidence_for_session(&self, session_id: &str) -> DbResult<Vec<EvidenceArtifact>> {
        let mut stmt = self.conn.prepare(
            "SELECT id, session_id, source, kind, payload_json, collected_at FROM evidence_artifacts WHERE session_id = ?1 ORDER BY collected_at",
        )?;
        let rows = stmt.query_map(params![session_id], |row| {
            Ok(EvidenceArtifact {
                id: row.get(0)?,
                session_id: row.get(1)?,
                source: row.get(2)?,
                kind: row.get(3)?,
                payload_json: row.get(4)?,
                collected_at: row.get(5)?,
            })
        })?;
        rows.collect::<Result<Vec<_>, _>>().map_err(Into::into)
    }

    pub fn save_agent_session(&self, session: &AgentSessionRecord) -> DbResult<()> {
        self.conn.execute(
            "INSERT INTO agent_sessions (id, case_id, message, plan_json, evidence_json, status, confidence, created_at) VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8)",
            params![
                session.id,
                session.case_id,
                session.message,
                session.plan_json,
                session.evidence_json,
                session.status,
                session.confidence,
                session.created_at
            ],
        )?;
        Ok(())
    }

    pub fn list_agent_sessions(&self, limit: i64) -> DbResult<Vec<AgentSessionRecord>> {
        let mut stmt = self.conn.prepare(
            "SELECT id, case_id, message, plan_json, evidence_json, status, confidence, created_at FROM agent_sessions ORDER BY created_at DESC LIMIT ?1",
        )?;
        let rows = stmt.query_map(params![limit], |row| {
            Ok(AgentSessionRecord {
                id: row.get(0)?,
                case_id: row.get(1)?,
                message: row.get(2)?,
                plan_json: row.get(3)?,
                evidence_json: row.get(4)?,
                status: row.get(5)?,
                confidence: row.get(6)?,
                created_at: row.get(7)?,
            })
        })?;
        rows.collect::<Result<Vec<_>, _>>().map_err(Into::into)
    }

    pub fn upsert_intel_item(&self, item: &IntelItem) -> DbResult<()> {
        self.conn.execute(
            "INSERT OR REPLACE INTO intel_items (id, source, category, title, summary, url, severity, published_at, fetched_at) VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8, ?9)",
            params![
                item.id, item.source, item.category, item.title, item.summary,
                item.url, item.severity, item.published_at, item.fetched_at
            ],
        )?;
        Ok(())
    }

    pub fn list_intel_items(&self, limit: i64) -> DbResult<Vec<IntelItem>> {
        let mut stmt = self.conn.prepare(
            "SELECT id, source, category, title, summary, url, severity, published_at, fetched_at FROM intel_items ORDER BY published_at DESC LIMIT ?1",
        )?;
        let rows = stmt.query_map(params![limit], |row| {
            Ok(IntelItem {
                id: row.get(0)?,
                source: row.get(1)?,
                category: row.get(2)?,
                title: row.get(3)?,
                summary: row.get(4)?,
                url: row.get(5)?,
                severity: row.get(6)?,
                published_at: row.get(7)?,
                fetched_at: row.get(8)?,
            })
        })?;
        rows.collect::<Result<Vec<_>, _>>().map_err(Into::into)
    }

    pub fn search_intel_for_message(&self, message: &str, limit: i64) -> DbResult<Vec<IntelItem>> {
        let msg = message.to_lowercase();
        let items = self.list_intel_items(100)?;
        Ok(items
            .into_iter()
            .filter(|i| {
                let hay = format!("{} {} {}", i.title, i.summary, i.category).to_lowercase();
                msg.split_whitespace().any(|w| w.len() >= 4 && hay.contains(w))
            })
            .take(limit as usize)
            .collect())
    }

    pub fn save_org_playbook(&self, playbook: &OrgPlaybook) -> DbResult<()> {
        self.conn.execute(
            "INSERT OR REPLACE INTO org_playbooks (id, title, category, content, tags, created_at, updated_at) VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7)",
            params![
                playbook.id, playbook.title, playbook.category, playbook.content,
                playbook.tags, playbook.created_at, playbook.updated_at
            ],
        )?;
        self.rebuild_knowledge_fts_from_playbooks()?;
        Ok(())
    }

    fn rebuild_knowledge_fts_from_playbooks(&self) -> DbResult<()> {
        let playbooks = self.list_org_playbooks()?;
        for pb in playbooks {
            self.conn.execute(
                "INSERT INTO knowledge_fts (article_id, title, symptoms, causes, fixes, tags) VALUES (?1, ?2, ?3, ?4, ?5, ?6)",
                params![
                    format!("playbook-{}", pb.id),
                    pb.title,
                    pb.content.chars().take(500).collect::<String>(),
                    pb.category,
                    "",
                    pb.tags
                ],
            )?;
        }
        Ok(())
    }

    pub fn list_org_playbooks(&self) -> DbResult<Vec<OrgPlaybook>> {
        let mut stmt = self.conn.prepare(
            "SELECT id, title, category, content, tags, created_at, updated_at FROM org_playbooks ORDER BY updated_at DESC",
        )?;
        let rows = stmt.query_map([], |row| {
            Ok(OrgPlaybook {
                id: row.get(0)?,
                title: row.get(1)?,
                category: row.get(2)?,
                content: row.get(3)?,
                tags: row.get(4)?,
                created_at: row.get(5)?,
                updated_at: row.get(6)?,
            })
        })?;
        rows.collect::<Result<Vec<_>, _>>().map_err(Into::into)
    }

    pub fn upsert_repair_pack(&self, pack: &RepairPackRecord) -> DbResult<()> {
        self.conn.execute(
            "INSERT OR REPLACE INTO repair_packs (id, name, version, description, enabled, builtin, manifest_json, installed_at) VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8)",
            params![
                pack.id, pack.name, pack.version, pack.description,
                pack.enabled as i64, pack.builtin as i64, pack.manifest_json, pack.installed_at
            ],
        )?;
        Ok(())
    }

    pub fn list_repair_packs(&self) -> DbResult<Vec<RepairPackRecord>> {
        let mut stmt = self.conn.prepare(
            "SELECT id, name, version, description, enabled, builtin, manifest_json, installed_at FROM repair_packs ORDER BY name",
        )?;
        let rows = stmt.query_map([], |row| {
            Ok(RepairPackRecord {
                id: row.get(0)?,
                name: row.get(1)?,
                version: row.get(2)?,
                description: row.get(3)?,
                enabled: row.get::<_, i64>(4)? == 1,
                builtin: row.get::<_, i64>(5)? == 1,
                manifest_json: row.get(6)?,
                installed_at: row.get(7)?,
            })
        })?;
        rows.collect::<Result<Vec<_>, _>>().map_err(Into::into)
    }

    pub fn get_watchdog_config(&self) -> DbResult<WatchdogConfig> {
        self.conn.query_row(
            "SELECT enabled, interval_minutes, health_threshold, auto_notify, auto_plan, updated_at FROM watchdog_config WHERE id = 1",
            [],
            |row| {
                Ok(WatchdogConfig {
                    enabled: row.get::<_, i64>(0)? == 1,
                    interval_minutes: row.get(1)?,
                    health_threshold: row.get(2)?,
                    auto_notify: row.get::<_, i64>(3)? == 1,
                    auto_plan: row.get::<_, i64>(4)? == 1,
                    updated_at: row.get(5)?,
                })
            },
        ).map_err(Into::into)
    }

    pub fn update_watchdog_config(&self, config: &WatchdogConfig) -> DbResult<WatchdogConfig> {
        let now = Utc::now().to_rfc3339();
        self.conn.execute(
            "UPDATE watchdog_config SET enabled = ?1, interval_minutes = ?2, health_threshold = ?3, auto_notify = ?4, auto_plan = ?5, updated_at = ?6 WHERE id = 1",
            params![
                config.enabled as i64,
                config.interval_minutes,
                config.health_threshold,
                config.auto_notify as i64,
                config.auto_plan as i64,
                now
            ],
        )?;
        self.get_watchdog_config()
    }

    pub fn save_watchdog_event(&self, event: &WatchdogEvent) -> DbResult<()> {
        self.conn.execute(
            "INSERT INTO watchdog_events (id, event_type, health_score, message, plan_json, issues_json, acknowledged, created_at) VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8)",
            params![
                event.id, event.event_type, event.health_score, event.message,
                event.plan_json, event.issues_json, event.acknowledged as i64, event.created_at
            ],
        )?;
        Ok(())
    }

    pub fn list_watchdog_events(&self, limit: i64) -> DbResult<Vec<WatchdogEvent>> {
        let mut stmt = self.conn.prepare(
            "SELECT id, event_type, health_score, message, plan_json, issues_json, acknowledged, created_at FROM watchdog_events ORDER BY created_at DESC LIMIT ?1",
        )?;
        let rows = stmt.query_map(params![limit], |row| {
            Ok(WatchdogEvent {
                id: row.get(0)?,
                event_type: row.get(1)?,
                health_score: row.get(2)?,
                message: row.get(3)?,
                plan_json: row.get(4)?,
                issues_json: row.get(5)?,
                acknowledged: row.get::<_, i64>(6)? == 1,
                created_at: row.get(7)?,
            })
        })?;
        rows.collect::<Result<Vec<_>, _>>().map_err(Into::into)
    }

    pub fn get_chat_history(&self, limit: i64) -> DbResult<Vec<ChatMessage>> {
        let mut stmt = self.conn.prepare(
            "SELECT id, role, content, metadata_json, created_at FROM chat_history ORDER BY created_at ASC LIMIT ?1"
        )?;
        let rows = stmt.query_map(params![limit], |row| {
            Ok(ChatMessage {
                id: row.get(0)?,
                role: row.get(1)?,
                content: row.get(2)?,
                metadata_json: row.get(3)?,
                created_at: row.get(4)?,
            })
        })?;
        rows.collect::<Result<Vec<_>, _>>().map_err(Into::into)
    }

    pub fn has_recent_unacked_watchdog_event_of_type(
        &self,
        event_type: &str,
        within_minutes: i64,
    ) -> DbResult<bool> {
        let cutoff = (Utc::now() - chrono::Duration::minutes(within_minutes)).to_rfc3339();
        let count: i64 = self.conn.query_row(
            "SELECT COUNT(*) FROM watchdog_events WHERE acknowledged = 0 AND event_type = ?1 AND created_at > ?2",
            params![event_type, cutoff],
            |r| r.get(0),
        )?;
        Ok(count > 0)
    }

    pub fn has_recent_unacked_watchdog_event(&self, within_minutes: i64) -> DbResult<bool> {
        let cutoff = (Utc::now() - chrono::Duration::minutes(within_minutes)).to_rfc3339();
        let count: i64 = self.conn.query_row(
            "SELECT COUNT(*) FROM watchdog_events WHERE acknowledged = 0 AND created_at > ?1",
            params![cutoff],
            |r| r.get(0),
        )?;
        Ok(count > 0)
    }

    pub fn delete_all_user_data(&self) -> DbResult<()> {
        self.conn.execute_batch(
            "DELETE FROM chat_history;
             DELETE FROM technician_notes;
             DELETE FROM cases;
             DELETE FROM clients;
             DELETE FROM repair_history;
             DELETE FROM diagnostic_reports;
             DELETE FROM scan_history;
             DELETE FROM evidence_artifacts;
             DELETE FROM agent_sessions;
             DELETE FROM watchdog_events;
             DELETE FROM settings;"
        )?;
        Ok(())
    }
}

fn map_knowledge_row(row: &rusqlite::Row) -> rusqlite::Result<KnowledgeArticle> {
    Ok(KnowledgeArticle {
        id: row.get(0)?,
        category: row.get(1)?,
        title: row.get(2)?,
        symptoms: row.get(3)?,
        causes: row.get(4)?,
        fixes: row.get(5)?,
        prevention: row.get(6)?,
        when_to_escalate: row.get(7)?,
        tags: row.get(8)?,
        created_at: row.get(9)?,
    })
}

fn map_note_row(row: &rusqlite::Row) -> rusqlite::Result<TechnicianNote> {
    Ok(TechnicianNote {
        id: row.get(0)?,
        case_id: row.get(1)?,
        report_id: row.get(2)?,
        author: row.get(3)?,
        content: row.get(4)?,
        created_at: row.get(5)?,
    })
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct EvidenceArtifact {
    pub id: String,
    pub session_id: String,
    pub source: String,
    pub kind: String,
    pub payload_json: String,
    pub collected_at: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AgentSessionRecord {
    pub id: String,
    pub case_id: Option<String>,
    pub message: String,
    pub plan_json: String,
    pub evidence_json: Option<String>,
    pub status: String,
    pub confidence: f64,
    pub created_at: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct IntelItem {
    pub id: String,
    pub source: String,
    pub category: String,
    pub title: String,
    pub summary: String,
    pub url: Option<String>,
    pub severity: String,
    pub published_at: String,
    pub fetched_at: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct OrgPlaybook {
    pub id: String,
    pub title: String,
    pub category: String,
    pub content: String,
    pub tags: String,
    pub created_at: String,
    pub updated_at: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RepairPackRecord {
    pub id: String,
    pub name: String,
    pub version: String,
    pub description: String,
    pub enabled: bool,
    pub builtin: bool,
    pub manifest_json: String,
    pub installed_at: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct WatchdogConfig {
    pub enabled: bool,
    pub interval_minutes: i64,
    pub health_threshold: i32,
    pub auto_notify: bool,
    pub auto_plan: bool,
    pub updated_at: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct WatchdogEvent {
    pub id: String,
    pub event_type: String,
    pub health_score: i32,
    pub message: String,
    pub plan_json: Option<String>,
    pub issues_json: Option<String>,
    pub acknowledged: bool,
    pub created_at: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ScanRecord {
    pub id: String,
    pub scan_data: String,
    pub health_score: i32,
    pub created_at: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DiagnosticReport {
    pub id: String,
    pub scan_id: Option<String>,
    pub title: String,
    pub summary: String,
    pub findings: String,
    pub recommendations: String,
    pub health_score: i32,
    pub risk_level: String,
    pub technician_notes: Option<String>,
    pub plain_language: String,
    pub created_at: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RepairRecord {
    pub id: String,
    pub action_id: String,
    pub action_name: String,
    pub status: String,
    pub details: Option<String>,
    pub risk_level: String,
    pub created_at: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ConnectivityDiagnosticRecord {
    pub id: String,
    pub session_id: Option<String>,
    pub user_message: Option<String>,
    pub overall_status: String,
    pub playbook_summary: String,
    pub results_json: String,
    pub recommended_actions_json: String,
    pub created_at: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct KnowledgeArticle {
    pub id: String,
    pub category: String,
    pub title: String,
    pub symptoms: String,
    pub causes: String,
    pub fixes: String,
    pub prevention: String,
    pub when_to_escalate: String,
    pub tags: String,
    pub created_at: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Profile {
    pub id: String,
    pub display_name: String,
    pub email: Option<String>,
    pub skill_level: String,
    pub role: String,
    pub created_at: String,
    pub updated_at: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LicenseRecord {
    pub tier: String,
    pub license_key: Option<String>,
    pub activated_at: Option<String>,
    pub expires_at: Option<String>,
    pub organization: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Client {
    pub id: String,
    pub name: String,
    pub email: Option<String>,
    pub phone: Option<String>,
    pub company: Option<String>,
    pub notes: Option<String>,
    pub created_at: String,
    pub updated_at: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CreateClient {
    pub name: String,
    pub email: Option<String>,
    pub phone: Option<String>,
    pub company: Option<String>,
    pub notes: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SupportCase {
    pub id: String,
    pub client_id: Option<String>,
    pub device_id: Option<String>,
    pub title: String,
    pub status: String,
    pub priority: String,
    pub description: Option<String>,
    pub report_id: Option<String>,
    pub created_at: String,
    pub updated_at: String,
    pub closed_at: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CreateCase {
    pub client_id: Option<String>,
    pub device_id: Option<String>,
    pub title: String,
    pub status: String,
    pub priority: String,
    pub description: Option<String>,
    pub report_id: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct UpdateCase {
    pub title: String,
    pub status: String,
    pub priority: String,
    pub description: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TechnicianNote {
    pub id: String,
    pub case_id: Option<String>,
    pub report_id: Option<String>,
    pub author: String,
    pub content: String,
    pub created_at: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CreateNote {
    pub case_id: Option<String>,
    pub report_id: Option<String>,
    pub author: String,
    pub content: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ChatMessage {
    pub id: String,
    pub role: String,
    pub content: String,
    pub metadata_json: Option<String>,
    pub created_at: String,
}

pub mod commands {
    use super::*;
    use crate::secrets;
    use crate::AppState;
    use tauri::State;

    const SENSITIVE_SETTINGS: &[&str] = &["ai_api_key"];

    fn redact_settings(settings: Vec<(String, String)>) -> Vec<(String, String)> {
        settings
            .into_iter()
            .filter(|(key, _)| !SENSITIVE_SETTINGS.contains(&key.as_str()))
            .collect()
    }

    #[tauri::command]
    pub fn get_settings(state: State<AppState>) -> Result<Vec<(String, String)>, String> {
        let settings = state.lock_db()?.get_all_settings().map_err(|e| e.to_string())?;
        Ok(redact_settings(settings))
    }

    #[tauri::command]
    pub fn update_settings(state: State<AppState>, key: String, value: String) -> Result<(), String> {
        if SENSITIVE_SETTINGS.contains(&key.as_str()) {
            return Err("This setting must be updated through AI Settings.".to_string());
        }
        state.lock_db()?.set_setting(&key, &value).map_err(|e| e.to_string())
    }

    #[tauri::command]
    pub fn list_reports(state: State<AppState>, limit: Option<i64>) -> Result<Vec<DiagnosticReport>, String> {
        state.lock_db()?.list_reports(limit.unwrap_or(50)).map_err(|e| e.to_string())
    }

    #[tauri::command]
    pub fn get_report(state: State<AppState>, id: String) -> Result<DiagnosticReport, String> {
        state.lock_db()?.get_report(&id).map_err(|e| e.to_string())
    }

    #[tauri::command]
    pub fn delete_report(state: State<AppState>, id: String) -> Result<(), String> {
        state.lock_db()?.delete_report(&id).map_err(|e| e.to_string())
    }

    #[tauri::command]
    pub fn search_reports(state: State<AppState>, query: String) -> Result<Vec<DiagnosticReport>, String> {
        state.lock_db()?.search_reports(&query).map_err(|e| e.to_string())
    }

    #[tauri::command]
    pub fn list_knowledge_articles(state: State<AppState>, category: Option<String>) -> Result<Vec<KnowledgeArticle>, String> {
        state.lock_db()?.list_knowledge(category.as_deref()).map_err(|e| e.to_string())
    }

    #[tauri::command]
    pub fn get_knowledge_article(state: State<AppState>, id: String) -> Result<KnowledgeArticle, String> {
        state.lock_db()?.get_knowledge(&id).map_err(|e| e.to_string())
    }

    #[tauri::command]
    pub fn get_profile(state: State<AppState>) -> Result<Profile, String> {
        state.lock_db()?.get_profile().map_err(|e| e.to_string())
    }

    #[tauri::command]
    pub fn update_profile(
        state: State<AppState>,
        display_name: String,
        email: Option<String>,
        skill_level: String,
        role: Option<String>,
    ) -> Result<Profile, String> {
        let _ = role;
        let db = state.lock_db()?;
        db.update_profile(&display_name, email.as_deref(), &skill_level)
            .map_err(|e| e.to_string())?;
        db.get_profile().map_err(|e| e.to_string())
    }

    #[tauri::command]
    pub fn get_chat_history(state: State<AppState>, limit: Option<i64>) -> Result<Vec<ChatMessage>, String> {
        state
            .lock_db()?
            .get_chat_history(limit.unwrap_or(100))
            .map_err(|e| e.to_string())
    }

    #[tauri::command]
    pub fn delete_all_user_data(state: State<AppState>) -> Result<(), String> {
        state.lock_db()?.delete_all_user_data().map_err(|e| e.to_string())?;
        secrets::delete_api_key(&state.data_dir)?;
        Ok(())
    }

    #[tauri::command]
    pub fn list_clients(state: State<AppState>) -> Result<Vec<Client>, String> {
        let db = state.lock_db()?;
        crate::licensing::require_feature(&db, "technician_workspace")?;
        db.list_clients().map_err(|e| e.to_string())
    }

    #[tauri::command]
    pub fn create_client(state: State<AppState>, client: CreateClient) -> Result<Client, String> {
        let db = state.lock_db()?;
        crate::licensing::require_feature(&db, "technician_workspace")?;
        db.create_client(&client).map_err(|e| e.to_string())
    }

    #[tauri::command]
    pub fn update_client(state: State<AppState>, id: String, client: CreateClient) -> Result<Client, String> {
        let db = state.lock_db()?;
        crate::licensing::require_feature(&db, "technician_workspace")?;
        db.update_client(&id, &client).map_err(|e| e.to_string())
    }

    #[tauri::command]
    pub fn list_cases(state: State<AppState>) -> Result<Vec<SupportCase>, String> {
        let db = state.lock_db()?;
        crate::licensing::require_feature(&db, "technician_workspace")?;
        db.list_cases().map_err(|e| e.to_string())
    }

    #[tauri::command]
    pub fn create_case(state: State<AppState>, case: CreateCase) -> Result<SupportCase, String> {
        let db = state.lock_db()?;
        crate::licensing::require_feature(&db, "technician_workspace")?;
        let created = db.create_case(&case).map_err(|e| e.to_string())?;
        crate::integrations::psa::spawn_case_event(&state, "case.created", created.clone());
        Ok(created)
    }

    #[tauri::command]
    pub fn update_case(state: State<AppState>, id: String, case: UpdateCase) -> Result<SupportCase, String> {
        let db = state.lock_db()?;
        crate::licensing::require_feature(&db, "technician_workspace")?;
        let updated = db.update_case(&id, &case).map_err(|e| e.to_string())?;
        crate::integrations::psa::spawn_case_event(&state, "case.updated", updated.clone());
        Ok(updated)
    }

    #[tauri::command]
    pub fn add_technician_note(state: State<AppState>, note: CreateNote) -> Result<TechnicianNote, String> {
        let db = state.lock_db()?;
        crate::licensing::require_feature(&db, "technician_workspace")?;
        db.add_note(&note).map_err(|e| e.to_string())
    }

    #[tauri::command]
    pub fn list_technician_notes(state: State<AppState>, case_id: Option<String>, report_id: Option<String>) -> Result<Vec<TechnicianNote>, String> {
        let db = state.lock_db()?;
        crate::licensing::require_feature(&db, "technician_workspace")?;
        db.list_notes(case_id.as_deref(), report_id.as_deref()).map_err(|e| e.to_string())
    }
}

mod knowledge_seed {
    pub struct SeedArticle {
        pub id: &'static str,
        pub category: &'static str,
        pub title: &'static str,
        pub symptoms: &'static str,
        pub causes: &'static str,
        pub fixes: &'static str,
        pub prevention: &'static str,
        pub when_to_escalate: &'static str,
        pub tags: &'static str,
    }

    pub fn articles() -> Vec<SeedArticle> {
        vec![
            SeedArticle { id: "kb-windows-slow-boot", category: "Windows", title: "Slow Windows Startup", symptoms: "Computer takes several minutes to boot; desktop appears but apps are unresponsive initially.", causes: "Too many startup programs; failing hard drive; pending Windows updates; corrupted boot configuration.", fixes: "1. Open Task Manager > Startup tab and disable unnecessary programs.\n2. Run Disk Cleanup to remove temporary files.\n3. Check for Windows Updates.\n4. Run `sfc /scannow` in an elevated Command Prompt.\n5. Consider upgrading to an SSD if using a mechanical drive.", prevention: "Keep startup programs minimal; maintain at least 15% free disk space; install updates regularly.", when_to_escalate: "If boot time exceeds 5 minutes after optimization, or you hear clicking sounds from the drive.", tags: "[\"performance\", \"startup\", \"windows\"]" },
            SeedArticle { id: "kb-macos-wifi", category: "macOS", title: "Wi-Fi Connection Drops on macOS", symptoms: "Wi-Fi disconnects randomly; 'No Internet' despite being connected; slow network speeds.", causes: "Outdated macOS; router firmware issues; DNS problems; conflicting network locations; VPN interference.", fixes: "1. Toggle Wi-Fi off and on.\n2. Remove and re-add the Wi-Fi network.\n3. Reset DNS to automatic or use 1.1.1.1 / 8.8.8.8.\n4. Delete network preference files: System Settings > Network.\n5. Reset SMC and NVRAM if issue persists.", prevention: "Keep macOS updated; avoid multiple VPN clients; position router optimally.", when_to_escalate: "If issue occurs on all networks including mobile hotspot, hardware diagnostics may be needed.", tags: "[\"networking\", \"wifi\", \"macos\"]" },
            SeedArticle { id: "kb-linux-disk-full", category: "Linux", title: "Disk Space Full on Linux", symptoms: "'No space left on device' errors; applications fail to save; system becomes sluggish.", causes: "Large log files; unused packages; Docker images; user downloads; core dumps.", fixes: "1. Run `df -h` to identify full partitions.\n2. Use `du -sh /*` to find large directories.\n3. Clean package cache: `sudo apt clean` or `sudo dnf clean all`.\n4. Remove old logs: `sudo journalctl --vacuum-time=7d`.\n5. Find large files: `find / -size +100M 2>/dev/null`.", prevention: "Monitor disk usage regularly; set up log rotation; clean package caches monthly.", when_to_escalate: "If root partition is full and system won't boot, professional recovery may be required.", tags: "[\"storage\", \"linux\", \"performance\"]" },
            SeedArticle { id: "kb-network-dns", category: "Networking", title: "DNS Resolution Failures", symptoms: "Websites won't load but ping to IP addresses works; 'DNS_PROBE_FINISHED_NXDOMAIN' errors.", causes: "Incorrect DNS settings; ISP DNS outage; firewall blocking DNS; corrupted DNS cache; VPN DNS leak.", fixes: "1. Flush DNS cache (platform-specific).\n2. Switch to public DNS (1.1.1.1, 8.8.8.8).\n3. Restart router/modem.\n4. Disable VPN temporarily to test.\n5. Check hosts file for incorrect entries.", prevention: "Use reliable DNS providers; document network settings; keep router firmware updated.", when_to_escalate: "If DNS fails on all devices on the network, contact ISP or network administrator.", tags: "[\"networking\", \"dns\", \"connectivity\"]" },
            SeedArticle { id: "kb-printer-spooler", category: "Printers", title: "Print Jobs Stuck in Queue", symptoms: "Documents stay in print queue; printer shows 'offline'; nothing prints despite being connected.", causes: "Print spooler service crashed; driver corruption; network printer communication failure; paper jam not cleared.", fixes: "1. Cancel all jobs in the print queue.\n2. Restart the print spooler service.\n3. Remove and re-add the printer.\n4. Update or reinstall printer drivers.\n5. Power cycle the printer (off 30 seconds, then on).", prevention: "Keep drivers updated; don't power off printer during print jobs; use wired connection when possible.", when_to_escalate: "If printer hardware shows error codes or physical damage is visible.", tags: "[\"printers\", \"windows\", \"hardware\"]" },
            SeedArticle { id: "kb-vpn-connect", category: "VPNs", title: "VPN Won't Connect", symptoms: "VPN client shows connection timeout; authentication fails; connected but no internet.", causes: "Incorrect credentials; firewall blocking VPN ports; outdated VPN client; split tunneling misconfiguration; ISP blocking VPN.", fixes: "1. Verify credentials (without sharing them with support tools).\n2. Try a different VPN protocol (WireGuard, OpenVPN, IKEv2).\n3. Temporarily disable firewall to test.\n4. Update VPN client to latest version.\n5. Check if VPN works on another network (mobile hotspot).", prevention: "Keep VPN client updated; document working configuration; test after OS updates.", when_to_escalate: "Contact your organization's IT administrator for corporate VPN issues.", tags: "[\"vpn\", \"networking\", \"security\"]" },
            SeedArticle { id: "kb-m365-outlook", category: "Microsoft 365", title: "Outlook Not Syncing", symptoms: "New emails don't appear; calendar events missing; 'Disconnected' status in Outlook.", causes: "Expired credentials; oversized mailbox; corrupted OST/PST file; server-side issues; add-in conflicts.", fixes: "1. Check Microsoft 365 service health page.\n2. Sign out and back into Office account.\n3. Repair Office installation.\n4. Create a new Outlook profile.\n5. Clear cached credentials in Credential Manager.", prevention: "Archive old emails regularly; limit mailbox size; keep Office updated.", when_to_escalate: "If organization-wide outage or admin-level configuration is needed.", tags: "[\"email\", \"microsoft365\", \"outlook\"]" },
            SeedArticle { id: "kb-security-malware", category: "Security", title: "Suspected Malware Infection", symptoms: "Unexpected pop-ups; browser redirects; high CPU from unknown processes; files encrypted with ransom note.", causes: "Phishing emails; malicious downloads; outdated software; disabled security software; USB infections.", fixes: "1. Disconnect from network immediately if ransomware suspected.\n2. Run a full antivirus scan.\n3. Boot into Safe Mode and scan again.\n4. Check startup programs and browser extensions.\n5. Update all software and change passwords from a clean device.", prevention: "Enable automatic updates; use reputable antivirus; never open suspicious attachments; maintain backups.", when_to_escalate: "Immediately for ransomware. Contact cybersecurity professional for business systems.", tags: "[\"security\", \"malware\", \"ransomware\"]" },
            SeedArticle { id: "kb-perf-high-cpu", category: "Performance", title: "High CPU Usage", symptoms: "Fan runs constantly; system is slow; Task Manager shows high CPU from unknown process.", causes: "Background updates; malware; runaway processes; browser with many tabs; indexing services; thermal throttling.", fixes: "1. Identify the process in Task Manager / Activity Monitor.\n2. End non-essential high-CPU tasks.\n3. Disable unnecessary startup programs.\n4. Check for pending updates (may resolve after completion).\n5. Scan for malware if process is suspicious.", prevention: "Monitor startup programs; keep system clean; ensure adequate cooling.", when_to_escalate: "If CPU usage stays at 100% with no identifiable cause after reboot.", tags: "[\"performance\", \"cpu\", \"troubleshooting\"]" },
            SeedArticle { id: "kb-software-crash", category: "Software", title: "Application Keeps Crashing", symptoms: "App closes unexpectedly; error dialogs on launch; app freezes and requires force quit.", causes: "Corrupted preferences; incompatible OS update; insufficient memory; conflicting software; damaged installation.", fixes: "1. Restart the application and computer.\n2. Check for app updates.\n3. Reset app preferences/cache.\n4. Reinstall the application.\n5. Check system requirements and available RAM.", prevention: "Keep apps updated; maintain sufficient free RAM and disk space; backup app data.", when_to_escalate: "If crashes affect critical business software or data loss occurs.", tags: "[\"software\", \"crashes\", \"troubleshooting\"]" },
        ]
    }
}

mod connectivity_kb_seed {
    pub struct SeedArticle {
        pub id: &'static str,
        pub category: &'static str,
        pub title: &'static str,
        pub symptoms: &'static str,
        pub causes: &'static str,
        pub fixes: &'static str,
        pub prevention: &'static str,
        pub when_to_escalate: &'static str,
        pub tags: &'static str,
    }

    pub fn articles() -> Vec<SeedArticle> {
        vec![
            SeedArticle {
                id: "kb-offline-no-internet",
                category: "Networking",
                title: "No Internet Connection (Offline Troubleshooting)",
                symptoms: "Browser shows 'No Internet'; apps cannot sync; Wi-Fi icon shows connected but pages won't load.",
                causes: "Router/modem issue; DNS failure; VPN stuck; adapter disabled; ISP outage; captive portal.",
                fixes: "1. Run Thorpe connectivity diagnostics (Jonathan or Repair Center).\n2. Toggle Wi-Fi off and on.\n3. Restart modem and router (power off 30 seconds).\n4. Flush DNS cache.\n5. Disable VPN temporarily.\n6. Try a mobile hotspot to isolate ISP vs device.",
                prevention: "Document working DNS settings; keep router firmware updated; note VPN requirements.",
                when_to_escalate: "If all devices on the network fail, contact ISP. If only one device fails after all steps, hardware repair may be needed.",
                tags: "[\"networking\", \"offline\", \"connectivity\", \"wifi\"]",
            },
            SeedArticle {
                id: "kb-gateway-unreachable",
                category: "Networking",
                title: "Cannot Reach Router or Gateway",
                symptoms: "Connected to Wi-Fi but no local network access; cannot open router admin page; gateway ping fails.",
                causes: "Wrong network; DHCP failure; router crashed; Ethernet cable loose; airplane mode.",
                fixes: "1. Confirm correct Wi-Fi network (not guest/isolated VLAN).\n2. Reconnect to network and obtain new IP (renew DHCP).\n3. Restart router.\n4. For Ethernet, reseat cable and try another port.\n5. Run connectivity diagnostics in Thorpe.",
                prevention: "Label networks; avoid overlapping guest/main SSIDs without routing.",
                when_to_escalate: "Corporate managed networks — contact network administrator.",
                tags: "[\"networking\", \"gateway\", \"router\", \"offline\"]",
            },
            SeedArticle {
                id: "kb-dns-works-ip-only",
                category: "Networking",
                title: "Internet Works by IP but Not by Website Name",
                symptoms: "Ping to 8.8.8.8 succeeds but websites fail; DNS_PROBE errors in browser.",
                causes: "Corrupted DNS cache; wrong DNS servers; hosts file override; VPN DNS leak.",
                fixes: "1. Flush DNS cache (Thorpe Repair Center or Jonathan).\n2. Set DNS to 1.1.1.1 and 8.8.8.8.\n3. Check hosts file for bad entries.\n4. Disable VPN and retest.",
                prevention: "Use reliable DNS; document custom DNS for work networks.",
                when_to_escalate: "If DNS fails on all networks after flush, malware or policy may block DNS.",
                tags: "[\"dns\", \"networking\", \"offline\", \"connectivity\"]",
            },
        ]
    }
}
