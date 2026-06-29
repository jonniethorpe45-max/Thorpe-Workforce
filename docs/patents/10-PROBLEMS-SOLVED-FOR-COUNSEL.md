# Thorpe Desktop — Problems Solved

**Prepared for:** Patent counsel  
**Product:** Thorpe Desktop  
**Core invention:** Jonathan — autonomous AI technician with local repair orchestration  
**Date:** June 27, 2026  
**Software version:** 1.1.0

---

## Executive summary

Thorpe Desktop is a cross-platform desktop application (Windows, macOS, Linux) that embeds **Jonathan**, an autonomous AI technician. Jonathan does not merely advise users—it **diagnoses, executes, and verifies repairs locally** on the end-user device, then explains what was done in plain language.

The core technical problem solved: **conventional IT support chatbots recommend manual steps they never perform, cannot verify, and cannot safely execute on the client device.** Thorpe couples a governed, offline-capable local repair engine with an AI that only narrates repairs already executed and recorded.

---

## Field of the invention

Computer systems diagnostics, automated remediation, and AI-assisted technical support on end-user desktops and laptops across Windows, macOS, and Linux.

---

## Problems in the prior art

### 1. Chat-only support (no local execution)

Traditional IT chatbots and virtual assistants tell users to open Settings, run terminal commands, or reboot. They do not execute OS-level diagnostics or repairs on the device. The user must interpret and perform every step manually.

### 2. Cloud dependency

Most AI support tools require continuous cloud connectivity. When the network is down—the very condition users often need help with—cloud AI cannot assist with local diagnostics or remediation.

### 3. No verification of outcomes

Existing tools do not prove that a suggested or attempted fix improved system health. There is no structured before/after health verification tied to the support interaction.

### 4. Conflation of AI text with system changes

In conventional LLM-based support, the model may describe actions it did not perform. Users cannot distinguish between a recommendation and an executed repair. This creates trust, liability, and safety risks.

### 5. Unsafe autonomous agents

General-purpose LLM tool-use agents can invoke arbitrary or hallucinated commands. There is no cryptographic allowlist governing which OS-level actions an AI may run on an endpoint.

### 6. Reactive-only support

Most consumer and SMB support is user-initiated. Proactive monitoring (CPU, memory, disk) is typically siloed in MSP/RMM tools—not integrated into the same conversational repair pipeline the end user interacts with.

### 7. Fragmented network troubleshooting

Network problems are often addressed with disconnected utilities or generic advice. There is no unified, offline-capable connectivity diagnostic suite fused into a single agent incident response.

### 8. Lack of enterprise governance

Consumer AI assistants lack role-based controls, repair-pack signing, audit trails, and policy-governed separation between planning AI and narration AI.

---

## How Thorpe Desktop solves these problems

| Problem | Thorpe / Jonathan solution |
|---------|---------------------------|
| Manual chat-only support | Executes local diagnostics and repairs (connectivity suite, DNS flush, temp cleanup, resource analysis, disk analysis, etc.) |
| Cloud dependency | Core diagnostics, repair execution, and local narrative operate **offline**; cloud LLM is optional |
| No fix verification | After mutating repairs, runs a **follow-up health scan** and reports before/after metrics in the structured response |
| AI invents fixes in text | **Execute-then-narrate:** repairs complete **before** narrative generation; AI constrained to executed repairs only |
| Unsafe autonomous execution | **Mutating** actions require explicit user approval; safe diagnostics run automatically |
| Uncontrolled tool invocation | Repair actions filtered by **cryptographically signed repair-pack allowlist** |
| Reactive-only support | **Proactive Watchdog** monitors CPU, memory, and disk; alerts hand off into the same incident pipeline |
| Fragmented troubleshooting | **Offline connectivity suite** fuses layered network diagnostics into one agent response |
| No audit trail | Collects system evidence, persists incident sessions, optional PSA/webhook escalation |

---

## Technical architecture (summary)

Jonathan implements a local-first incident pipeline:

```
User message → Evidence collection → Security gate → Offline connectivity (if applicable)
→ Repair planning (LLM JSON or rules) → Repair-pack allowlist filter → Confirmation gate
→ Local OS repair execution → Post-mutating verification scan → Session persistence
→ Narrative generation (local template or cloud LLM) → Structured chat response
```

**Key invariant:** Cloud LLM failure does not prevent repairs from having already executed locally.

**Primary code reference:** `orchestrate_incident` in `src-tauri/src/agent/mod.rs`

---

## Commercial and user problems solved

**End users without IT staff** — Natural-language fix for “Wi-Fi not working” or “computer is slow” without a help desk or MSP.

**Small businesses** — Reduces paid IT visits for routine maintenance and provides documented, verifiable remediation.

**MSP / enterprise (adjacent)** — Optional PSA webhook escalation; governed AI with feature and policy controls rather than unconstrained autonomous agents.

---

## Recommended patent focus

| Priority | Application | Description |
|----------|-------------|-------------|
| **P0** | Patent A — Core orchestration | Execute-then-narrate autonomous IT incident pipeline on client device |
| **P0** | Patent B — Repair packs | Cryptographically signed allowlist gates which OS tools AI may run |
| **P0** | Patent C — Offline connectivity | Layered network diagnostics fused into agent; no cloud required |
| **P1** | Patent D — Watchdog handoff | Background monitor hands alerts into same agent pipeline |
| **P1** | Patent E — Dual LLM | Separate planner and narrator LLMs with independent fallbacks |

---

## One-sentence invention statement

Thorpe Desktop solves the problem that AI IT assistants recommend fixes they never perform, cannot verify, and cannot safely execute locally—by coupling a governed, offline-capable repair engine on the client device with an AI that only narrates repairs already executed and verified.

---

## Related documents in this package

- `01-INVENTION-DISCLOSURE-JONATHAN.md` — Full technical disclosure  
- `02-PATENT-CANDIDATE-INVENTORY.md` — Patent applications A–H  
- `04-CLAIM-SEEDS-FOR-ATTORNEY.md` — Seed claims for drafting  
- `05-PRIOR-ART-DIFFERENTIATION.md` — Prior-art categories and differentiation  
- `07-EXECUTIVE-BRIEF-ONE-PAGE.md` — One-page summary  

**Applicant / assignee:** _[Complete Document 06 before filing]_
