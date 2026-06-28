const GENERIC_ACCOUNT_NAMES: &[&str] = &[
    "user",
    "guest",
    "admin",
    "administrator",
    "root",
    "default",
    "test",
    "owner",
    "system",
    "public",
];

/// Read the OS login account name (e.g. `john.smith`, `DOMAIN\john`).
pub fn os_account_name() -> Option<String> {
    let name = std::env::var("USERNAME")
        .or_else(|_| std::env::var("USER"))
        .ok()?;
    let trimmed = name.trim();
    if trimmed.is_empty() {
        None
    } else {
        Some(trimmed.to_string())
    }
}

/// Derive a friendly first name from an OS account or display name token.
pub fn first_name_from_account(account: &str) -> Option<String> {
    let account = account.trim();
    if account.is_empty() {
        return None;
    }

    let local_account = account.rsplit('\\').next().unwrap_or(account);
    let segment = local_account
        .split(['.', '_', '-', ' '])
        .find(|part| !part.trim().is_empty())?
        .trim();

    if segment.is_empty() || is_generic_account_name(segment) {
        return None;
    }

    Some(title_case_word(segment))
}

/// Default profile display name from the logged-in OS user, falling back to `User`.
pub fn default_display_name() -> String {
    os_account_name()
        .and_then(|account| first_name_from_account(&account))
        .unwrap_or_else(|| "User".to_string())
}

pub fn is_generic_account_name(name: &str) -> bool {
    let lower = name.trim().to_lowercase();
    GENERIC_ACCOUNT_NAMES.contains(&lower.as_str())
}

fn title_case_word(word: &str) -> String {
    let mut chars = word.chars();
    let Some(first) = chars.next() else {
        return String::new();
    };
    let rest: String = chars.flat_map(char::to_lowercase).collect();
    format!("{}{}", first.to_uppercase(), rest)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn derives_first_name_from_dotted_account() {
        assert_eq!(
            first_name_from_account("jordan.smith"),
            Some("Jordan".to_string())
        );
    }

    #[test]
    fn derives_first_name_from_domain_account() {
        assert_eq!(
            first_name_from_account("CORP\\Alex"),
            Some("Alex".to_string())
        );
    }

    #[test]
    fn skips_generic_accounts() {
        assert_eq!(first_name_from_account("Administrator"), None);
        assert_eq!(first_name_from_account("user"), None);
    }
}
