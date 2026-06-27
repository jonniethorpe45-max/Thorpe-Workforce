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
      <div className={clsx("flex flex-col items-center gap-2", className)}>
        <img src="/brand/thorpe-shield.svg" alt="Thorpe" className="h-12 w-12" />
        <div className="text-center">
          <p className="font-display text-lg font-extrabold tracking-[0.14em] text-white">
            THORPE
          </p>
          {showTagline && (
            <p className="mt-0.5 text-[10px] font-semibold tracking-[0.2em] text-thorpe-primary">
              YOUR AI IT TECHNICIAN
            </p>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className={clsx("flex items-center gap-3", className)}>
      <img src="/brand/thorpe-shield.svg" alt="Thorpe" className="h-10 w-10 shrink-0" />
      <div className="min-w-0">
        <p className="font-display text-base font-extrabold tracking-[0.12em] text-white">
          THORPE
        </p>
        {showTagline && (
          <p className="text-[10px] font-semibold tracking-[0.18em] text-thorpe-primary">
            YOUR AI IT TECHNICIAN
          </p>
        )}
      </div>
    </div>
  );
}
