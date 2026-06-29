# Patent Candidate Inventory — Thorpe Desktop / Jonathan

**Purpose:** Request for patent counsel to evaluate, prioritize, and file applications to protect the Thorpe Desktop concept and Jonathan autonomous technician architecture.

**Recommended jurisdiction:** United States (USPTO) utility patents first; consider PCT within 12 months for international coverage.

**Filing strategy note:** Consider an **early provisional** on Patent A to establish priority date, followed by non-provisional with continuations for B–F within 12 months.

---

## Priority tier summary

| Tier | Patents | Rationale |
|------|---------|-----------|
| **P0 — File first** | A, B, C | Core differentiation; highest competitive value |
| **P1 — File within 6 months** | D, E | Strong supplementary protection |
| **P2 — Evaluate after search** | F, G, H | Narrower or design; depends on prior art |
| **P3 — Trade secret / copyright** | UI flows, prompt text | May be better protected non-patent |

---

## Patent A — Core autonomous incident orchestration (BROAD)

**Working title:** System and Method for Local-First Autonomous IT Incident Resolution with Execute-Then-Narrate AI Assistant

**Type:** Utility — system + method claims

**Abstract (draft):** A computer-implemented system on an end-user device receives a natural-language support request, collects local system evidence, plans a set of repair actions using rule-based and/or LLM-based planning, filters planned actions against a signed allowlist, executes non-mutating diagnostics automatically and defers mutating repairs pending user confirmation, performs a follow-up health scan after successful mutating repairs, and only thereafter generates a user-facing narrative constrained to describe repairs already executed.

**Key elements to claim:**

- Execute-then-narrate ordering (repairs before LLM narrative)
- Dual planner fallback (LLM JSON plan → rule plan)
- Confirmation gate for mutating vs. diagnostic actions
- Post-mutating verification scan with structured improvement metrics
- Structured chat response with repairs, pending, verification, plan metadata
- Local-first operation without cloud dependency

**Code anchors:** `orchestrate_incident`, `chat_with_jonathan`, `plan_chat_repairs`, `format_technician_response`

**Estimated claim count:** 1 independent system + 1 independent method + 15–25 dependent

**Priority:** **P0 — Provisional recommended immediately**

---

## Patent B — Signed repair pack gated autonomous execution

**Working title:** Cryptographically Signed Repair Pack Allowlist for AI-Agent OS Tool Execution

**Type:** Utility

**Abstract (draft):** A method for controlling which operating-system-level repair tools an autonomous AI agent may invoke, comprising installing repair packs with Ed25519-signed manifests, maintaining an allowlist union of enabled pack tools, and intersecting AI planner output with the allowlist before execution.

**Key elements:**

- Repair pack manifest structure (tools, version, maps_to_action)
- Ed25519 signature verification on install
- Runtime intersection of planner tool IDs with `allowed_tool_ids`
- Built-in vs. custom pack distinction; built-in packs non-overwritable

**Code anchors:** `pack_signing.rs`, `packs.rs`, `filter_allowed_tools`, `install_repair_pack`

**Priority:** **P0**

---

## Patent C — Offline layered connectivity diagnostics integrated into AI agent pipeline

**Working title:** Offline Network Connectivity Decision Tree with Agent Incident Fusion and Diagnostic Deduplication

**Type:** Utility

**Abstract (draft):** Upon detecting network-related user intent, a local agent executes a layered connectivity suite (adapter, gateway, DNS, internet reachability) without cloud connectivity, evaluates a local playbook to produce recommended repair actions and summary, persists results as session evidence, suppresses duplicate connectivity diagnostics in a subsequent repair plan, and embeds the report in an AI chat response.

**Key elements:**

- Keyword-triggered pre-run before planning
- Layered checks with pass/fail/warn status
- Local playbook decision tree → `recommended_actions`
- `offline_capable: true` semantic
- Dedup: remove `connectivity-suite` from plan if suite already executed
- Persistence to diagnostics table + evidence artifacts

**Code anchors:** `connectivity/mod.rs`, `orchestrate_incident` connectivity block

**Priority:** **P0**

---

## Patent D — Proactive watchdog to autonomous agent handoff

**Working title:** Background Health Monitor with Pre-Computed Repair Plan Handoff to Conversational AI Agent

**Type:** Utility

**Abstract (draft):** A background monitoring service periodically scans system health, generates per-metric alerts (CPU, memory, disk, composite health), optionally pre-computes a repair plan using the same rule planner as the conversational agent, notifies the user, and upon user initiation injects a synthetic support request into the same incident orchestration pipeline used for interactive chat, merging any pre-computed plan with agent-generated results.

**Key elements:**

