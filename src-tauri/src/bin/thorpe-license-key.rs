use std::env;

use thorpe_lib::licensing::{generate_license_key, validate_license_key};

fn usage() {
    eprintln!(
        r#"Thorpe license key generator

USAGE:
  thorpe-license-key --tier PRO|ENT --group1 <val> --group2 <val> --group3 <val>
  thorpe-license-key --validate <LICENSE-KEY>

ENV:
  THORPE_LICENSE_SIGNING_SECRET   HMAC secret (required for release builds)

EXAMPLES:
  thorpe-license-key --tier PRO --group1 ACME --group2 2026 --group3 A001
  thorpe-license-key --validate PRO-ACME-2026-A001-XXXX
"#
    );
}

fn parse_flag(args: &[String], flag: &str) -> Option<String> {
    args.iter()
        .position(|a| a == flag)
        .and_then(|i| args.get(i + 1).cloned())
}

fn main() {
    let args: Vec<String> = env::args().collect();
    if args.len() < 2 || args.iter().any(|a| a == "--help" || a == "-h") {
        usage();
        std::process::exit(if args.len() < 2 { 1 } else { 0 });
    }

    if let Some(key) = parse_flag(&args, "--validate") {
        match validate_license_key(&key) {
            Ok((tier, normalized)) => {
                println!("Valid {tier} license: {normalized}");
            }
            Err(err) => {
                eprintln!("Invalid license: {err}");
                std::process::exit(1);
            }
        }
        return;
    }

    let tier = parse_flag(&args, "--tier").unwrap_or_default();
    let g1 = parse_flag(&args, "--group1").unwrap_or_default();
    let g2 = parse_flag(&args, "--group2").unwrap_or_default();
    let g3 = parse_flag(&args, "--group3").unwrap_or_default();

    if tier.is_empty() || g1.is_empty() || g2.is_empty() || g3.is_empty() {
        eprintln!("--tier, --group1, --group2, and --group3 are required.");
        usage();
        std::process::exit(1);
    }

    match generate_license_key(&tier, &g1, &g2, &g3) {
        Ok(key) => println!("{key}"),
        Err(err) => {
            eprintln!("{err}");
            std::process::exit(1);
        }
    }
}
