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
        "inline-flex rounded-full px-2 py-1 text-xs font-medium",
        lowered.includes("active") || lowered.includes("interested") || lowered.includes("booked")
          ? "bg-emerald-50 text-emerald-700"
          : lowered.includes("paused") || lowered.includes("pending")
            ? "bg-amber-50 text-amber-700"
            : lowered.includes("error") || lowered.includes("rejected") || lowered.includes("lost")
              ? "bg-rose-50 text-rose-700"
              : "bg-slate-100 text-slate-700"
      )}
    >
      {pretty}
    </span>
  );
}
