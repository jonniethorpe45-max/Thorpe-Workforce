use crate::net;
use serde::Deserialize;

const DEFAULT_RELEASES_API: &str =
    "https://api.github.com/repos/jonniethorpe45-max/Thorpe-Workforce/releases/latest";

#[derive(Debug, Deserialize)]
struct GithubAsset {
    name: String,
    browser_download_url: String,
}

#[derive(Debug, Deserialize)]
struct GithubRelease {
    tag_name: String,
    html_url: String,
    body: Option<String>,
    draft: Option<bool>,
    prerelease: Option<bool>,
    assets: Vec<GithubAsset>,
}

#[derive(Debug, Clone, serde::Serialize)]
pub struct UpdateInfo {
    pub current_version: String,
    pub latest_version: String,
    pub update_available: bool,
    pub release_notes: String,
    pub download_url: String,
}

#[derive(Debug, Clone, serde::Serialize)]
pub struct ReleaseDownloads {
    pub release_version: String,
    pub releases_page: String,
    pub windows_exe: Option<String>,
    pub windows_msi: Option<String>,
    pub macos_dmg: Option<String>,
    pub linux_appimage: Option<String>,
    pub linux_deb: Option<String>,
}

async fn fetch_latest_release(api_url: Option<&str>) -> Result<GithubRelease, String> {
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
        .map_err(|e| format!("Release lookup failed: {e}"))?;

    if !response.status().is_success() {
        return Err(format!("Release lookup failed (HTTP {})", response.status()));
    }

    response.json().await.map_err(|e| e.to_string())
}

fn pick_asset(assets: &[GithubAsset], suffix: &str) -> Option<String> {
    assets
        .iter()
        .find(|asset| asset.name.ends_with(suffix))
        .map(|asset| asset.browser_download_url.clone())
}

fn primary_download_url(release: &GithubRelease) -> String {
    let assets = &release.assets;
    let platform_url = {
        #[cfg(all(target_os = "windows", target_arch = "x86_64"))]
        {
            pick_asset(assets, "_x64-setup.exe")
        }
        #[cfg(target_os = "macos")]
        {
            pick_asset(assets, "_aarch64.dmg")
        }
        #[cfg(target_os = "linux")]
        {
            pick_asset(assets, "_amd64.AppImage")
        }
        #[cfg(not(any(
            all(target_os = "windows", target_arch = "x86_64"),
            target_os = "macos",
            target_os = "linux"
        )))]
        {
            None::<String>
        }
    };

    platform_url
        .or_else(|| pick_asset(assets, "_x64-setup.exe"))
        .unwrap_or_else(|| release.html_url.clone())
}

pub async fn get_release_downloads(api_url: Option<&str>) -> Result<ReleaseDownloads, String> {
    let release = fetch_latest_release(api_url).await?;

    if release.draft.unwrap_or(false) || release.prerelease.unwrap_or(false) {
        return Err("Latest release is not publicly available yet.".to_string());
    }

    let version = release.tag_name.trim_start_matches('v').to_string();

    Ok(ReleaseDownloads {
        release_version: version,
        releases_page: release.html_url,
        windows_exe: pick_asset(&release.assets, "_x64-setup.exe"),
        windows_msi: pick_asset(&release.assets, "_x64_en-US.msi"),
        macos_dmg: pick_asset(&release.assets, "_aarch64.dmg"),
        linux_appimage: pick_asset(&release.assets, "_amd64.AppImage"),
        linux_deb: pick_asset(&release.assets, "_amd64.deb"),
    })
}

pub async fn check_for_updates(current_version: &str, api_url: Option<&str>) -> Result<UpdateInfo, String> {
    let release = match fetch_latest_release(api_url).await {
        Ok(release) => release,
        Err(_) => return Ok(fallback_up_to_date(current_version)),
    };

    if release.draft.unwrap_or(false) || release.prerelease.unwrap_or(false) {
        return Ok(fallback_up_to_date(current_version));
    }

    let latest = release.tag_name.trim_start_matches('v').to_string();
    let update_available = version_gt(&latest, current_version);
    let download_url = primary_download_url(&release);
    let tag_name = release.tag_name.clone();
    let release_notes = if update_available {
        release
            .body
            .filter(|b| !b.trim().is_empty())
            .unwrap_or_else(|| format!("Thorpe {tag_name} is available."))
    } else {
        "You are running the latest version of Thorpe.".to_string()
    };

    Ok(UpdateInfo {
        current_version: current_version.to_string(),
        latest_version: latest,
        update_available,
        release_notes,
        download_url,
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
        assert!(version_gt("1.0.8", "1.0.7"));
    }

    #[test]
    fn picks_assets_by_suffix() {
        let assets = vec![
            GithubAsset {
                name: "Thorpe_1.0.8_x64-setup.exe".to_string(),
                browser_download_url: "https://example.com/setup.exe".to_string(),
            },
            GithubAsset {
                name: "Thorpe_1.0.8_amd64.deb".to_string(),
                browser_download_url: "https://example.com/pkg.deb".to_string(),
            },
        ];

        assert_eq!(
            pick_asset(&assets, "_x64-setup.exe").as_deref(),
            Some("https://example.com/setup.exe")
        );
        assert_eq!(
            pick_asset(&assets, "_amd64.deb").as_deref(),
            Some("https://example.com/pkg.deb")
        );
        assert!(pick_asset(&assets, "_missing").is_none());
    }
}
