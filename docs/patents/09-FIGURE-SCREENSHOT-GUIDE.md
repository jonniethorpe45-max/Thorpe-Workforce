# Patent Figure and Screenshot Guide

**Purpose:** Map UI screenshots and diagrams to patent specification figures.

---

## Generated screenshots (`screenshots/`)

| File | Route | Patent figure use | Caption |
|------|-------|-------------------|---------|
| `01-dashboard.png` | `/` | Optional UI context | Thorpe Desktop dashboard with system health summary |
| `02-jonathan-chat-wifi.png` | `/jonathan` | FIG. 6 (UI) | Jonathan assistant after network issue — diagnostics, approval UI |
| `03-jonathan-pending-approval.png` | `/jonathan` | FIG. 7 (UI) | Pending mutating repair approval card with Approve button |
| `04-settings-watchdog.png` | `/settings` | FIG. 8 (UI) | Proactive Watchdog configuration and recent metric alerts |
| `05-repair-center.png` | `/repairs` | Optional | Repair Center with confirmation-gated actions |
| `06-connectivity-report.png` | `/jonathan` | FIG. 9 (UI) | Inline offline connectivity report in chat response |

Screenshots are captured from the web preview (mock backend) at 1280×800 using headless Chrome. Attorney may substitute production Tauri captures for filing.

---

## Mermaid diagrams (convert to line drawings)

From `03-SYSTEM-ARCHITECTURE-AND-FLOWS.md`:

| Figure # | Diagram | Description |
|----------|---------|-------------|
| FIG. 1 | System architecture block | Modules: UI, API, orchestration, AI, DB, OS |
| FIG. 2 | Chat turn sequence | Execute-then-narrate ordering |
| FIG. 3 | Orchestration flowchart | Security, connectivity, plan, filter, verify |
| FIG. 4 | Watchdog handoff sequence | Monitor → notification → Jonathan |
| FIG. 5 | Repair pack gating | Signed manifest → allowlist → execution |

**Conversion:** Export Mermaid to SVG (mermaid.live or `npx @mermaid-js/mermaid-cli`), then simplify to USPTO black-and-white line art per counsel guidance.

---

## Suggested figure order in specification

1. FIG. 1 — System architecture (block diagram)
2. FIG. 2 — Method sequence (chat turn)
3. FIG. 3 — Orchestration flowchart
4. FIG. 4 — Watchdog handoff sequence
5. FIG. 5 — Repair pack allowlist
6. FIG. 6 — Jonathan chat UI (screenshot)
7. FIG. 7 — Repair approval UI (screenshot)
8. FIG. 8 — Watchdog settings (screenshot)
9. FIG. 9 — Connectivity report in chat (screenshot)

---

## Manual capture (Tauri desktop)

If counsel requires native desktop captures:

```bash
npm run tauri:dev
# Navigate to routes above; capture at 1280×800 or 1920×1080
# macOS: Cmd+Shift+4 | Windows: Win+Shift+S
```

Replace files in `docs/patents/screenshots/` with same filenames.
