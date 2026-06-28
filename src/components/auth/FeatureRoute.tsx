import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Shield } from "lucide-react";
import { thorpeApi } from "../../services/tauri";

interface FeatureRouteProps {
  feature: string;
  title: string;
  description: string;
  children: React.ReactNode;
}

export function FeatureRoute({ feature, title, description, children }: FeatureRouteProps) {
  const [allowed, setAllowed] = useState<boolean | null>(null);

  useEffect(() => {
    thorpeApi.checkFeature(feature).then((f) => setAllowed(f.allowed)).catch(() => setAllowed(false));
  }, [feature]);

  if (allowed === null) {
    return <div className="animate-pulse text-steel">Checking license…</div>;
  }

  if (!allowed) {
    return (
      <div className="card mx-auto max-w-lg p-8 text-center">
        <Shield className="mx-auto mb-4 h-12 w-12 text-steel" />
        <h1 className="text-xl font-bold text-white">{title}</h1>
        <p className="mt-2 text-sm text-steel">{description}</p>
        <Link to="/licensing" className="btn-primary mt-6 inline-block text-sm">
          View licensing
        </Link>
      </div>
    );
  }

  return <>{children}</>;
}
