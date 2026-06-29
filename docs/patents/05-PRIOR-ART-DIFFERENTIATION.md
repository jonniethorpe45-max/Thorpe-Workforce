# Prior Art and Differentiation Notes

**Purpose:** Guide patent counsel's prior-art search and prosecution strategy. This is not a completed prior-art search.

---

## 1. Categories of known art (to search)

### 1.1 Conversational IT support chatbots

**Examples to search:** Microsoft Support virtual agent, Apple Support app chat, generic ChatGPT IT troubleshooting, Intercom/Zendesk AI bots.

**Typical limitations:**

- Recommend manual steps; do not execute OS commands locally
- No structured repair result object returned with chat
- No post-action verification scan
- Cloud-dependent

**Thorpe/Jonathan differentiation:**

- Execute-then-narrate: repairs complete before LLM response
- Structured `ChatResponse` with `repairs_executed`, `pending_repairs`, `verification`
- Works fully offline for diagnostics and local narrative

### 1.2 Remote monitoring and RMM (MSP tools)

**Examples to search:** ConnectWise Automate, Datto RMM, NinjaOne, Microsoft Intune remediations.

**Typical limitations:**

- Agent managed by MSP, not end-user conversational
- Scripted remediations, not NL-driven planning
- No consumer-facing AI persona
- Requires central management server

**Differentiation:**

- User-initiated natural language on local device
- Jonathan persona with chat approval UX
- Optional PSA webhook integration (outbound), not full RMM stack

### 1.3 OS built-in troubleshooters

**Examples:** Windows Troubleshooter, macOS Diagnostics, Linux network-manager troubleshoot.

**Typical limitations:**

- Fixed decision trees per symptom category
- No LLM planning or narration
- No chat interface with history
- No signed extensible repair packs

**Differentiation:**

- LLM + rules hybrid planner
- Signed OTA repair packs
- Unified incident session with evidence artifacts

### 1.4 LLM tool-use / function-calling agents

**Examples:** OpenAI function calling, LangChain agents, AutoGPT, Microsoft Copilot actions.

**Typical limitations:**

- LLM decides and triggers tools in cloud loop
- Hallucinated tool invocations possible
- Narrative and execution interleaved, not execute-then-narrate
- Often cloud-only

**Differentiation:**

- Deterministic Rust repair engine owns execution order
- LLM planner output filtered by signed allowlist
- Narrator constrained by system prompt to executed repairs only
- Dual LLM with separate fallbacks

### 1.5 Endpoint security and repair utilities

**Examples:** Malwarebytes, CCleaner, built-in disk cleanup, DNS flush utilities.

**Typical limitations:**

- Single-purpose tools, not orchestrated incidents
- No AI chat layer
- No verification loop in chat context

**Differentiation:**

- Orchestrated multi-tool incidents from one message
- Health score verification after mutating repairs

### 1.6 Network diagnostic apps

**Examples:** ping/traceroute GUIs, Wi-Fi analyzer apps.

**Differentiation:**

- Layered offline playbook fused into AI agent pipeline
- Dedup against repair plan
- Embedded in chat metadata

### 1.7 Proactive PC health monitors

**Examples:** HWMonitor alerts, Windows Performance Monitor alerts, third-party RAM/disk alerts.

**Differentiation:**

- Handoff into same orchestration as interactive Jonathan chat
- Pre-computed `AgentPlan` on alert
- Per-metric typed alerts with deduplication

---

## 2. Academic / patent literature search terms

Use these in USPTO, Google Patents, Espacenet:

```
autonomous IT support agent local repair execution
AI chatbot system remediation desktop
execute then explain language model
signed manifest allowed tool list AI agent
offline network diagnostic decision tree
post repair verification health scan
conversational agent mutating action confirmation
MSP webhook AI session audit
dual language model planner narrator
proactive monitor handoff conversational agent
```

**USPC/CPC classes to consider:**

- G06F 11/07 (monitoring, testing, fault detection)
- G06F 11/34 (performance evaluation)
- G06F 9/455 (virtual machines — if claiming isolation)
- G06N 3/08 (learning methods — LLM aspects, Alice risk)
- G06F 21/55 (security — repair pack signing)
- H04L 41/08 (network fault management)
- G06F 3/048 (GUI — design patents)

---

## 3. Alice / abstract idea considerations (US)

**Potential examiner rejection:** Claims directed to "organizing human activity" or "mental processes" via generic computer implementation.

**Proposed technical improvements to emphasize:**

1. **Specific improvement to computer functionality** — automated OS-level repair execution with verification scan improves device operation, not merely presenting information
2. **Signed allowlist gate** — concrete security mechanism, not generic AI
3. **Offline connectivity suite** — specific layered network tests without cloud
4. **Execute-then-narrate ordering** — reduces hallucinated repairs, technical reliability improvement
5. **Post-mutating micro-scan** — measurable health metric change

**Attorney:** Consider emphasizing hardware/device-specific steps (ping, DNS resolution, shell commands) in independent claims.

---

## 4. Public disclosure inventory (bar date risk)

| Disclosure | Risk | Notes |
|------------|------|-------|
| GitHub repository (Thorpe-Workforce) | **High** | Attorney to confirm earliest public commit dates |
| GitHub Releases (v1.0.8, etc.) | **High** | Published installers |
| Marketing website | Medium | If any |
| This patent package | Low | Internal to counsel if not published |
| Customer pilots | Medium | NDA may protect |

**Action:** File provisional **before** additional public marketing if not already barred.

---

## 5. Open source and third-party components

| Component | License | Patent note |
|-----------|---------|-------------|
| Tauri | Apache/MIT | No conflict |
| React | MIT | No conflict |
| ed25519-dalek | BSD | No conflict |
| OpenAI API | Commercial ToS | API use ≠ patent on API |
| SQLite | Public domain | No conflict |

Thorpe-specific orchestration logic is original Rust/TypeScript in repository.

---

## 6. Competitive landscape watch list

Monitor patent filings from:

- Microsoft (Windows Copilot, Intune)
- Apple (Apple Intelligence, diagnostics)
- Google (Chrome OS diagnostics)
- CrowdStrike / SentinelOne (endpoint, different domain)
- NinjaOne, ConnectWise (RMM)

---

## 7. Differentiation summary table (for IDS / prosecution)

| Feature | Prior art typical | Thorpe Jonathan |
|---------|-------------------|-----------------|
| Repair execution | Manual or MSP remote | Local automatic before chat reply |
| LLM role | Planner + executor intertwined | Planner and/or narrator only; Rust executes |
| Offline | Limited | Full diagnostics + local narrative |
| Tool permissions | Admin-defined scripts | Signed repair pack allowlist |
| Network issues | Separate utility | Fused into agent + dedup |
| Proactive monitor | Alert only | Handoff to same agent pipeline |
| Verification | None in chat | Health scan delta in response |
| Mutating safety | Varies | Chat confirmation + Repair Center gate |

---

## 8. Request for formal prior-art search

Counsel should deliver:

1. Search report with closest references (patents + publications)
2. Patentability opinion per application in Document 02
3. Claim amendment recommendations
4. Freedom-to-operate note for commercial launch
