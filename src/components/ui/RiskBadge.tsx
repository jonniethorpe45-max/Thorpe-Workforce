import { clsx } from "clsx";

const variants = {
  low: "badge-low",
  medium: "badge-medium",
  high: "badge-high",
  critical: "badge-critical",
};

interface RiskBadgeProps {
  level: string;
  className?: string;
}

export function RiskBadge({ level, className }: RiskBadgeProps) {
  const normalized = level.toLowerCase() as keyof typeof variants;
  return (
    <span className={clsx(variants[normalized] || "badge bg-gray-500/15 text-gray-400", className)}>
      {level}
    </span>
  );
}
