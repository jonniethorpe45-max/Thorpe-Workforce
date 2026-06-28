import { clsx } from "clsx";

interface ThorpeLogoProps {
  variant?: "horizontal" | "stacked" | "icon";
  className?: string;
  showTagline?: boolean;
}

export function ThorpeLogo({
  variant = "horizontal",
  className,
  showTagline = true,
}: ThorpeLogoProps) {
  if (variant === "icon") {
    return (
      <img
        src="/brand/thorpe-shield.svg"
        alt="Thorpe"
        className={clsx("h-9 w-9", className)}
      />
    );
  }

  if (variant === "stacked") {
    return (
      <img
        src="/brand/thorpe-logo-stacked.svg"
        alt="Thorpe — Your AI IT Technician"
        className={clsx("h-[4.5rem] w-auto", className)}
      />
    );
  }

  if (!showTagline) {
    return (
      <div className={clsx("flex items-center gap-3", className)}>
        <img src="/brand/thorpe-shield.svg" alt="Thorpe" className="h-10 w-10 shrink-0" />
        <p className="font-display text-base font-bold tracking-[0.14em] text-white">THORPE</p>
      </div>
    );
  }

  return (
    <img
      src="/brand/thorpe-logo-horizontal.svg"
      alt="Thorpe — Your AI IT Technician"
      className={clsx("h-10 w-auto max-w-[220px]", className)}
    />
  );
}
