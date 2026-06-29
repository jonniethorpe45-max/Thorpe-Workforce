# System Architecture and Flows — Thorpe Desktop / Jonathan

**For:** Patent drawings and specification figures  
**Format:** Mermaid diagrams (attorney may convert to USPTO-compliant line drawings)

---

## Figure 1 — System architecture (block diagram)

```mermaid
flowchart TB
    subgraph UI["Presentation Layer (React / Tauri WebView)"]
        JA[Jonathan Assistant Chat]
        RC[Repair Center]
        SS[System Scanner]
        WD_UI[Watchdog Settings / Alerts]
        IC[Intelligence Console]
    end

    subgraph API["Tauri Command API"]
        CWJ[chat_with_jonathan]
        ER[execute_repair]
        RSS[run_system_scan]
        GWS[get_watchdog_status]
        RCD[run_connectivity_diagnostics]
    end

    subgraph ORCH["Incident Orchestration (Rust)"]
        OI[orchestrate_incident]
        BP[build_plan]
        PWL[plan_with_llm]
        PWR[plan_with_rules]
        FAT[filter_allowed_tools]
        PCR[plan_chat_repairs]
        PRF[perform_repairs_with_failures]
        VS[quick_system_scan verification]
    end

    subgraph AI["Narrative Layer"]
        LOC[format_technician_response]
        CLD[call_openai_compatible]
        ENT[enterprise_ai resolve_runtime]
    end

    subgraph DATA["Local Persistence (SQLite)"]
        CH[chat_history]
        AS[agent_sessions]
        EV[evidence_artifacts]
        RH[repair_history]
        CD[connectivity_diagnostics]
        WE[watchdog_events]
        FTS[knowledge_fts]
    end

    subgraph OS["Operating System"]
        CMD[Shell / PowerShell Commands]
        NET[Network Stack / Ping / DNS]
    end

    JA --> CWJ
    WD_UI -->|Send to Jonathan| JA
    CWJ --> OI
    OI --> BP
    BP --> PWL
    BP --> PWR
    OI --> FAT
    OI --> PCR
    PCR --> PRF
    PRF --> CMD
    OI --> VS
    VS --> NET
    CWJ --> LOC
    CWJ --> CLD
    CLD --> ENT
    OI --> CH
    OI --> AS
    OI --> EV
    PRF --> RH
    OI --> CD
```

---

## Figure 2 — Chat turn sequence (method steps)

```mermaid
sequenceDiagram
    participant U as User
    participant UI as Jonathan UI
    participant Chat as chat_with_jonathan
    participant Orch as orchestrate_incident
    participant Plan as build_plan
    participant Repair as Repair Engine
    participant Scan as quick_system_scan
    participant Narr as Narrative Layer

    U->>UI: Natural language issue
    UI->>Chat: ChatRequest (message, scan, history, confirmed_repairs?)
    Chat->>Orch: orchestrate_incident()
    Orch->>Orch: collect evidence, security check
    opt Network keywords
        Orch->>Orch: run_connectivity_suite()
    end
    Orch->>Plan: build_plan (LLM or rules)
    Plan-->>Orch: AgentPlan
    Orch->>Orch: filter_allowed_tools (repair packs)
    Orch->>Repair: plan_chat_repairs + perform_repairs
    Repair-->>Orch: RepairResult[]
    opt Mutating success
        Orch->>Scan: quick_system_scan()
        Scan-->>Orch: RepairVerification
    end
    Orch-->>Chat: IncidentResult
    alt Cloud available
        Chat->>Narr: LLM narrate (repairs already done)
    else Autonomous
        Chat->>Narr: format_technician_response
    end
    Narr-->>Chat: message text
    Chat-->>UI: ChatResponse (repairs, pending, verification, plan)
    UI-->>U: Display + optional Approve button
```

---

## Figure 3 — Orchestration decision flowchart

```mermaid
flowchart TD
    START([User message received]) --> EVID[Collect system evidence]
    EVID --> SEC{Security keywords?}
    SEC -->|Yes| CASE[Create escalation case<br/>No repairs]
    SEC -->|No| NET{Connectivity keywords?}
    NET -->|Yes| SUITE[Run offline connectivity suite<br/>Save evidence]
    NET -->|No| PLAN
    SUITE --> DEDUP[Mark connectivity-suite for dedup]
    DEDUP --> PLAN[build_plan: LLM or rules]
    PLAN --> FILTER[filter_allowed_tools]
    FILTER --> DEDUP2{Connectivity already ran?}
    DEDUP2 -->|Yes| REM[Remove connectivity-suite from plan]
    DEDUP2 -->|No| CONF
    REM --> CONF[plan_chat_repairs + confirmed_repairs]
    CONF --> EXEC[Execute to_run repairs]
    EXEC --> MUT{Mutating success?}
    MUT -->|Yes| VERIFY[quick_system_scan verification]
    MUT -->|No| PERSIST
    VERIFY --> PERSIST[Persist session + KB suggestions]
    PERSIST --> LOW{confidence < 0.55?}
    LOW -->|Yes| ESC[Low-confidence case]
    LOW -->|No| RETURN([IncidentResult])
    CASE --> RETURN
    ESC --> RETURN
```

