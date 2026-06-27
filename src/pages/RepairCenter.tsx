import { useEffect, useState } from "react";
import { Wrench, AlertTriangle, CheckCircle, XCircle, History } from "lucide-react";
import { RiskBadge } from "../components/ui/RiskBadge";
import { thorpeApi } from "../services/tauri";
import { useAppStore } from "../services/store";
import type { RepairAction, RepairRecord } from "../services/types";

export function RepairCenter() {
  const [actions, setActions] = useState<RepairAction[]>([]);
  const [history, setHistory] = useState<RepairRecord[]>([]);
  const [selected, setSelected] = useState<RepairAction | null>(null);
  const [executing, setExecuting] = useState(false);
  const [result, setResult] = useState<{ success: boolean; message: string; details?: string | null } | null>(null);
  const [showHistory, setShowHistory] = useState(false);
  const { addNotification } = useAppStore();

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const feature = await thorpeApi.checkFeature("repair_center");
      if (!feature.allowed) return;

      const [acts, hist] = await Promise.all([
        thorpeApi.listRepairActions(),
        thorpeApi.listRepairHistory(),
      ]);
      setActions(acts);
      setHistory(hist);
    } catch (err) {
      console.error(err);
    }
  };

  const executeAction = async (confirmed: boolean) => {
    if (!selected) return;
    setExecuting(true);
    setResult(null);
    try {
      const res = await thorpeApi.executeRepair(selected.id, confirmed);
      setResult(res);
      addNotification({
        type: res.success ? "success" : "error",
        title: selected.name,
        message: res.message,
      });
      const hist = await thorpeApi.listRepairHistory();
      setHistory(hist);
    } catch (err) {
      setResult({ success: false, message: String(err) });
    } finally {
      setExecuting(false);
    }
  };

  const [featureAllowed, setFeatureAllowed] = useState<boolean | null>(null);

  useEffect(() => {
    thorpeApi.checkFeature("repair_center").then((f) => setFeatureAllowed(f.allowed));
  }, []);

  if (featureAllowed === false) {
    return (
      <div className="flex flex-col items-center justify-center gap-4 py-20 animate-fade-in">
        <Wrench className="h-16 w-16 text-gray-600" />
        <h2 className="text-xl font-bold text-white">Repair Center</h2>
        <p className="max-w-md text-center text-gray-400">
          Repair Center requires a Professional license. Upgrade to access safe maintenance tools.
        </p>
        <a href="/licensing" className="btn-primary">
          View Licensing
        </a>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Repair Center</h1>
          <p className="mt-1 text-gray-400">
            Safe maintenance tools with explicit consent for every action.
          </p>
        </div>
        <button onClick={() => setShowHistory(!showHistory)} className="btn-secondary text-sm">
          <History className="h-4 w-4" />
          {showHistory ? "Hide History" : "View History"}
        </button>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="space-y-3 lg:col-span-1">
          {actions.map((action) => (
            <button
              key={action.id}
              onClick={() => {
                setSelected(action);
                setResult(null);
              }}
              className={`card w-full text-left transition-all hover:border-thorpe-500/30 ${
                selected?.id === action.id ? "border-thorpe-500/50" : ""
              }`}
            >
              <div className="flex items-center justify-between">
                <p className="font-medium text-gray-200">{action.name}</p>
                <RiskBadge level={action.risk_level} />
              </div>
              <p className="mt-1 text-xs text-gray-400">{action.description}</p>
              <span className="mt-2 inline-block text-xs text-gray-500">{action.category}</span>
            </button>
          ))}
        </div>

        <div className="lg:col-span-2">
          {selected ? (
            <div className="card space-y-4">
              <h2 className="text-lg font-bold text-white">{selected.name}</h2>

              <div>
                <h3 className="text-sm font-medium text-gray-400">Purpose</h3>
                <p className="text-gray-200">{selected.purpose}</p>
              </div>

              <div className="flex items-center gap-2">
                <span className="text-sm text-gray-400">Risk Level:</span>
                <RiskBadge level={selected.risk_level} />
              </div>

              {selected.risk_level !== "low" && (
                <div className="flex items-start gap-2 rounded-lg bg-yellow-500/10 border border-yellow-500/20 p-3">
                  <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-yellow-400" />
                  <p className="text-sm text-yellow-200">
                    This action has elevated risk. Review the details carefully before proceeding.
                  </p>
                </div>
              )}

              {result && (
                <div
                  className={`flex items-start gap-2 rounded-lg p-3 ${
                    result.success
                      ? "bg-green-500/10 border border-green-500/20"
                      : "bg-red-500/10 border border-red-500/20"
                  }`}
                >
                  {result.success ? (
                    <CheckCircle className="h-4 w-4 text-green-400" />
                  ) : (
                    <XCircle className="h-4 w-4 text-red-400" />
                  )}
                  <div>
                    <p className="text-sm font-medium text-gray-200">{result.message}</p>
                    {result.details && (
                      <pre className="mt-2 whitespace-pre-wrap text-xs text-gray-400">
                        {result.details}
                      </pre>
                    )}
                  </div>
                </div>
              )}

              <div className="flex gap-3 border-t border-surface-border pt-4">
                <button
                  onClick={() => executeAction(true)}
                  disabled={executing}
                  className="btn-primary"
                >
                  {executing ? "Executing..." : "Execute Repair"}
                </button>
                <button onClick={() => setSelected(null)} className="btn-secondary">
                  Cancel
                </button>
              </div>
            </div>
          ) : (
            <div className="card flex h-64 flex-col items-center justify-center gap-3">
              <Wrench className="h-10 w-10 text-gray-600" />
              <p className="text-sm text-gray-400">Select a repair action to view details</p>
            </div>
          )}

          {showHistory && history.length > 0 && (
            <div className="card mt-4">
              <h3 className="mb-3 font-medium text-white">Repair History</h3>
              <div className="space-y-2">
                {history.map((record) => (
                  <div
                    key={record.id}
                    className="flex items-center justify-between rounded-lg bg-surface p-3 text-sm"
                  >
                    <div>
                      <p className="text-gray-200">{record.action_name}</p>
                      <p className="text-xs text-gray-500">
                        {new Date(record.created_at).toLocaleString()}
                      </p>
                    </div>
                    <span
                      className={`text-xs font-medium ${
                        record.status === "completed" ? "text-green-400" : "text-red-400"
                      }`}
                    >
                      {record.status}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
