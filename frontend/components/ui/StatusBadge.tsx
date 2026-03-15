import clsx from "clsx";

type Props = {
  status: string;
};

export function StatusBadge({ status }: Props) {
  const lowered = status.toLowerCase();
  const pretty = status.replaceAll("_", " ");
  return (
    <span
      className={clsx(
        "inline-flex rounded-full border px-2 py-1 text-xs font-medium backdrop-blur-sm",
        lowered.includes("active") || lowered.includes("interested") || lowered.includes("booked")
          ? "border-emerald-400/40 bg-emerald-500/15 text-emerald-200"
          : lowered.includes("paused") || lowered.includes("pending")
            ? "border-amber-400/40 bg-amber-500/15 text-amber-200"
            : lowered.includes("error") || lowered.includes("rejected") || lowered.includes("lost")
              ? "border-rose-400/40 bg-rose-500/15 text-rose-200"
              : "border-slate-400/35 bg-slate-700/25 text-slate-200"
      )}
    >
      {pretty}
    </span>
  );
}
