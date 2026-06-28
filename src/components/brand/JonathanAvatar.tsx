import { clsx } from "clsx";

interface JonathanAvatarProps {
  size?: "sm" | "md" | "lg" | "xl";
  className?: string;
  showRing?: boolean;
}

const sizes = {
  sm: "h-8 w-8",
  md: "h-12 w-12",
  lg: "h-16 w-16",
  xl: "h-24 w-24",
};

export function JonathanAvatar({
  size = "md",
  className,
  showRing = true,
}: JonathanAvatarProps) {
  return (
    <div
      className={clsx(
        "relative shrink-0 rounded-full",
        showRing &&
          "bg-gradient-to-br from-thorpe-primary to-cyber-teal p-[2px] shadow-brand",
        className
      )}
    >
      <img
        src="/brand/jonathan-avatar.svg"
        alt="Jonathan, AI Technician"
        className={clsx("rounded-full object-cover bg-navy", sizes[size])}
      />
    </div>
  );
}
