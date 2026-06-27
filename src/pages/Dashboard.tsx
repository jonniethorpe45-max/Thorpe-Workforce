import { motion } from "framer-motion";
import { Link } from "react-router-dom";
import {
  MessageSquare,
  Scan,
  Wrench,
  FileText,
  ArrowRight,
  Activity,
  HardDrive,
  Cpu,
} from "lucide-react";
import { useEffect, useState } from "react";
import { HealthScoreRing } from "../components/ui/HealthScoreRing";
import { thorpeApi } from "../services/tauri";
import { useAppStore } from "../services/store";

export function Dashboard() {
  const { lastScan, setLastScan, license } = useAppStore();
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    thorpeApi
      .getLastScan()
      .then((scan) => {
        if (scan) setLastScan(scan);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [setLastScan]);

  const quickActions = [
    { to: "/jonathan", icon: MessageSquare, label: "Ask Jonathan", color: "bg-thorpe-600/20 text-thorpe-400" },
    { to: "/scanner", icon: Scan, label: "Run Scan", color: "bg-green-600/20 text-green-400" },
    { to: "/repairs", icon: Wrench, label: "Repair Center", color: "bg-orange-600/20 text-orange-400" },
    { to: "/reports", icon: FileText, label: "View Reports", color: "bg-purple-600/20 text-purple-400" },
  ];

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold text-white">Dashboard</h1>
        <p className="mt-1 text-gray-400">
          Welcome to Thorpe. Your AI-powered IT support platform.
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          className="card lg:col-span-1"
        >
          <h2 className="mb-4 text-sm font-medium text-gray-400">System Health</h2>
          {loading ? (
            <div className="flex h-40 items-center justify-center">
              <div className="h-8 w-8 animate-spin rounded-full border-2 border-thorpe-500 border-t-transparent" />
            </div>
          ) : lastScan ? (
            <div className="flex flex-col items-center gap-4">
              <HealthScoreRing score={lastScan.health_score} />
              <p className="text-center text-sm text-gray-400">
                Last scanned {new Date(lastScan.timestamp).toLocaleString()}
              </p>
              <Link to="/scanner" className="btn-secondary text-xs">
                Run New Scan <ArrowRight className="h-3 w-3" />
              </Link>
            </div>
          ) : (
            <div className="flex flex-col items-center gap-4 py-6">
              <Activity className="h-12 w-12 text-gray-600" />
              <p className="text-center text-sm text-gray-400">No scan data yet</p>
              <Link to="/scanner" className="btn-primary text-sm">
                Run Your First Scan
              </Link>
            </div>
          )}
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="card lg:col-span-2"
        >
          <h2 className="mb-4 text-sm font-medium text-gray-400">Quick Actions</h2>
          <div className="grid gap-3 sm:grid-cols-2">
            {quickActions.map(({ to, icon: Icon, label, color }) => (
              <Link
                key={to}
                to={to}
                className="flex items-center gap-4 rounded-lg border border-surface-border bg-surface p-4 transition-all hover:border-thorpe-500/30 hover:bg-surface-overlay"
              >
                <div className={`rounded-lg p-3 ${color}`}>
                  <Icon className="h-5 w-5" />
                </div>
                <span className="font-medium text-gray-200">{label}</span>
                <ArrowRight className="ml-auto h-4 w-4 text-gray-500" />
              </Link>
            ))}
          </div>
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
          <h2 className="mb-4 text-sm font-medium text-gray-400">Recent Issues</h2>
          <div className="space-y-3">
            {lastScan.issues.slice(0, 5).map((issue) => (
              <div
                key={issue.id}
                className="flex items-start gap-3 rounded-lg border border-surface-border bg-surface p-3"
              >
                <div
                  className={`mt-0.5 h-2 w-2 shrink-0 rounded-full ${
                    issue.severity === "critical"
                      ? "bg-red-500"
                      : issue.severity === "high"
                        ? "bg-orange-500"
                        : issue.severity === "medium"
                          ? "bg-yellow-500"
                          : "bg-green-500"
                  }`}
                />
                <div>
                  <p className="text-sm font-medium text-gray-200">{issue.title}</p>
                  <p className="text-xs text-gray-400">{issue.description}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="card flex items-center justify-between">
        <div>
          <p className="text-sm text-gray-400">License</p>
          <p className="text-lg font-semibold text-white">
            {license?.tier_display ?? "Free"} Plan
          </p>
        </div>
        <Link to="/licensing" className="btn-secondary text-sm">
          Manage License
        </Link>
      </div>
    </div>
  );
}

function SystemStatCard({
  icon: Icon,
  label,
  value,
  sub,
}: {
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  value: string;
  sub: string;
}) {
  return (
    <div className="card flex items-center gap-4">
      <div className="rounded-lg bg-surface p-3">
        <Icon className="h-5 w-5 text-thorpe-400" />
      </div>
      <div>
        <p className="text-xs text-gray-400">{label}</p>
        <p className="text-xl font-bold text-white">{value}</p>
        <p className="text-xs text-gray-500">{sub}</p>
      </div>
    </div>
  );
}
