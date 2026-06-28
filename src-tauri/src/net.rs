/// Validates outbound HTTPS URLs to reduce SSRF risk for user-configured fetches.
pub fn validate_https_url(url: &str, allow_private_hosts: bool) -> Result<(), String> {
    let parsed = url::Url::parse(url.trim()).map_err(|_| "Invalid URL format.".to_string())?;
    if parsed.scheme() != "https" {
        return Err("Only HTTPS URLs are allowed.".to_string());
    }
    if parsed.host().is_none() {
        return Err("URL must include a host.".to_string());
    }
    if !allow_private_hosts {
        if let Some(host) = parsed.host_str() {
            if is_private_or_loopback_host(host) {
                return Err("Private or loopback hosts are not allowed for this URL.".to_string());
            }
        }
    }
    Ok(())
}

fn is_private_or_loopback_host(host: &str) -> bool {
    let host = host.trim_matches(['[', ']']).to_lowercase();
    if host == "localhost" || host.ends_with(".local") || host == "::1" {
        return true;
    }
    if let Ok(ip) = host.parse::<std::net::IpAddr>() {
        return match ip {
            std::net::IpAddr::V4(v4) => {
                v4.is_loopback()
                    || v4.is_private()
                    || v4.is_link_local()
                    || v4.octets()[0] == 169 && v4.octets()[1] == 254
            }
            std::net::IpAddr::V6(v6) => v6.is_loopback() || v6.is_unique_local(),
        };
    }
    false
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn rejects_http_scheme() {
        assert!(validate_https_url("http://example.com/feed.json", false).is_err());
    }

    #[test]
    fn rejects_localhost_intel_feed() {
        assert!(validate_https_url("https://localhost/feed.json", false).is_err());
    }

    #[test]
    fn allows_public_https() {
        assert!(validate_https_url("https://example.com/feed.json", false).is_ok());
    }
}
