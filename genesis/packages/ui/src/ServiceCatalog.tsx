import type { ServiceInfo } from "@genesis/sdk";

type ServiceCatalogProps = {
  services: ServiceInfo[];
};

export function ServiceCatalog({ services }: ServiceCatalogProps) {
  if (!services.length) {
    return <p className="g-muted">No services registered.</p>;
  }

  return (
    <div className="g-catalog">
      {services.map((service) => (
        <article key={service.id} className="g-catalog-item">
          <h3>{service.name}</h3>
          <p className="g-small">
            {service.id} · port {service.port}
          </p>
          <span className={`g-badge g-badge-${service.status}`}>{service.status}</span>
        </article>
      ))}
    </div>
  );
}
