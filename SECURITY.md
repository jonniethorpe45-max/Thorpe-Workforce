# Security Policy

## Overview

Thorpe is designed with security and user trust as foundational principles. This document outlines our security architecture, practices, and reporting procedures.

## Security Architecture

### Local-First Design

- All user data stored locally in SQLite (`thorpe.db` in app data directory)
- No telemetry or data collection by default
- Cloud AI is opt-in only; API keys stored in the OS credential store (with encrypted local fallback)

### Consent Model

Every sensitive operation requires explicit user consent:

1. **System scans** — User must check consent checkbox before scanning
2. **Repair actions** — Each action shows risk level and requires confirmation
3. **Report sharing** — User controls export and sharing
4. **Data deletion** — User-initiated with double confirmation

### What Thorpe Does NOT Do

- ❌ Request passwords, security answers, or recovery codes
- ❌ Keylogging or input monitoring
- ❌ Browser password extraction
- ❌ Hidden monitoring or spyware behavior
- ❌ Unauthorized privilege escalation
- ❌ Remote control or unattended access
- ❌ Collect personal documents or unrelated personal data
- ❌ Harvest credentials of any kind

### Data Collection (With Consent Only)

System scans collect only diagnostic information:

- Operating system and version
- CPU, memory, disk usage
- Network configuration (not traffic content)
- Running process names and resource usage
- Startup application list
- Hardware summary

### AI Security (Jonathan)

- System prompt enforces security boundaries
- Never requests sensitive credentials
- Distinguishes facts from suggestions
- Warns before risky operations
- Escalates to human technicians when appropriate

### Repair Actions

- Every action rated by risk level (low, medium, high)
- Destructive actions never performed without explicit consent
- All actions logged in repair history
- Actions are cancellable before execution

## Secure Development

- Content Security Policy configured in `tauri.conf.json`
- Tauri capability-based permission model
- Input validation on all Tauri commands
- Parameterized SQLite queries (no SQL injection)
- Dependencies regularly updated

## Reporting Vulnerabilities

If you discover a security vulnerability, please report it responsibly:

1. **Email**: security@thorpe.app
2. **Do not** open public GitHub issues for security vulnerabilities
3. Include steps to reproduce and potential impact
4. We aim to respond within 48 hours

## Security Review Checklist

- [x] Local-first data storage
- [x] Explicit consent for diagnostics
- [x] Explicit consent for repairs
- [x] No credential harvesting
- [x] No keylogging
- [x] No hidden monitoring
- [x] No remote control
- [x] Transparent action logging
- [x] User-controlled data deletion
- [x] CSP headers configured
- [x] AI security boundaries in system prompt
