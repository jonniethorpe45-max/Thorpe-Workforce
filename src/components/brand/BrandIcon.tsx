import { clsx } from "clsx";
import type { LucideIcon } from "lucide-react";

interface BrandIconProps {
  icon: LucideIcon;
  variant?: "primary" | "teal" | "success" | "warning" | "neutral";
  className?: string;
}

const variants = {
  primary: "bg-thorpe-primary/15 text-thorpe-primary border-thorpe-primary/25",
  teal: "bg-cyber-teal/15 text-cyber-teal border-cyber-teal/25",
  success: "bg-success/15 text-success border-success/25",
  warning: "bg-warning/15 text-warning border-warning/25",
  neutral: "bg-steel/15 text-steel border-steel/25",
};

export function BrandIcon({ icon: Icon, variant = "primary", className }: BrandIconProps) {
  return (
    <div
      className={clsx(
        "flex h-10 w-10 items-center justify-center rounded-xl border",
        variants[variant],
        className
      )}
    >
      <Icon className="h-5 w-5" strokeWidth={1.75} />
    </div>
  );
}
