import type { Approval } from "@genesis/sdk";

type ApprovalCardProps = {
  approval: Approval;
  onApprove?: (approvalId: string) => Promise<void> | void;
  onExecute?: (approvalId: string) => Promise<void> | void;
  busy?: boolean;
};

export function ApprovalCard({ approval, onApprove, onExecute, busy }: ApprovalCardProps) {
  return (
    <article className="g-approval-card" data-status={approval.status}>
      <header className="g-approval-card__header">
        <h3>Approval</h3>
        <span className={`g-badge g-badge-${approval.status}`}>{approval.status}</span>
      </header>
      <p className="g-muted">{approval.intent.summary}</p>
      <dl className="g-meta">
        <div>
          <dt>Capability</dt>
          <dd>{approval.intent.capability || "none"}</dd>
        </div>
        <div>
          <dt>Risk</dt>
          <dd>{approval.policy.risk_level}</dd>
        </div>
        <div>
          <dt>Policy</dt>
          <dd>{approval.policy.decision}</dd>
        </div>
      </dl>
      <p className="g-small">{approval.policy.reason}</p>
      <div className="g-actions">
        {approval.status === "pending" && onApprove ? (
          <button
            className="g-button g-button-primary"
            type="button"
            disabled={busy}
            onClick={() => onApprove(approval.id)}
          >
            Approve
          </button>
        ) : null}
        {approval.status === "approved" && onExecute ? (
          <button
            className="g-button g-button-primary"
            type="button"
            disabled={busy}
            onClick={() => onExecute(approval.id)}
          >
            Execute
          </button>
        ) : null}
      </div>
    </article>
  );
}
