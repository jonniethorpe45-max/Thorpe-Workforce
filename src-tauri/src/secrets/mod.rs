use aes_gcm::{
    aead::{Aead, KeyInit},
    Aes256Gcm, Nonce,
};
use sha2::{Digest, Sha256};
use std::fs;
use std::path::{Path, PathBuf};

const KEYRING_SERVICE: &str = "app.thorpe.desktop";
const KEYRING_USER: &str = "openai_api_key";
const ENCRYPTED_KEY_FILE: &str = ".credentials/openai_key.enc";

pub fn store_api_key(data_dir: &Path, key: &str) -> Result<(), String> {
    if key.trim().is_empty() {
        return delete_api_key(data_dir);
    }

    if let Ok(entry) = keyring::Entry::new(KEYRING_SERVICE, KEYRING_USER) {
        if entry.set_password(key).is_ok() {
            remove_encrypted_fallback(data_dir);
            return Ok(());
        }
    }

    write_encrypted_fallback(data_dir, key)
}

pub fn get_api_key(data_dir: &Path) -> Result<Option<String>, String> {
    if let Ok(entry) = keyring::Entry::new(KEYRING_SERVICE, KEYRING_USER) {
        match entry.get_password() {
            Ok(key) if !key.is_empty() => return Ok(Some(key)),
            Ok(_) => return Ok(None),
            Err(keyring::Error::NoEntry) => {}
            Err(_) => {}
        }
    }

    read_encrypted_fallback(data_dir)
}

pub fn delete_api_key(data_dir: &Path) -> Result<(), String> {
    if let Ok(entry) = keyring::Entry::new(KEYRING_SERVICE, KEYRING_USER) {
        let _ = entry.delete_credential();
    }
    remove_encrypted_fallback(data_dir);
    Ok(())
}

pub fn migrate_api_key_from_db(
    data_dir: &Path,
    legacy_key: Option<String>,
) -> Result<(), String> {
    if let Some(key) = legacy_key {
        if !key.trim().is_empty() {
            store_api_key(data_dir, &key)?;
        }
    }
    Ok(())
}

fn encrypted_key_path(data_dir: &Path) -> PathBuf {
    data_dir.join(ENCRYPTED_KEY_FILE)
}

fn derive_fallback_key(data_dir: &Path) -> [u8; 32] {
    let mut hasher = Sha256::new();
    hasher.update(b"thorpe-credential-v1");
    if let Ok(host) = hostname::get() {
        hasher.update(host.to_string_lossy().as_bytes());
    }
    if let Ok(user) = std::env::var("USER").or_else(|_| std::env::var("USERNAME")) {
        hasher.update(user.as_bytes());
    }
    hasher.update(data_dir.to_string_lossy().as_bytes());
    hasher.finalize().into()
}

fn write_encrypted_fallback(data_dir: &Path, key: &str) -> Result<(), String> {
    let path = encrypted_key_path(data_dir);
    if let Some(parent) = path.parent() {
        fs::create_dir_all(parent).map_err(|e| format!("Failed to create credentials directory: {e}"))?;
    }

    let cipher = Aes256Gcm::new_from_slice(&derive_fallback_key(data_dir))
        .map_err(|e| format!("Failed to initialize credential encryption: {e}"))?;
    let nonce_bytes: [u8; 12] = rand::random();
    let nonce = Nonce::from_slice(&nonce_bytes);
    let ciphertext = cipher
        .encrypt(nonce, key.as_bytes())
        .map_err(|e| format!("Failed to encrypt API key: {e}"))?;

    let mut payload = Vec::with_capacity(12 + ciphertext.len());
    payload.extend_from_slice(&nonce_bytes);
    payload.extend_from_slice(&ciphertext);
    fs::write(&path, payload).map_err(|e| format!("Failed to store encrypted API key: {e}"))?;

    #[cfg(unix)]
    {
        use std::os::unix::fs::PermissionsExt;
        let _ = fs::set_permissions(&path, fs::Permissions::from_mode(0o600));
    }

    Ok(())
}

fn read_encrypted_fallback(data_dir: &Path) -> Result<Option<String>, String> {
    let path = encrypted_key_path(data_dir);
    if !path.exists() {
        return Ok(None);
    }

    let payload = fs::read(&path).map_err(|e| format!("Failed to read encrypted API key: {e}"))?;
    if payload.len() <= 12 {
        return Err("Encrypted API key file is corrupted.".to_string());
    }

    let (nonce_bytes, ciphertext) = payload.split_at(12);
    let cipher = Aes256Gcm::new_from_slice(&derive_fallback_key(data_dir))
        .map_err(|e| format!("Failed to initialize credential decryption: {e}"))?;
    let plaintext = cipher
        .decrypt(Nonce::from_slice(nonce_bytes), ciphertext)
        .map_err(|e| format!("Failed to decrypt API key: {e}"))?;

    String::from_utf8(plaintext).map(Some).map_err(|e| format!("Stored API key is invalid UTF-8: {e}"))
}

fn remove_encrypted_fallback(data_dir: &Path) {
    let path = encrypted_key_path(data_dir);
    let _ = fs::remove_file(path);
}
