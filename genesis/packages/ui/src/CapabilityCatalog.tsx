import type { Capability } from "@genesis/sdk";

type CapabilityCatalogProps = {
  capabilities: Capability[];
};

export function CapabilityCatalog({ capabilities }: CapabilityCatalogProps) {
  if (!capabilities.length) {
    return <p className="g-muted">No capabilities registered.</p>;
  }

  return (
    <div className="g-catalog">
      {capabilities.map((cap) => (
        <article key={cap.id} className="g-catalog-item">
          <h3>{cap.name}</h3>
          <p className="g-small">{cap.description || cap.id}</p>
          <dl className="g-meta">
            <div>
              <dt>Risk</dt>
              <dd>{cap.risk_level}</dd>
            </div>
            <div>
              <dt>Connector</dt>
              <dd>{cap.connector}</dd>
            </div>
          </dl>
          <span className={`g-badge g-badge-${cap.status}`}>{cap.status}</span>
        </article>
      ))}
    </div>
  );
}
