import type { ReactNode } from "react";
import { Bot, BriefcaseBusiness, Megaphone, Search, Settings2, Sparkles } from "lucide-react";

type WorkerTemplateCardProps = {
  name: string;
  category: string;
  description: string;
  pricingLabel: string;
  ratingLabel?: string;
  installsLabel?: string;
  tags?: string[];
  isFeatured?: boolean;
  status?: ReactNode;
  footer: ReactNode;
};

function categoryIcon(category: string) {
  const normalized = (category || "").toLowerCase();
  if (normalized.includes("marketing") || normalized.includes("content")) return Megaphone;
  if (normalized.includes("research")) return Search;
  if (normalized.includes("sales")) return BriefcaseBusiness;
  if (normalized.includes("automation") || normalized.includes("operations")) return Settings2;
  return Bot;
}

export function WorkerTemplateCard({
  name,
  category,
  description,
  pricingLabel,
  ratingLabel,
  installsLabel,
  tags,
  isFeatured,
  status,
  footer
}: WorkerTemplateCardProps) {
  const Icon = categoryIcon(category);

  return (
    <article className="card p-4">
      <div className="flex items-start justify-between gap-2">
        <div>
          <h3 className="text-base font-semibold">{name}</h3>
          <p className="mt-1 inline-flex items-center gap-1 text-xs text-slate-500">
            <Icon className="h-3.5 w-3.5 text-cyan-300" />
            {category}
          </p>
        </div>
        {status}
      </div>

      <p className="mt-2 text-sm text-slate-700">{description}</p>

      <div className="mt-3 flex flex-wrap items-center gap-2 text-xs">
        {isFeatured ? (
          <span className="inline-flex items-center gap-1 rounded-full border border-amber-300/35 bg-amber-500/15 px-2 py-1 text-amber-200">
            <Sparkles className="h-3 w-3" />
            Featured
          </span>
        ) : null}
        <span className="chip">{pricingLabel}</span>
        {ratingLabel ? <span className="chip">{ratingLabel}</span> : null}
        {installsLabel ? <span className="chip">{installsLabel}</span> : null}
      </div>

      {tags?.length ? (
        <div className="mt-3 flex flex-wrap gap-1">
          {tags.map((tag) => (
            <span className="chip" key={`${name}-${tag}`}>
              {tag}
            </span>
          ))}
        </div>
      ) : null}

      <div className="mt-4 flex flex-wrap gap-2">{footer}</div>
    </article>
  );
}
