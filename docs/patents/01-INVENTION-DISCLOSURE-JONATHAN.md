# Invention Disclosure: Jonathan Autonomous AI Technician

**Invention title (working):** Local-First Autonomous IT Incident Orchestration with Execute-Then-Narrate AI Technician  
**Product:** Thorpe Desktop  
**Agent name:** Jonathan  
**Disclosure type:** Utility patent — system and method

---

## 1. Field of the invention

Computer systems diagnostics, automated remediation, and AI-assisted technical support on end-user devices (desktops and laptops) across Windows, macOS, and Linux.

---

## 2. Background and problem solved

Traditional IT support chatbots:

- Recommend manual steps (open Settings, run a command, reboot)
- Depend on continuous cloud connectivity
- Do not verify whether suggested actions improved system health
- Conflate AI text generation with actual system changes
- Lack enterprise controls over which OS-level actions an AI may invoke

**Jonathan** solves this by treating the AI as a **narrator and planner** layered on top of a **deterministic local repair engine** that runs on the device. Repairs execute **before** the user sees the assistant's reply. The AI is constrained not to invent repairs—it may only describe repairs already executed and recorded.

---

## 3. Summary of the invention

Jonathan is implemented as a pipeline:

```
User message → Evidence collection → Security gate → Optional offline connectivity suite
→ Repair planning (LLM JSON or rules) → Repair-pack allowlist filter → Confirmation gate
→ Local OS repair execution → Post-mutating verification scan → Session persistence
→ Narrative generation (local template or cloud LLM) → Structured chat response
```

The user receives a single response containing: narrative text, list of repairs executed, pending repairs requiring approval, verification metrics, connectivity report (if applicable), agent plan, knowledge suggestions, and optional escalation case ID.

---

## 4. Detailed operation — user chat flow

### 4.1 Frontend (`JonathanAssistant.tsx`)

1. User enters a natural-language issue (e.g., "Wi-Fi not working", "computer is slow").
2. Frontend calls Tauri command `chat_with_jonathan` with:
   - `message`: user text
   - `skill_level`: beginner | advanced (affects explanation depth)
   - `scan_context`: optional JSON of last system scan
   - `history`: prior chat turns
   - `confirmed_repairs`: optional list of repair action IDs when user clicks **Approve**
3. Assistant message metadata is persisted and restored from `metadata_json` (repairs, plan, verification, connectivity).

### 4.2 Entry point — `chat_with_jonathan` (`ai/mod.rs`)

**Order of operations (critical for patent characterization):**

1. Parse optional scan context into `SystemScanResult`
2. Save user message to `chat_history`
3. Call `orchestrate_incident()` — **all repairs run here**
4. Convert `IncidentResult` to `ChatExtras` (repairs, pending, verification, etc.)
5. Resolve narrative source:
   - Enterprise AI runtime (`source: "enterprise"`)
   - User cloud OpenAI-compatible API (`source: "openai"`)
   - Local deterministic formatter (`source: "local"`)
   - Fallback variants on policy/error
6. Enrich message with structured sections (case ID, pending repairs, verification, connectivity, plan)
7. Save assistant message with full `metadata_json`
8. Return `ChatResponse`

**Key invariant:** Cloud LLM failure does not prevent repairs from having already executed locally.

### 4.3 Orchestration — `orchestrate_incident` (`agent/mod.rs`)

| Step | Action | Output |
|------|--------|--------|
| 1 | Generate `session_id` (UUID) | Session correlation |
| 2 | `evidence::collect_system_evidence(scan)` | Event log excerpt, service summary, network summary |
| 3 | Persist evidence artifacts (`system_evidence`, `scan_snapshot`) | Audit trail |
| 4 | Seed intel feed and repair packs | Planner tool availability |
| 5 | **Security escalation check** | If malware/credential keywords → create PSA case, **no repairs** |
| 6 | **Connectivity pre-run** (if network keywords) | `ConnectivityReport`, DB record, evidence artifact |
| 7 | `build_plan()` — enterprise LLM → user LLM → rules | `AgentPlan` |
| 8 | Extract `tool_id` from plan steps | Planned repair IDs |
| 9 | `filter_allowed_tools()` — intersect with repair-pack allowlist | Gated tool list |
| 10 | If connectivity already ran, remove duplicate `connectivity-suite` | Dedup |
| 11 | `plan_chat_repairs(planned, confirmed_repairs)` | `to_run` + `pending_confirmation` |
| 12 | `perform_repairs_with_failures(db, to_run)` | `Vec<RepairResult>` |
| 13 | If any mutating repair succeeded → `quick_system_scan()` | `RepairVerification` |
| 14 | `gather_kb()` — knowledge FTS + intel search | `KbSuggestion[]` |
| 15 | `persist_session()` — plan, evidence, confidence | `AgentSessionRecord` + PSA webhook |
| 16 | If `plan.confidence < 0.55` → low-confidence escalation case | Internal case (optional) |

