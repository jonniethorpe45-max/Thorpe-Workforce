import type { AuditEvent } from "@genesis/sdk";

type AuditEventListProps = {
  events: AuditEvent[];
};

export function AuditEventList({ events }: AuditEventListProps) {
  if (!events.length) {
    return <p className="g-muted">No audit events.</p>;
  }

  return (
    <ul className="g-audit-list">
      {events.map((event) => (
        <li key={event.id} className="g-audit-item">
          <div className="g-audit-item__top">
            <strong>{event.event_type}</strong>
            <time dateTime={event.created_at}>{new Date(event.created_at).toLocaleString()}</time>
          </div>
          <p className="g-small">User: {event.user_id}</p>
          <pre className="g-code">{JSON.stringify(event.payload, null, 2)}</pre>
        </li>
      ))}
    </ul>
  );
}
