use crate::db::{Database, IntelItem};
use chrono::Utc;
use serde::Deserialize;
use uuid::Uuid;

const DEFAULT_FEED_URL: &str =
    "https://raw.githubusercontent.com/jonniethorpe45-max/Thorpe-Workforce/main/intel/feed.json";

#[derive(Debug, Deserialize)]
struct IntelFeedFile {
    items: Vec<IntelFeedItem>,
}

#[derive(Debug, Deserialize)]
struct IntelFeedItem {
    id: String,
    source: String,
    category: String,
    title: String,
    summary: String,
    url: Option<String>,
    severity: Option<String>,
    published_at: String,
}

fn bundled_intel() -> Vec<IntelItem> {
    let now = Utc::now().to_rfc3339();
    vec![
        IntelItem {
            id: "intel-win11-24h2-vpn".into(),
            source: "Thorpe Intel".into(),
            category: "Windows".into(),
            title: "Windows 11 24H2 VPN regression".into(),
            summary: "Some VPN clients fail after 24H2 until adapter power management is disabled.".into(),
            url: Some("https://learn.microsoft.com/windows/release-health/".into()),
            severity: "medium".into(),
            published_at: now.clone(),
            fetched_at: now.clone(),
        },
        IntelItem {
            id: "intel-dns-ipv6".into(),
            source: "Thorpe Intel".into(),
            category: "Networking".into(),
            title: "IPv6 DNS resolution failures".into(),
            summary: "Flush DNS and verify AAAA records when sites load intermittently.".into(),
            url: None,
            severity: "low".into(),
            published_at: now.clone(),
            fetched_at: now.clone(),
        },
        IntelItem {
            id: "intel-macos-sequoia-login".into(),
            source: "Thorpe Intel".into(),
            category: "macOS".into(),
            title: "macOS login item delays".into(),
            summary: "Review Login Items after major macOS upgrades; disable stale agents.".into(),
            url: Some("https://support.apple.com/guide/mac-help/mchlp2896/mac".into()),
            severity: "info".into(),
            published_at: now.clone(),
            fetched_at: now,
        },
    ]
}

pub fn ensure_intel_seeded(db: &Database) -> Result<(), String> {
    let count: i64 = db
        .conn()
        .query_row("SELECT COUNT(*) FROM intel_items", [], |r| r.get(0))
        .map_err(|e| e.to_string())?;
    if count > 0 {
        return Ok(());
    }
    for item in bundled_intel() {
        db.upsert_intel_item(&item).map_err(|e| e.to_string())?;
    }
    Ok(())
}

pub async fn sync_intel_feed(db: &Database, feed_url: Option<&str>) -> Result<i64, String> {
    let url = feed_url.unwrap_or(DEFAULT_FEED_URL).to_string();
    crate::net::validate_https_url(&url, false)?;
    let client = reqwest::Client::builder()
        .timeout(std::time::Duration::from_secs(15))
        .build()
        .map_err(|e| e.to_string())?;

    let feed_result = client.get(&url).send().await;

    let imported = match feed_result {
        Ok(resp) if resp.status().is_success() => {
            let feed: IntelFeedFile = resp.json().await.map_err(|e| e.to_string())?;
            let mut count = 0i64;
            let fetched_at = Utc::now().to_rfc3339();
            for item in feed.items {
                db.upsert_intel_item(&IntelItem {
                    id: item.id,
                    source: item.source,
                    category: item.category,
                    title: item.title,
                    summary: item.summary,
                    url: item.url,
                    severity: item.severity.unwrap_or_else(|| "info".to_string()),
                    published_at: item.published_at,
                    fetched_at: fetched_at.clone(),
                })
                .map_err(|e| e.to_string())?;
                count += 1;
            }
            count
        }
        _ => {
            for item in bundled_intel() {
                db.upsert_intel_item(&item).map_err(|e| e.to_string())?;
            }
            bundled_intel().len() as i64
        }
    };

    Ok(imported)
}

pub fn create_playbook(
    db: &Database,
    title: &str,
    category: &str,
    content: &str,
    tags: &[String],
) -> Result<crate::db::OrgPlaybook, String> {
    let now = Utc::now().to_rfc3339();
    let playbook = crate::db::OrgPlaybook {
        id: Uuid::new_v4().to_string(),
        title: title.to_string(),
        category: category.to_string(),
        content: content.to_string(),
        tags: serde_json::to_string(tags).unwrap_or_else(|_| "[]".to_string()),
        created_at: now.clone(),
        updated_at: now,
    };
    db.save_org_playbook(&playbook).map_err(|e| e.to_string())?;
    Ok(playbook)
}
