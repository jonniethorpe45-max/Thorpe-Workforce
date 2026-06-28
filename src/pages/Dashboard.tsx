import { motion } from "framer-motion";
import { Link } from "react-router-dom";
import { clsx } from "clsx";
import type { LucideIcon } from "lucide-react";
import {
  Scan,
  Wrench,
  FileText,
  ArrowRight,
  Activity,
  HardDrive,
  Cpu,
  AlertCircle,
  Clock,
  RefreshCw,
  CheckCircle2,
  MessageSquare,
  CreditCard,
} from "lucide-react";
import { useEffect, useState } from "react";
import { HealthScoreRing } from "../components/ui/HealthScoreRing";
import { JonathanAvatar } from "../components/brand/JonathanAvatar";
import { BrandIcon } from "../components/brand/BrandIcon";
import { thorpeApi } from "../services/tauri";
import { useAppStore } from "../services/store";
import { extractFirstName } from "../lib/userName";

function healthLabel(score: number) {
  if (score >= 90) return { text: "Excellent", color: "text-success" };
  if (score >= 75) return { text: "Good", color: "text-cyber-teal" };
  if (score >= 60) return { text: "Fair", color: "text-warning" };
  return { text: "Needs attention", color: "text-orange-400" };
}

export function Dashboard() {
  const { lastScan, setLastScan, license } = useAppStore();
  const [loading, setLoading] = useState(true);
  const [firstName, setFirstName] = useState<string | null>(null);

  useEffect(() => {
    thorpeApi.getProfile().then((profile) => setFirstName(extractFirstName(profile.display_name))).catch(console.error);
  }, []);

  useEffect(() => {
    thorpeApi
      .getLastScan()
      .then((scan) => {
        if (scan) setLastScan(scan);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [setLastScan]);

  const healthScore = lastScan?.health_score ?? null;
  const health = healthScore !== null ? healthLabel(healthScore) : null;
  const issueCount = lastScan?.issues.length ?? 0;

  const recentActivity = lastScan
    ? [
        {
          icon: CheckCircle2,
          color: "text-success",
          text: `System scan completed — health score ${lastScan.health_score}/100`,
          time: new Date(lastScan.timestamp).toLocaleString(),
        },
        ...lastScan.issues.slice(0, 2).map((issue) => ({
          icon: AlertCircle,
          color:
            issue.severity === "critical" || issue.severity === "high"
              ? "text-warning"
              : "text-steel",
          text: issue.title,
          time: "From last scan",
        })),
      ]
    : [];

  return (
    <div className="space-y-6 animate-fade-in">
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        className="card-brand relative overflow-hidden"
      >
        <div className="absolute -right-8 -top-8 h-40 w-40 rounded-full bg-thorpe-primary/10 blur-3xl" />
        <div className="relative flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-start gap-4">
            <JonathanAvatar size="lg" />
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.2em] text-thorpe-primary">
                AI Technician
              </p>
              <h1 className="mt-1 font-display text-2xl font-bold text-white sm:text-3xl">
                {firstName ? `Welcome back, ${firstName}!` : "Welcome back!"}
              </h1>
              <p className="mt-2 max-w-xl text-sm leading-relaxed text-steel">
                Hi{firstName ? ` ${firstName}` : ""}, I&apos;m{" "}
                <span className="font-display font-bold tracking-[0.06em] text-slate-200">Jonathan</span>.
                I&apos;m here to help you understand and fix your technology.
              </p>
            </div>
          </div>
          <Link to="/scanner" className="btn-primary shrink-0 self-start sm:self-center">
            <Scan className="h-4 w-4" />
            Start New Scan
          </Link>
        </div>
      </motion.div>

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.05 }}
          className="stat-card"
        >
          <div className="flex items-center justify-between">
            <BrandIcon icon={Activity} variant="success" />
            {loading && (
              <div className="h-5 w-5 animate-spin rounded-full border-2 border-thorpe-primary border-t-transparent" />
            )}
          </div>
          <p className="mt-3 text-xs font-medium uppercase tracking-wider text-steel">
            System Health
          </p>
          {healthScore !== null && health ? (
            <>
              <p className="font-display text-3xl font-bold text-white">{healthScore}</p>
              <p className={`text-sm font-medium ${health.color}`}>{health.text}</p>
            </>
          ) : (
            <>
              <p className="font-display text-3xl font-bold text-steel">—</p>
              <p className="text-sm text-steel">Run a scan to check</p>
            </>
          )}
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="stat-card"
        >
          <BrandIcon icon={AlertCircle} variant="warning" />
          <p className="mt-3 text-xs font-medium uppercase tracking-wider text-steel">Open Issues</p>
          <p className="font-display text-3xl font-bold text-white">{issueCount}</p>
          <p className={`text-sm font-medium ${issueCount > 0 ? "text-warning" : "text-success"}`}>
            {issueCount > 0 ? "Needs attention" : "All clear"}
          </p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.15 }}
          className="stat-card"
        >
          <BrandIcon icon={Clock} variant="teal" />
          <p className="mt-3 text-xs font-medium uppercase tracking-wider text-steel">Last Scan</p>
          <p className="font-display text-lg font-bold text-white">
            {lastScan
              ? new Date(lastScan.timestamp).toLocaleDateString(undefined, {
                  month: "short",
                  day: "numeric",
                })
              : "Never"}
          </p>
          <p className="text-sm text-steel">
            {lastScan
              ? new Date(lastScan.timestamp).toLocaleTimeString(undefined, {
                  hour: "numeric",
                  minute: "2-digit",
                })
              : "No scan data yet"}
          </p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="stat-card"
        >
          <BrandIcon icon={RefreshCw} variant="primary" />
          <p className="mt-3 text-xs font-medium uppercase tracking-wider text-steel">Updates</p>
          <p className="font-display text-3xl font-bold text-white">
            {lastScan?.updates_available ? "!" : "✓"}
          </p>
          <p className="text-sm text-steel">
            {lastScan?.updates_available ? "Updates available" : "Up to date"}
          </p>
        </motion.div>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.25 }}
          className="card flex flex-col items-center justify-center py-6 lg:col-span-1"
        >
          <h2 className="mb-4 self-start text-xs font-semibold uppercase tracking-wider text-steel">
            Health Overview
          </h2>
          {loading ? (
            <div className="flex h-40 items-center justify-center">
              <div className="h-8 w-8 animate-spin rounded-full border-2 border-thorpe-primary border-t-transparent" />
            </div>
          ) : lastScan ? (
            <>
              <HealthScoreRing score={lastScan.health_score} size="lg" />
              <p className="mt-4 text-center text-sm text-steel">
                Last scanned {new Date(lastScan.timestamp).toLocaleString()}
              </p>
              <Link to="/scanner" className="btn-secondary mt-4 text-xs">
                Run New Scan <ArrowRight className="h-3 w-3" />
              </Link>
            </>
          ) : (
            <div className="flex flex-col items-center gap-4 py-4">
              <BrandIcon icon={Activity} variant="primary" className="!h-14 !w-14 [&_svg]:!h-7 [&_svg]:!w-7" />
              <p className="text-center text-sm text-steel">No scan data yet</p>
              <Link to="/scanner" className="btn-primary text-sm">
                Run Your First Scan
              </Link>
            </div>
          )}
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="card lg:col-span-2"
        >
          <h2 className="mb-4 text-xs font-semibold uppercase tracking-wider text-steel">
            Recent Activity
          </h2>
          {recentActivity.length > 0 ? (
            <div className="space-y-3">
              {recentActivity.map((item, i) => (
                <div
                  key={i}
                  className="flex items-start gap-3 rounded-xl border border-navy-border bg-navy-light/50 p-3"
                >
                  <item.icon className={clsx("mt-0.5 h-4 w-4 shrink-0", item.color)} />
                  <div className="min-w-0 flex-1">
                    <p className="text-sm text-slate-200">{item.text}</p>
                    <p className="text-xs text-steel">{item.time}</p>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="rounded-xl border border-dashed border-navy-border py-10 text-center">
              <p className="text-sm text-steel">Run a system scan to see recent activity.</p>
              <Link to="/scanner" className="btn-primary mt-4 inline-flex text-sm">
                Start Scan
              </Link>
            </div>
          )}
        </motion.div>
      </div>

      {lastScan && (
        <div className="grid gap-4 sm:grid-cols-3">
          <SystemStatCard
            icon={Cpu}
            label="CPU Usage"
            value={`${lastScan.cpu.usage_percent.toFixed(1)}%`}
            sub={lastScan.cpu.brand}
          />
          <SystemStatCard
            icon={Activity}
            label="Memory"
            value={`${lastScan.memory.usage_percent.toFixed(1)}%`}
            sub={`${lastScan.memory.used_gb} / ${lastScan.memory.total_gb} GB`}
          />
          <SystemStatCard
            icon={HardDrive}
            label="Storage"
            value={`${lastScan.disks[0]?.usage_percent.toFixed(1) ?? 0}%`}
            sub={`${lastScan.disks[0]?.available_gb ?? 0} GB free`}
          />
        </div>
      )}

      {lastScan && lastScan.issues.length > 0 && (
        <div className="card">
          <h2 className="mb-4 text-xs font-semibold uppercase tracking-wider text-steel">
            Detected Issues
          </h2>
          <div className="space-y-3">
            {lastScan.issues.slice(0, 5).map((issue) => (
              <div
                key={issue.id}
                className="flex items-start gap-3 rounded-xl border border-navy-border bg-navy-light/40 p-3"
              >
                <div
                  className={clsx(
                    "mt-1 h-2 w-2 shrink-0 rounded-full",
                    issue.severity === "critical"
                      ? "bg-red-500"
                      : issue.severity === "high"
                        ? "bg-warning"
                        : issue.severity === "medium"
                          ? "bg-yellow-400"
                          : "bg-success"
                  )}
                />
                <div>
                  <p className="text-sm font-medium text-slate-200">{issue.title}</p>
                  <p className="text-xs text-steel">{issue.description}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        {[
          { to: "/jonathan", icon: MessageSquare, label: "Ask Jonathan", variant: "primary" as const },
          { to: "/repairs", icon: Wrench, label: "Repair Center", variant: "warning" as const },
          { to: "/reports", icon: FileText, label: "View Reports", variant: "teal" as const },
          {
            to: "/licensing",
            icon: CreditCard,
            label: license?.tier_display ?? "Free Plan",
            variant: "neutral" as const,
          },
        ].map(({ to, icon, label, variant }) => (
          <Link
            key={to}
            to={to}
            className="card flex items-center gap-3 transition-all hover:border-thorpe-primary/30"
          >
            <BrandIcon icon={icon} variant={variant} />
            <span className="font-medium text-slate-200">{label}</span>
            <ArrowRight className="ml-auto h-4 w-4 text-steel" />
          </Link>
        ))}
      </div>
    </div>
  );
}

function SystemStatCard({
  icon,
  label,
  value,
  sub,
}: {
  icon: LucideIcon;
  label: string;
  value: string;
  sub: string;
}) {
  return (
    <div className="card flex items-center gap-4">
      <BrandIcon icon={icon} variant="primary" />
      <div>
        <p className="text-xs font-medium uppercase tracking-wider text-steel">{label}</p>
        <p className="font-display text-xl font-bold text-white">{value}</p>
        <p className="text-xs text-steel">{sub}</p>
      </div>
    </div>
  );
}