Returns `IncidentResult` to narrative layer.

---

## 5. Repair planning

### 5.1 Rule-based planner (`repairs/planner.rs`)

Maps user message keywords and scan signals to repair tool IDs:

- Network terms → `connectivity-suite`, `dns-flush`
- Performance terms → `high-resource-id`, `startup-review`, `temp-cleanup`, `restart-recommend`
- Storage terms → `disk-analysis`, `temp-cleanup`
- Scan issue categories (storage, performance, network) → corresponding tools
- High memory (>85%) → `high-resource-id`

### 5.2 LLM planner (`agent/planner.rs`)

When enterprise or user cloud runtime is available:

- Builds `PlannerContext` with message, scan JSON, evidence JSON, KB excerpts (3), intel excerpts (3), available tools
- Calls OpenAI-compatible `/chat/completions` with `response_format: json_object`, temperature 0.2
- Parses JSON into `AgentPlan`: hypotheses, confidence, steps[], citations, escalate_if
- Each step: `tool_id`, `reason`, `risk`, `requires_approval`
- Filters steps to tools present in `available_tools`

Falls back to `plan_with_rules` if LLM unavailable or returns empty steps.

### 5.3 Repair action taxonomy (`repairs/mod.rs`)

| Kind | Behavior | Examples |
|------|----------|----------|
| `diagnostic` | Auto-execute without confirmation | `connectivity-suite`, `disk-analysis`, `high-resource-id` |
| `mutating` | Requires user confirmation | `dns-flush`, `temp-cleanup`, `print-spooler-restart` |
| `advisory` | Informational only | `startup-review`, `update-check`, `restart-recommend` |

`plan_chat_repairs` splits planned IDs into immediate execution vs. pending approval based on `requires_confirmation` and `confirmed_repairs` list.

---

## 6. Repair execution and verification

### 6.1 Execution

`perform_repair(db, action_id)`:

1. Looks up `RepairAction` from catalog
2. Runs platform-specific command (PowerShell, shell, etc.) via `execute_action`
3. Records result in `repair_history` SQLite table
4. Returns `RepairResult` with success, message, details, `action_kind`

### 6.2 Post-mutating verification

When `any_mutating_success(repairs_executed)`:

```rust
RepairVerification {
    health_before,    // from scan context or 0
    health_after,     // from quick_system_scan()
    issues_before,
    issues_after,
    improved: health_after > health_before || issues_after < issues_before
}
```

Surfaced in UI and appended to both local and cloud narratives.

---

## 7. Offline connectivity diagnostics

**Trigger:** `is_connectivity_issue(message)` — keyword detection in user message.

**Suite (`run_connectivity_suite`):** Layered checks without internet:

1. Network adapter status (OS-specific)
2. Default gateway reachability (ping)
3. DNS resolution (`example.com`)
4. Internet reachability (ping 1.1.1.1, 8.8.8.8)

**Playbook (`evaluate_playbook`):** Local decision tree produces:

- `overall_status`: offline | degraded | healthy
- `recommended_actions`: repair tool IDs
- `playbook_summary`: human-readable assessment
- `offline_capable: true`

**Agent integration:**

- Full report saved to `connectivity_diagnostics` table
- Evidence artifact `offline_connectivity_suite` linked to session
- `connectivity-suite` removed from repair plan if suite already ran
- Report embedded in `ChatResponse.connectivity_report`

---

## 8. Narrative modes (autonomous vs cloud)

### 8.1 Local autonomous (`format_technician_response`)

Deterministic markdown builder using:

- User first name personalization
- Repairs executed (grouped by diagnostic / mutating / advisory)
- Pending repairs list
- Verification block
- Connectivity summary
- Agent plan steps
- KB suggestions

No network required.

### 8.2 Cloud narration (`call_openai_compatible`)

System prompt explicitly states repairs **already ran**. LLM must:

- Describe repairs in past tense
- Not invent actions not in `repairs_executed`
- Never request credentials
- Personalize by first name

Temperature 0.7 for conversational tone.

### 8.3 Enterprise AI layer (`enterprise_ai/mod.rs`)

`resolve_runtime("jonathan")` gates cloud use on:

- License feature `enterprise_ai_console`
- Org policy: `cloud_ai_enabled`, monthly budget, token limits
- Agent enabled + user role in `allowed_roles`
- Provider enabled + API key configured

Usage logged to audit table.

---

## 9. Repair pack security model

**Purpose:** Control which OS-level tools Jonathan may invoke.

1. **Built-in packs** (`thorpe-core`, `thorpe-network`, `thorpe-performance`) ship with app
2. **Custom packs** installed via `install_repair_pack(manifest_json)`
3. Manifest signed with **Ed25519** (or legacy HMAC) — `pack_signing.rs`
4. `allowed_tool_ids(db)` = union of enabled pack tools
5. `filter_allowed_tools` intersects planner output with allowlist before execution

