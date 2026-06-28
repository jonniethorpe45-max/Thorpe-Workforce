use crate::net;
use serde::Deserialize;

const DEFAULT_RELEASES_API: &str =
    "https://api.github.com/repos/jonniethorpe45-max/Thorpe-Workforce/releases/latest";

#[derive(Debug, Deserialize)]
struct GithubRelease {
    tag_name: String,
    html_url: String,
    body: Option<String>,
    draft: Option<bool>,
    prerelease: Option<bool>,
}

#[derive(Debug, Clone, serde::Serialize)]
pub struct UpdateInfo {
    pub current_version: String,
    pub latest_version: String,
    pub update_available: bool,
    pub release_notes: String,
    pub download_url: String,
}

pub async fn check_for_updates(current_version: &str, api_url: Option<&str>) -> Result<UpdateInfo, String> {
    let url = api_url.unwrap_or(DEFAULT_RELEASES_API);
    net::validate_https_url(url, false)?;

    let client = reqwest::Client::builder()
        .user_agent("Thorpe-Desktop")
        .timeout(std::time::Duration::from_secs(15))
        .build()
        .map_err(|e| e.to_string())?;

    let response = client
        .get(url)
        .header("Accept", "application/vnd.github+json")
        .send()
        .await
        .map_err(|e| format!("Update check failed: {e}"))?;

    if !response.status().is_success() {
        return Ok(fallback_up_to_date(current_version));
    }

    let release: GithubRelease = response.json().await.map_err(|e| e.to_string())?;

    if release.draft.unwrap_or(false) || release.prerelease.unwrap_or(false) {
        return Ok(fallback_up_to_date(current_version));
    }

    let latest = release.tag_name.trim_start_matches('v').to_string();
    let update_available = version_gt(&latest, current_version);

    Ok(UpdateInfo {
        current_version: current_version.to_string(),
        latest_version: latest,
        update_available,
        release_notes: if update_available {
            release
                .body
                .filter(|b| !b.trim().is_empty())
                .unwrap_or_else(|| format!("Thorpe {} is available.", release.tag_name))
        } else {
            "You are running the latest version of Thorpe.".to_string()
        },
        download_url: release.html_url,
    })
}

fn fallback_up_to_date(current: &str) -> UpdateInfo {
    UpdateInfo {
        current_version: current.to_string(),
        latest_version: current.to_string(),
        update_available: false,
        release_notes: "You are running the latest version of Thorpe.".to_string(),
        download_url: "https://github.com/jonniethorpe45-max/Thorpe-Workforce/releases/latest".to_string(),
    }
}

fn parse_version(version: &str) -> Option<(u32, u32, u32)> {
    let version = version.trim().trim_start_matches('v');
    let mut parts = version.split('.');
    let major = parts.next()?.parse().ok()?;
    let minor = parts.next()?.parse().ok()?;
    let patch = parts.next()?.parse().ok()?;
    Some((major, minor, patch))
}

fn version_gt(latest: &str, current: &str) -> bool {
    match (parse_version(latest), parse_version(current)) {
        (Some(l), Some(c)) => l > c,
        _ => false,
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn compares_semver() {
        assert!(version_gt("1.2.0", "1.1.0"));
        assert!(version_gt("1.1.1", "1.1.0"));
        assert!(!version_gt("1.1.0", "1.1.0"));
        assert!(!version_gt("1.0.9", "1.1.0"));
    }
}