---

## Figure 4 — Watchdog to Jonathan handoff

```mermaid
sequenceDiagram
    participant WD as Watchdog Loop
    participant DB as SQLite
    participant UI as App Shell
    participant NC as Notification Center
    participant JA as Jonathan Assistant
    participant Chat as chat_with_jonathan

    WD->>WD: quick_system_scan()
    WD->>WD: detect_metric_alerts (CPU, memory, disk, health)
    WD->>WD: plan_with_rules (optional auto_plan)
    WD->>DB: save_watchdog_event
    WD->>UI: emit watchdog-alert
    UI->>NC: Notification + Send to Jonathan action
    NC->>JA: setWatchdogHandoff + navigate
    JA->>JA: buildWatchdogJonathanPrompt()
    JA->>Chat: chatWithJonathan (synthetic message)
    Chat->>Chat: orchestrate_incident (full pipeline)
    Chat-->>JA: ChatResponse + merged plan
    JA->>DB: acknowledge_watchdog_event
```

---

## Figure 5 — Repair pack gating

```mermaid
flowchart LR
    MANIFEST[Signed Repair Pack Manifest] --> INSTALL[install_repair_pack<br/>Ed25519 verify]
    INSTALL --> DB[(repair_packs table)]
    DB --> ALLOW[allowed_tool_ids union]
    PLAN[AgentPlan steps] --> IDS[tool_id list]
    IDS --> INTERSECT{filter_allowed_tools}
    ALLOW --> INTERSECT
    INTERSECT --> SAFE[Filtered tool IDs]
    SAFE --> EXEC[perform_repairs]
```

---

## Key data structures (for specification)

### ChatRequest

```
message: string
skill_level: string
scan_context: optional SystemScanResult JSON
history: ChatHistoryItem[]
confirmed_repairs: optional string[] (repair action IDs)
```

### AgentPlan

```
hypotheses: string[]
confidence: float (0.0–1.0)
steps: AgentPlanStep[]
citations: string[]
escalate_if: string[]
```

### AgentPlanStep

```
tool_id: string
reason: string
risk: string
requires_approval: boolean
```

### RepairResult

```
success: boolean
message: string
action_id: string
action_name: string
action_kind: diagnostic | mutating | advisory
record_id: string
```

### RepairVerification

```
health_before: int
health_after: int
issues_before: int
issues_after: int
improved: boolean
```

### ConnectivityReport

```
checks: ConnectivityCheck[]
overall_status: offline | degraded | healthy
recommended_actions: string[]
playbook_summary: string
offline_capable: true
```

### WatchdogEvent

```
id: string
event_type: health_threshold | high_cpu | high_memory | low_disk:{mount}
health_score: int
message: string
plan_json: optional AgentPlan JSON
issues_json: optional ScanIssue[] JSON
acknowledged: boolean
```

---

## Platform deployment

| Component | Technology |
|-----------|------------|
| Desktop shell | Tauri 2 (Rust + WebView) |
| Frontend | React 18, TypeScript |
| Backend | Rust (scanner, repairs, agent, AI) |
| Database | SQLite with FTS5 |
| Cloud AI | OpenAI-compatible HTTPS API (optional) |
| Targets | Windows 10/11, macOS Apple Silicon, Linux |

---

## Suggested patent figure captions

1. **FIG. 1** — Block diagram of Thorpe Desktop autonomous IT support system showing presentation layer, orchestration engine, narrative layer, local persistence, and operating system interface.

2. **FIG. 2** — Sequence diagram illustrating execute-then-narrate ordering wherein repair execution precedes AI narrative generation.

3. **FIG. 3** — Flowchart of incident orchestration including security gate, connectivity pre-run, planning, allowlist filtering, confirmation gate, execution, and verification.

4. **FIG. 4** — Sequence diagram of proactive watchdog alert handoff into conversational agent pipeline.

5. **FIG. 5** — Flowchart of cryptographically signed repair pack allowlist intersection with AI planner output.