CLI tools: `thorpe-pack-sign`, `thorpe-license-key`

---

## 10. Proactive watchdog integration

Background loop (`watchdog/mod.rs`):

- Interval: configurable (default 15 min, minimum 5)
- Runs `quick_system_scan()`
- **Per-metric alerts:** CPU >80%, memory >85%, disk >90%, health below threshold
- Dedupes unacknowledged alerts per `event_type` within interval
- Optional `auto_plan`: pre-computes `AgentPlan` via `plan_with_rules`
- Emits Tauri event `watchdog-alert` to UI

**Handoff to Jonathan:**

1. User clicks "Send to Jonathan" (Settings or notification)
2. `WatchdogHandoff` stored in app state; navigate to `/jonathan`
3. Synthetic user prompt built: `Watchdog alert (CPU spike): ... Health score is 68/100. Please investigate...`
4. Full `chat_with_jonathan` / `orchestrate_incident` pipeline runs
5. Pre-loaded plan merged into response if API plan absent
6. Event acknowledged on success

---

## 11. Intelligence console and RAG

**Enterprise-gated** (`intelligence_console` license feature):

- Threat intel feed sync (`sync_intel_feed`)
- Org playbooks (`upsert_org_playbook`) — content indexed into `knowledge_fts` on save
- Repair pack management
- Agent session audit and PDF export

**Planner RAG:** `search_knowledge_for_message` (FTS) + `search_intel_for_message` feed excerpts into `PlannerContext`. Playbooks surface through same FTS path as KB articles.

---

## 12. Security and escalation

| Trigger | Behavior |
|---------|----------|
| Malware/ransomware/virus keywords | No repairs; `SupportCase` created; PSA `case.escalated` |
| Password/credential keywords | Same |
| `plan.confidence < 0.55` | Low-confidence escalation case (internal) |
| Mutating repairs | User approval required in chat or Repair Center |

Jonathan system prompt forbids credential requests.

---

## 13. Data persistence

| Table | Contents |
|-------|----------|
| `chat_history` | Messages + `metadata_json` (full incident state) |
| `agent_sessions` | Plan JSON, evidence JSON, confidence, status |
| `evidence_artifacts` | Per-session evidence blobs |
| `repair_history` | Executed repair log |
| `connectivity_diagnostics` | Offline suite results |
| `watchdog_events` | Proactive alerts + plan JSON + issues JSON |
| `knowledge_fts` | KB + org playbooks (FTS5) |

PSA webhooks: `agent.session.completed`, `case.escalated`, `case.created` with HMAC signature.

---

## 14. Novel technical combinations (for patentability discussion)

_Attorney to evaluate against prior art:_

1. **Execute-then-narrate:** Local repair engine completes before any LLM generates user-visible text; LLM constrained to factual repair log.
2. **Dual-LLM architecture:** Separate JSON planner and conversational narrator with independent fallbacks.
3. **Signed repair-pack allowlist:** Cryptographic gate on autonomous OS tool execution.
4. **Offline connectivity playbook fused into agent path** with duplicate diagnostic suppression.
5. **Post-mutating verification micro-scan** feeding structured chat metadata.
6. **Watchdog-to-agent handoff** reusing full incident pipeline with pre-computed plan.
7. **Confirmation-threaded chat orchestration:** Same `orchestrate_incident` handles initial and approval messages via `confirmed_repairs`.
8. **Tiered AI governance:** Free local autonomous repairs + optional user cloud + enterprise role/budget policy on same engine.

---

## 15. Reduction to practice

- **Status:** Implemented and tested in Thorpe Desktop v1.1.0 codebase
- **Platforms:** Windows (NSIS/MSI), macOS (DMG), Linux (AppImage/deb) via Tauri 2
- **Tests:** 70+ frontend tests, 40 Rust unit tests including watchdog, connectivity, repair planning
- **Public disclosure risk:** GitHub repository and releases may affect filing timeline — attorney to advise on bar dates

---

## 16. Figures referenced

See [03-SYSTEM-ARCHITECTURE-AND-FLOWS.md](./03-SYSTEM-ARCHITECTURE-AND-FLOWS.md) for:

- Figure 1: System architecture block diagram
- Figure 2: Chat turn sequence diagram
- Figure 3: Orchestration flowchart
- Figure 4: Watchdog handoff sequence
- Figure 5: Repair pack gating flow

---

## 17. Glossary

| Term | Definition |
|------|------------|
| Jonathan | Embedded AI technician agent in Thorpe Desktop |
| Repair action / tool | Atomic diagnostic or mutating OS operation with ID (e.g., `dns-flush`) |
| Agent plan | Structured JSON plan with hypotheses, steps, confidence |
| Incident | One user message processed through `orchestrate_incident` |
| Mutating repair | OS-changing action requiring explicit user confirmation |
| Repair pack | Signed manifest defining allowed repair tools |
| Watchdog | Background proactive health monitor |
