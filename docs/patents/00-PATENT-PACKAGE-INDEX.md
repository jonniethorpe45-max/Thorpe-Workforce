# Thorpe Desktop — Patent Attorney Submission Package

**Prepared for:** Patent counsel review and filing strategy  
**Product:** Thorpe Desktop (cross-platform IT support application)  
**Core invention:** Jonathan — autonomous AI technician with local repair orchestration  
**Codebase reference:** `/workspace` (Thorpe-Workforce repository, Desktop branch)  
**Document date:** June 27, 2026  
**Software version referenced:** 1.1.0 (see `package.json`, `src-tauri/Cargo.toml`)

---

## Important notice (read first)

This package is a **technical invention disclosure** prepared from the Thorpe Desktop source code and product design. It is **not legal advice**, does not constitute filed patent claims, and does not establish priority dates. Your patent attorney must:

- Conduct a formal prior-art and patentability search
- Draft claims appropriate to your jurisdiction (USPTO, EPO, etc.)
- Confirm inventorship and ownership with the client
- Advise on provisional vs. non-provisional, PCT, and continuation strategy
- Review export control and open-source implications before filing

---

## Package contents

| # | Document | Purpose |
|---|----------|---------|
| 01 | [01-INVENTION-DISCLOSURE-JONATHAN.md](./01-INVENTION-DISCLOSURE-JONATHAN.md) | Primary invention disclosure — how Jonathan works, step-by-step |
| 02 | [02-PATENT-CANDIDATE-INVENTORY.md](./02-PATENT-CANDIDATE-INVENTORY.md) | Recommended patent applications (utility + optional design) |
| 03 | [03-SYSTEM-ARCHITECTURE-AND-FLOWS.md](./03-SYSTEM-ARCHITECTURE-AND-FLOWS.md) | Architecture diagrams, data structures, sequence flows |
| 04 | [04-CLAIM-SEEDS-FOR-ATTORNEY.md](./04-CLAIM-SEEDS-FOR-ATTORNEY.md) | Seed independent/dependent claims for attorney drafting |
| 05 | [05-PRIOR-ART-DIFFERENTIATION.md](./05-PRIOR-ART-DIFFERENTIATION.md) | Known art categories and differentiation arguments |
| 06 | [06-INVENTOR-AND-ASSIGNMENT-SHEET.md](./06-INVENTOR-AND-ASSIGNMENT-SHEET.md) | Inventor information template and assignment checklist |

---

## Executive summary for counsel

**Thorpe Desktop** is a local-first desktop application (Windows, macOS, Linux) that embeds **Jonathan**, an AI technician agent. Unlike conventional chatbot IT assistants that recommend manual steps, Jonathan:

1. **Plans** repairs using rules and/or LLM JSON planning
2. **Executes** OS-level diagnostic and repair actions locally **before** generating user-facing narrative
3. **Verifies** mutating repairs with a follow-up health scan
4. **Gates** mutating actions behind user confirmation while auto-running safe diagnostics
5. **Operates offline** for core diagnostics (connectivity suite, repair engine, local narrative)
6. **Integrates** proactive monitoring (Watchdog) that hands off pre-planned incidents into the same pipeline
7. **Restricts** autonomous tool permissions via cryptographically signed repair packs
8. **Separates** planning LLM and narration LLM with independent fallbacks

The recommended filing strategy (detailed in Document 02) centers on **one broad system/method patent** on the execute-then-narrate autonomous agent architecture, supplemented by **narrower patents** on connectivity playbook fusion, signed repair-pack gating, watchdog handoff, and post-repair verification loops.

---

## Key source files (for examiner / code deposit)

| Subsystem | Primary paths |
|-----------|---------------|
| Chat entry & narrative | `src-tauri/src/ai/mod.rs` |
| Incident orchestration | `src-tauri/src/agent/mod.rs` |
| LLM/rule planner | `src-tauri/src/agent/planner.rs` |
| Repair engine | `src-tauri/src/repairs/mod.rs`, `planner.rs` |
| Repair pack signing | `src-tauri/src/repairs/pack_signing.rs`, `packs.rs` |
| Offline connectivity | `src-tauri/src/connectivity/mod.rs` |
| Proactive watchdog | `src-tauri/src/watchdog/mod.rs` |
| Evidence collection | `src-tauri/src/evidence/mod.rs` |
| Enterprise AI policy | `src-tauri/src/enterprise_ai/mod.rs` |
| Licensing / features | `src-tauri/src/licensing/mod.rs` |
| UI — Jonathan chat | `src/pages/JonathanAssistant.tsx` |
| UI — Watchdog handoff | `src/lib/watchdog.ts`, `src/components/layout/AppLayout.tsx` |

---

## Suggested next steps for attorney

1. Review Documents 01–04 and confirm inventorship (Document 06).
2. Run prior-art search on: autonomous IT repair agents, LLM tool execution, desktop health monitors, MSP PSA integrations.
3. Decide provisional filing date and claim scope for **Patent A** (core Jonathan orchestration).
4. Evaluate whether to file **Patent B–F** as continuations or separate applications.
5. Request code listing or appendix if filing requires software-related enablement (Alice/Mayo analysis for US).
6. Coordinate trademark (Jonathan, Thorpe) separately from utility patents.

---

## Contact / assignment

_Complete Document 06 before filing._

| Field | Value |
|-------|-------|
| Applicant / assignee | _[Company legal name]_ |
| Address | _[To be completed]_ |
| Correspondence | _[To be completed]_ |
| Inventor(s) | _[See Document 06]_ |
