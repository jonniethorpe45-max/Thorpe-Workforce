# Thorpe Desktop / Jonathan — One-Page Executive Brief for Patent Counsel

**Product:** Thorpe Desktop · **Agent:** Jonathan · **Date:** June 27, 2026

---

## What we invented

**Jonathan** is an AI technician embedded in a desktop app that **fixes computers locally**, not just advises. When a user says “Wi-Fi isn’t working” or “my PC is slow,” Jonathan:

1. Diagnoses the machine on-device (no cloud required for core operation)
2. **Runs repairs automatically** (safe diagnostics) and asks permission before system-changing actions
3. **Re-scans** to verify the fix improved health score
4. **Then** explains what it did—in plain language or via optional cloud AI

**Core novelty:** Repairs execute **before** the AI writes its reply. The AI cannot invent fixes it did not perform.

---

## Why it matters commercially

| Problem today | Jonathan approach |
|---------------|-------------------|
| Chatbots give manual steps | Executes OS-level repairs locally |
| Cloud-only AI support | Works offline for diagnostics + local narrative |
| No proof a “fix” worked | Before/after health verification in every response |
| Unsafe autonomous agents | Mutating actions require explicit user approval |
| MSP tools need IT staff | End-user conversational interface |

**Markets:** Consumer PC support, SMB without IT staff, MSP assist (PSA webhooks), enterprise with governed AI (role/budget controls).

---

## What to patent (priority)

| Priority | Application | One-line description |
|----------|-------------|----------------------|
| **P0** | **A — Core orchestration** | Execute-then-narrate autonomous IT incident pipeline on client device |
| **P0** | **B — Repair packs** | Cryptographically signed allowlist gates which OS tools AI may run |
| **P0** | **C — Offline connectivity** | Layered network diagnostics fused into agent; no cloud required |
| **P1** | **D — Watchdog handoff** | Background CPU/memory/disk monitor hands alerts into same agent pipeline |
| **P1** | **E — Dual LLM** | Separate planner LLM and narrator LLM with independent fallbacks |

Full detail: `02-PATENT-CANDIDATE-INVENTORY.md`

---

## Technical proof (reduction to practice)

- **Shipped in code:** Thorpe Desktop v1.1.0 (Rust/Tauri + React)
- **Platforms:** Windows, macOS, Linux
- **Key module:** `orchestrate_incident` in `src-tauri/src/agent/mod.rs`
- **Tests:** 70+ frontend, 40+ Rust unit tests

---

## Urgency / disclosure risk

- Source and releases on **GitHub** (public) — counsel must confirm bar dates and recommend **provisional filing ASAP** on Patent A if not already filed.
- Complete `06-INVENTOR-AND-ASSIGNMENT-SHEET.md` before filing.

---

## What we need from counsel

1. Prior-art search on Patents A–E  
2. Provisional filing recommendation and timeline  
3. Alice (§101) analysis for software method claims  
4. Inventorship and assignment to operating company  
5. Trademark clearance: **Thorpe**, **Jonathan**

**Full package:** `docs/patents/00-PATENT-PACKAGE-INDEX.md`
