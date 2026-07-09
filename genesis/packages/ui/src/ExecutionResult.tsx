import type { ExecuteResult, IntentResult } from "@genesis/sdk";

type ExecutionResultProps = {
  intentResult?: IntentResult | null;
  executeResult?: ExecuteResult | null;
};

export function ExecutionResult({ intentResult, executeResult }: ExecutionResultProps) {
  if (!intentResult && !executeResult) {
    return <p className="g-muted">No execution result yet.</p>;
  }

  return (
    <section className="g-execution-result">
      {intentResult ? (
        <>
          <h3>Intent result</h3>
          <p>{intentResult.explanation}</p>
          <dl className="g-meta">
            <div>
              <dt>Status</dt>
              <dd>{intentResult.execution.status}</dd>
            </div>
            <div>
              <dt>Policy</dt>
              <dd>{intentResult.policy.decision}</dd>
            </div>
            <div>
              <dt>Approval</dt>
              <dd>{intentResult.execution.approval_id || "—"}</dd>
            </div>
          </dl>
          <ol className="g-plan">
            {intentResult.plan.steps.map((step) => (
              <li key={step.id}>{step.description}</li>
            ))}
          </ol>
        </>
      ) : null}
      {executeResult ? (
        <>
          <h3>Execution</h3>
          <p>{executeResult.explanation}</p>
          <pre className="g-code">{JSON.stringify(executeResult.execution, null, 2)}</pre>
        </>
      ) : null}
    </section>
  );
}
