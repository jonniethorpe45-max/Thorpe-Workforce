import { useState } from "react";
import { motion } from "framer-motion";
import { Scan, Shield, CheckCircle, AlertTriangle, Loader2 } from "lucide-react";
import { HealthScoreRing } from "../components/ui/HealthScoreRing";
import { RiskBadge } from "../components/ui/RiskBadge";
import { thorpeApi } from "../services/tauri";
import { useAppStore } from "../services/store";
import type { SystemScanResult } from "../services/types";

export function SystemScanner() {
  const [scanning, setScanning] = useState(false);
  const [consent, setConsent] = useState(false);
  const [result, setResult] = useState<SystemScanResult | null>(null);
  const { setLastScan, addNotification } = useAppStore();

  const runScan = async () => {
    if (!consent) {
      addNotification({
        type: "warning",
        title: "Consent Required",
        message: "Please consent to system diagnostics before scanning.",
      });
      return;
    }

    setScanning(true);
    try {
      const scan = await thorpeApi.runSystemScan();
      setResult(scan);
      setLastScan(scan);
      addNotification({
        type: "success",
        title: "Scan Complete",
        message: `Health score: ${scan.health_score}/100`,
      });
    } catch (err) {
      addNotification({
        type: "error",
        title: "Scan Failed",
        message: String(err),
      });
    } finally {
      setScanning(false);
    }
  };

  const generateReport = async () => {
    if (!result) return;
    try {
      const report = await thorpeApi.generateReport(result.id);
      addNotification({
        type: "success",
        title: "Report Generated",
        message: report.title,
      });
    } catch (err) {
      addNotification({
        type: "error",
        title: "Report Failed",
        message: String(err),
      });
    }
  };

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold text-white">System Health Scanner</h1>
        <p className="mt-1 text-gray-400">
          Secure diagnostic engine that gathers system information with your consent.
        </p>
      </div>

      <div className="card">
        <div className="flex items-start gap-4">
          <Shield className="mt-1 h-5 w-5 shrink-0 text-thorpe-400" />
          <div className="flex-1">
            <h3 className="font-medium text-white">Privacy & Consent</h3>
            <p className="mt-1 text-sm text-gray-400">
              Thorpe will collect: OS info, CPU, memory, disk usage, network configuration,
              running processes, and startup applications. We never collect personal documents,
              passwords, or browser data.
            </p>
            <label className="mt-3 flex items-center gap-2 text-sm text-gray-300">
              <input
                type="checkbox"
                checked={consent}
                onChange={(e) => setConsent(e.target.checked)}
                className="rounded border-surface-border bg-surface text-thorpe-600 focus:ring-thorpe-500"
              />
              I consent to system diagnostics
            </label>
          </div>
        </div>
      </div>

      <div className="flex gap-3">
        <button onClick={runScan} disabled={scanning || !consent} className="btn-primary">
          {scanning ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin" /> Scanning...
            </>
          ) : (
            <>
              <Scan className="h-4 w-4" /> Run System Scan
            </>
          )}
        </button>
        {result && (
          <button onClick={generateReport} className="btn-secondary">
            Generate Diagnostic Report
          </button>
        )}
      </div>

      {result && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-6">
          <div className="grid gap-6 lg:grid-cols-4">
            <div className="card flex flex-col items-center justify-center">
              <HealthScoreRing score={result.health_score} size="lg" />
              <p className="mt-3 text-sm text-gray-400">Overall Health</p>
            </div>

            <div className="card lg:col-span-3">
              <h3 className="mb-4 font-medium text-white">System Overview</h3>
              <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                <InfoItem label="Operating System" value={`${result.os.name} ${result.os.version}`} />
                <InfoItem label="Hostname" value={result.os.hostname} />
                <InfoItem label="Architecture" value={result.os.arch} />
                <InfoItem label="CPU" value={result.cpu.brand} />
                <InfoItem label="CPU Cores" value={String(result.cpu.cores)} />
                <InfoItem label="CPU Usage" value={`${result.cpu.usage_percent.toFixed(1)}%`} />
                <InfoItem
                  label="Memory"
                  value={`${result.memory.used_gb} / ${result.memory.total_gb} GB (${result.memory.usage_percent.toFixed(1)}%)`}
                />
                <InfoItem label="Kernel" value={result.os.kernel_version} />
              </div>
            </div>
          </div>

          <div className="card">
            <h3 className="mb-4 font-medium text-white">Disk Usage</h3>
            <div className="space-y-3">
              {result.disks.map((disk) => (
                <div key={disk.mount_point}>
                  <div className="mb-1 flex justify-between text-sm">
                    <span className="text-gray-300">
                      {disk.mount_point} ({disk.file_system})
                    </span>
                    <span className="text-gray-400">
                      {disk.used_gb} / {disk.total_gb} GB
                    </span>
                  </div>
                  <div className="h-2 overflow-hidden rounded-full bg-surface">
                    <div
                      className={`h-full rounded-full transition-all ${
                        disk.usage_percent > 90
                          ? "bg-red-500"
                          : disk.usage_percent > 75
                            ? "bg-yellow-500"
                            : "bg-thorpe-500"
                      }`}
                      style={{ width: `${disk.usage_percent}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>

          {result.issues.length > 0 ? (
            <div className="card">
              <h3 className="mb-4 flex items-center gap-2 font-medium text-white">
                <AlertTriangle className="h-5 w-5 text-yellow-400" />
                Detected Issues ({result.issues.length})
              </h3>
              <div className="space-y-3">
                {result.issues.map((issue) => (
                  <div
                    key={issue.id}
                    className="flex items-start gap-3 rounded-lg border border-surface-border bg-surface p-3"
                  >
                    <RiskBadge level={issue.severity} />
                    <div>
                      <p className="font-medium text-gray-200">{issue.title}</p>
                      <p className="text-sm text-gray-400">{issue.description}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div className="card flex items-center gap-3">
              <CheckCircle className="h-5 w-5 text-green-400" />
              <p className="text-gray-300">No significant issues detected.</p>
            </div>
          )}

          <div className="card">
            <h3 className="mb-4 font-medium text-white">Top Processes</h3>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-surface-border text-left text-gray-400">
                    <th className="pb-2 pr-4">Process</th>
                    <th className="pb-2 pr-4">PID</th>
                    <th className="pb-2 pr-4">CPU %</th>
                    <th className="pb-2">Memory</th>
                  </tr>
                </thead>
                <tbody>
                  {result.processes.map((proc) => (
                    <tr key={proc.pid} className="border-b border-surface-border/50">
                      <td className="py-2 pr-4 text-gray-200">{proc.name}</td>
                      <td className="py-2 pr-4 text-gray-400">{proc.pid}</td>
                      <td className="py-2 pr-4 text-gray-300">{proc.cpu_usage.toFixed(1)}%</td>
                      <td className="py-2 text-gray-300">{proc.memory_mb.toFixed(0)} MB</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </motion.div>
      )}
    </div>
  );
}

function InfoItem({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-xs text-gray-500">{label}</p>
      <p className="text-sm font-medium text-gray-200">{value}</p>
    </div>
  );
}