- Per-metric alert types with deduplication per event type
- Pre-computed `plan_json` on watchdog events
- Tauri event → UI notification → "Send to Jonathan"
- Shared `orchestrate_incident` pipeline for watchdog and chat
- Acknowledgment on successful handoff

**Code anchors:** `watchdog/mod.rs`, `watchdog.ts`, `JonathanAssistant.tsx` handoff effect

**Priority:** **P1**

---

## Patent E — Dual-LLM planner/narrator with independent fallbacks

**Working title:** Separated Planning and Narration Language Models for Autonomous IT Support with Rule-Based Fallback

**Type:** Utility

**Abstract (draft):** An IT support system employs a first LLM call producing structured JSON repair plans filtered to an allowlist, and a second LLM call generating user narrative constrained to repairs already executed, each independently fallible to rule-based planning and template-based narration respectively.

**Key elements:**

- Planner: JSON `AgentPlan`, temperature 0.2, tool filtering
- Narrator: conversational, temperature 0.7, anti-hallucination prompt
- Enterprise vs. user vs. local runtime resolution
- Independent fallback paths

**Code anchors:** `agent/planner.rs`, `ai/mod.rs`, `build_plan`, `resolve_user_cloud_response`

**Priority:** **P1**

---

## Patent F — Security keyword circuit breaker for autonomous repair agents

**Working title:** Autonomous IT Agent Security Escalation Gate Blocking OS Repairs on Credential and Malware Indicators

**Type:** Utility (narrower)

**Key elements:**

- Keyword detection for malware, ransomware, virus, password, credential
- Bypass repair engine entirely
- Automatic support case creation + PSA webhook
- Return structured escalation without mutating repairs

**Code anchors:** `security_escalation`, `is_security_escalation` in `agent/mod.rs`

**Priority:** **P2**

---

## Patent G — Org playbook full-text search fusion for AI planner context

**Working title:** Organizational Playbook Indexing into Unified Full-Text Search for AI Repair Planning

**Type:** Utility (narrower)

**Key elements:**

- Org playbooks written to FTS5 virtual table on save
- Same search path as knowledge base for planner excerpts
- Intel feed search in parallel

**Code anchors:** `db/mod.rs` `rebuild_knowledge_fts_from_playbooks`, `build_planner_context`

**Priority:** **P2**

---

## Patent H — Tiered license-governed AI runtime (Enterprise)

**Working title:** Multi-Tier License Feature Gating for Autonomous Local Repairs and Enterprise AI Policy Layer

**Type:** Utility (business method + system — evaluate Alice risk)

**Key elements:**

- Free tier: local autonomous repairs without cloud
- Enterprise: role-based provider access, budget enforcement, audit log
- Same repair engine across tiers; cloud gated separately from chat

**Code anchors:** `licensing/mod.rs`, `enterprise_ai/mod.rs`

**Priority:** **P2** — may be difficult to claim; consider trade secret for pricing tiers

---

## Design patents (optional)

| ID | Subject | Notes |
|----|---------|-------|
| D1 | Jonathan chat UI with repair approval cards | Distinctive approval-needed amber banner + Approve button |
| D2 | Health score ring + dashboard layout | If visually distinctive |
| D3 | Connectivity report inline in chat | Layered check list presentation |

Design patents are **lower priority** than utility patents for core technology.

---

## Defensive publications (alternative to filing)

If budget-constrained, consider publishing narrowly on:

- Specific keyword lists for `plan_repairs`
- Exact health score penalty formula

This prevents others from patenting identical specifics while keeping broad claims for Patents A–C.

---

## Estimated filing budget (for client planning — attorney to quote)

| Item | Typical range (US) |
|------|-------------------|
| Provisional (Patent A) | $3,000–$8,000 + USPTO fees |
| Non-provisional (A) | $12,000–$25,000 + fees |
| Each additional non-provisional (B–E) | $8,000–$18,000 each |
| Prior art search (comprehensive) | $2,000–$5,000 |
| PCT national phase (per country) | Varies |

---

## Recommended filing sequence

```
Month 0:  Provisional — Patent A (core orchestration)
Month 0:  Provisional — Patent B (repair packs) OR combine with A if budget limited
Month 1:  Prior art search results → refine claims
Month 2:  Provisional — Patent C (connectivity) if not combined
Month 6:  Non-provisional A + continuations/in divisionals for B, C
Month 6:  File D, E if search favorable
Month 12: PCT decision
```

---

## Request to patent attorney

Please provide:

1. Patentability opinion on Patents A–E against your search
2. Recommendation on combining vs. separating applications
3. Alice/abstract idea analysis for software method claims
4. Inventorship review (Document 06)
5. Assignment to operating company
6. Filing timeline given any public GitHub disclosure dates
7. Trademark clearance for "Jonathan" and "Thorpe" in Class 9/42
