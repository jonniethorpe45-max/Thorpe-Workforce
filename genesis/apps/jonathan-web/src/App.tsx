import { useMemo, useState } from "react";
import {
  createGenesisClient,
  type Approval,
  type AuditEvent,
  type ExecuteResult,
  type IntentResult,
} from "@genesis/sdk";
import {
  ApprovalCard,
  AuditEventList,
  ExecutionResult,
  IntentForm,
} from "@genesis/ui";

const GATEWAY_URL = import.meta.env.VITE_GATEWAY_URL || "http://localhost:7999";

export default function App() {
  const client = useMemo(() => createGenesisClient({ gatewayUrl: GATEWAY_URL }), []);
  const [intentResult, setIntentResult] = useState<IntentResult | null>(null);
  const [executeResult, setExecuteResult] = useState<ExecuteResult | null>(null);
  const [approval, setApproval] = useState<Approval | null>(null);
  const [audit, setAudit] = useState<AuditEvent[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function refreshAudit() {
    const events = await client.audit();
    setAudit(events.slice(0, 8));
  }

  async function handleIntent(message: string) {
    setError(null);
    setExecuteResult(null);
    setApproval(null);
    setBusy(true);
    try {
      const result = await client.intent(message);
      setIntentResult(result);
      if (result.execution.approval_id) {
        const approvals = await client.approvals();
        setApproval(approvals.find((item) => item.id === result.execution.approval_id) || null);
      }
      await refreshAudit();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Intent failed");
    } finally {
      setBusy(false);
    }
  }

  async function handleApprove(approvalId: string) {
    setBusy(true);
    setError(null);
    try {
      await client.approve(approvalId);
      const approvals = await client.approvals();
      setApproval(approvals.find((item) => item.id === approvalId) || null);
      await refreshAudit();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Approval failed");
    } finally {
      setBusy(false);
    }
  }

  async function handleExecute(approvalId: string) {
    setBusy(true);
    setError(null);
    try {
      const result = await client.execute(approvalId);
      setExecuteResult(result);
      const approvals = await client.approvals();
      setApproval(approvals.find((item) => item.id === approvalId) || null);
      await refreshAudit();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Execution failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="g-shell">
      <header className="g-hero">
        <p className="g-small">Genesis · Universal Intent Layer</p>
        <h1 className="g-brand">Jonathan</h1>
        <p className="g-tagline">
          Say what you need. Jonathan plans, checks policy, asks for approval when required, then
          executes through the gateway — with a full audit trail.
        </p>
      </header>

      <div className="g-grid g-grid-2">
        <section className="g-panel">
          <IntentForm onSubmit={handleIntent} disabled={busy} />
          {error ? <p className="g-error">{error}</p> : null}
          <ExecutionResult intentResult={intentResult} executeResult={executeResult} />
        </section>

        <section className="g-panel">
          <h2>Approval & audit</h2>
          {approval ? (
            <ApprovalCard
              approval={approval}
              onApprove={handleApprove}
              onExecute={handleExecute}
              busy={busy}
            />
          ) : (
            <p className="g-muted">Submit a medium-risk intent (e.g. schedule a meeting) to create an approval.</p>
          )}
          <h3 style={{ marginTop: "1.25rem" }}>Recent audit</h3>
          <AuditEventList events={audit} />
        </section>
      </div>
    </div>
  );
}
