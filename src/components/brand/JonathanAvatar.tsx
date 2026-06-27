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
        "relative shrink-0",
        showRing && "rounded-2xl bg-gradient-to-br from-thorpe-primary/20 to-cyber-teal/10 p-0.5",
        className
      )}
    >
      <img
        src="/brand/jonathan-avatar.svg"
        alt="Jonathan, AI Technician"
        className={clsx("rounded-2xl object-cover", sizes[size])}
      />
    </div>
  );
}
