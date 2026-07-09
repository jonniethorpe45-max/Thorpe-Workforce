import { useMemo, useState } from "react";
import {
  createGenesisClient,
  type Approval,
  type AuditEvent,
  type Capability,
  type ServiceInfo,
} from "@genesis/sdk";
import {
  ApprovalCard,
  AuditEventList,
  CapabilityCatalog,
  ServiceCatalog,
} from "@genesis/ui";

const GATEWAY_URL = import.meta.env.VITE_GATEWAY_URL || "http://localhost:7999";

type Tab = "approvals" | "audit" | "services" | "capabilities";

export default function App() {
  const client = useMemo(() => createGenesisClient({ gatewayUrl: GATEWAY_URL }), []);
  const [tab, setTab] = useState<Tab>("approvals");
  const [approvals, setApprovals] = useState<Approval[]>([]);
  const [audit, setAudit] = useState<AuditEvent[]>([]);
  const [services, setServices] = useState<ServiceInfo[]>([]);
  const [capabilities, setCapabilities] = useState<Capability[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function load() {
    setBusy(true);
    setError(null);
    try {
      const [a, au, s, c] = await Promise.all([
        client.approvals(),
        client.audit(),
        client.services(),
        client.capabilities(),
      ]);
      setApprovals(a);
      setAudit(au);
      setServices(s);
      setCapabilities(c);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load admin data");
    } finally {
      setBusy(false);
    }
  }

  async function handleApprove(approvalId: string) {
    setBusy(true);
    try {
      await client.approve(approvalId);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Approve failed");
      setBusy(false);
    }
  }

  async function handleExecute(approvalId: string) {
    setBusy(true);
    try {
      await client.execute(approvalId);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Execute failed");
      setBusy(false);
    }
  }

  return (
    <div className="g-shell">
      <header>
        <p className="g-small">Genesis Platform</p>
        <h1 className="g-brand">Admin Console</h1>
        <p className="g-tagline">
          Gateway-first operations view for approvals, audit, services, and capabilities. Policy and
          audit are never bypassed.
        </p>
        <div className="g-actions">
          <button className="g-button g-button-primary" type="button" onClick={load} disabled={busy}>
            {busy ? "Loading…" : "Refresh via gateway"}
          </button>
        </div>
        {error ? <p className="g-error">{error}</p> : null}
      </header>

      <div className="g-tabs" role="tablist">
        {(
          [
            ["approvals", "Approvals"],
            ["audit", "Audit"],
            ["services", "Services"],
            ["capabilities", "Capabilities"],
          ] as const
        ).map(([id, label]) => (
          <button
            key={id}
            className="g-tab"
            type="button"
            role="tab"
            aria-selected={tab === id}
            onClick={() => setTab(id)}
          >
            {label}
          </button>
        ))}
      </div>

      <section className="g-panel">
        {tab === "approvals" ? (
          approvals.length ? (
            approvals.map((item) => (
              <ApprovalCard
                key={item.id}
                approval={item}
                onApprove={handleApprove}
                onExecute={handleExecute}
                busy={busy}
              />
            ))
          ) : (
            <p className="g-muted">No approvals loaded. Click refresh.</p>
          )
        ) : null}
        {tab === "audit" ? <AuditEventList events={audit} /> : null}
        {tab === "services" ? <ServiceCatalog services={services} /> : null}
        {tab === "capabilities" ? <CapabilityCatalog capabilities={capabilities} /> : null}
      </section>
    </div>
  );
}
