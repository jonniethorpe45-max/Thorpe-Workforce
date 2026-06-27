import { clsx } from "clsx";

interface HealthScoreRingProps {
  score: number;
  size?: "sm" | "md" | "lg";
}

export function HealthScoreRing({ score, size = "md" }: HealthScoreRingProps) {
  const dimensions = { sm: 80, md: 120, lg: 160 };
  const dim = dimensions[size];
  const stroke = size === "sm" ? 6 : 8;
  const radius = (dim - stroke) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (score / 100) * circumference;

  const color =
    score >= 80 ? "#22C55E" : score >= 60 ? "#F59E0B" : score >= 40 ? "#F97316" : "#EF4444";

  const trackColor = "#1E3A5F";

  const labelSize = size === "sm" ? "text-lg" : size === "md" ? "text-2xl" : "text-3xl";

  return (
    <div className="relative inline-flex items-center justify-center">
      <svg width={dim} height={dim} className="-rotate-90">
        <circle
          cx={dim / 2}
          cy={dim / 2}
          r={radius}
          fill="none"
          stroke={trackColor}
          strokeWidth={stroke}
        />
        <circle
          cx={dim / 2}
          cy={dim / 2}
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth={stroke}
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          strokeLinecap="round"
          className="transition-all duration-1000 ease-out"
        />
      </svg>
      <div className="absolute flex flex-col items-center">
        <span className={clsx("font-bold text-white", labelSize)}>{score}</span>
        <span className="text-xs text-gray-400">/ 100</span>
      </div>
    </div>
  );
}
