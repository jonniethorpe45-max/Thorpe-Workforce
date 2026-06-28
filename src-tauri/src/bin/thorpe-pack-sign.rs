use std::env;
use std::fs;
use std::io::{self, Read};
use std::path::PathBuf;

use thorpe_lib::repairs::pack_signing::{
    generate_keypair_hex, sign_manifest_ed25519, signing_key_from_seed_hex,
};
use thorpe_lib::repairs::packs::RepairPackManifest;

fn usage() {
    eprintln!(
        r#"Thorpe repair pack signing tool

USAGE:
  thorpe-pack-sign --gen-keypair [--out-dir <dir>]
  thorpe-pack-sign --manifest <file.json> --key <private.hex> [--output <file.json>]

ENV:
  THORPE_PACK_SIGNING_KEY   Hex-encoded 32-byte Ed25519 seed (alternative to --key)

EXAMPLES:
  thorpe-pack-sign --gen-keypair --out-dir ./tools/pack-signing
  thorpe-pack-sign --manifest pack.json --key thorpe-pack-private.hex -o signed-pack.json
"#
    );
}

fn read_manifest(path: Option<&str>) -> Result<String, String> {
    match path {
        Some(p) => fs::read_to_string(p).map_err(|e| format!("Failed to read manifest: {e}")),
        None => {
            let mut buf = String::new();
            io::stdin()
                .read_to_string(&mut buf)
                .map_err(|e| format!("Failed to read stdin: {e}"))?;
            Ok(buf)
        }
    }
}

fn load_signing_key(key_path: Option<&str>) -> Result<ed25519_dalek::SigningKey, String> {
    if let Some(path) = key_path {
        let hex = fs::read_to_string(path).map_err(|e| format!("Failed to read key file: {e}"))?;
        return signing_key_from_seed_hex(hex.trim());
    }
    if let Ok(hex) = env::var("THORPE_PACK_SIGNING_KEY") {
        return signing_key_from_seed_hex(hex.trim());
    }
    Err("Provide --key <file> or set THORPE_PACK_SIGNING_KEY.".into())
}

fn gen_keypair(out_dir: Option<&str>) -> Result<(), String> {
    let dir = PathBuf::from(out_dir.unwrap_or("tools/pack-signing"));
    fs::create_dir_all(&dir).map_err(|e| e.to_string())?;

    let (private_hex, public_hex) = generate_keypair_hex();
    let private_path = dir.join("thorpe-pack-private.hex");
    let public_path = dir.join("thorpe-pack-public.hex");

    fs::write(&private_path, format!("{private_hex}\n")).map_err(|e| e.to_string())?;
    fs::write(&public_path, format!("{public_hex}\n")).map_err(|e| e.to_string())?;

    println!("Generated Ed25519 keypair:");
    println!("  Private seed: {}", private_path.display());
    println!("  Public key:   {}", public_path.display());
    println!();
    println!("Embed this public key in src-tauri/src/repairs/pack_signing.rs:");
    println!("  THORPE_PACK_PUBLIC_KEY_HEX = \"{public_hex}\"");
    println!();
    println!("Never commit the private key. Add thorpe-pack-private.hex to .gitignore.");

    Ok(())
}

fn sign_manifest_cmd(
    manifest_path: Option<&str>,
    key_path: Option<&str>,
    output_path: Option<&str>,
) -> Result<(), String> {
    let raw = read_manifest(manifest_path)?;
    let mut manifest: RepairPackManifest =
        serde_json::from_str(&raw).map_err(|e| format!("Invalid manifest JSON: {e}"))?;
    manifest.signature = None;
    let signing_key = load_signing_key(key_path)?;
    let signature = sign_manifest_ed25519(&manifest, &signing_key)?;
    manifest.signature = Some(signature);
    let signed = serde_json::to_string_pretty(&manifest).map_err(|e| e.to_string())?;

    match output_path {
        Some(path) => {
            fs::write(path, format!("{signed}\n")).map_err(|e| e.to_string())?;
            println!("Signed pack written to {path}");
        }
        None => println!("{signed}"),
    }
    Ok(())
}

fn main() {
    let args: Vec<String> = env::args().collect();
    if args.len() < 2 || args.iter().any(|a| a == "--help" || a == "-h") {
        usage();
        std::process::exit(if args.len() < 2 { 1 } else { 0 });
    }

    let mut gen = false;
    let mut out_dir: Option<String> = None;
    let mut manifest_path: Option<String> = None;
    let mut key_path: Option<String> = None;
    let mut output_path: Option<String> = None;

    let mut i = 1;
    while i < args.len() {
        match args[i].as_str() {
            "--gen-keypair" => gen = true,
            "--out-dir" => {
                i += 1;
                out_dir = args.get(i).cloned();
            }
            "--manifest" | "-m" => {
                i += 1;
                manifest_path = args.get(i).cloned();
            }
            "--key" | "-k" => {
                i += 1;
                key_path = args.get(i).cloned();
            }
            "--output" | "-o" => {
                i += 1;
                output_path = args.get(i).cloned();
            }
            other => {
                eprintln!("Unknown argument: {other}");
                usage();
                std::process::exit(1);
            }
        }
        i += 1;
    }

    let result = if gen {
        gen_keypair(out_dir.as_deref())
    } else {
        sign_manifest_cmd(
            manifest_path.as_deref(),
            key_path.as_deref(),
            output_path.as_deref(),
        )
    };

    if let Err(e) = result {
        eprintln!("Error: {e}");
        std::process::exit(1);
    }
}
