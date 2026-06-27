import { useEffect, useState } from "react";
import { FileText, Download, Trash2, Search, Eye } from "lucide-react";
import { RiskBadge } from "../components/ui/RiskBadge";
import { HealthScoreRing } from "../components/ui/HealthScoreRing";
import { thorpeApi } from "../services/tauri";
import { useAppStore } from "../services/store";
import type { DiagnosticReport } from "../services/types";

export function DiagnosticReports() {
  const [reports, setReports] = useState<DiagnosticReport[]>([]);
  const [selected, setSelected] = useState<DiagnosticReport | null>(null);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const { addNotification } = useAppStore();

  const loadReports = async () => {
    setLoading(true);
    try {
      const data = search
        ? await thorpeApi.searchReports(search)
        : await thorpeApi.listReports();
      setReports(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadReports();
  }, []);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    loadReports();
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Delete this report?")) return;
    try {
      await thorpeApi.deleteReport(id);
      setReports((prev) => prev.filter((r) => r.id !== id));
      if (selected?.id === id) setSelected(null);
      addNotification({ type: "success", title: "Report Deleted", message: "Report removed." });
    } catch (err) {
      addNotification({ type: "error", title: "Delete Failed", message: String(err) });
    }
  };

  const handleExport = async (report: DiagnosticReport) => {
    try {
      const feature = await thorpeApi.checkFeature("pdf_export");
      if (!feature.allowed) {
        addNotification({
          type: "warning",
          title: "Upgrade Required",
          message: "PDF export requires a Professional license.",
        });
        return;
      }
      const path = `/tmp/thorpe-report-${report.id}.pdf`;
      await thorpeApi.exportReportPdf(report.id, path);
      addNotification({
        type: "success",
        title: "PDF Exported",
        message: `Saved to ${path}`,
      });
    } catch (err) {
      addNotification({ type: "error", title: "Export Failed", message: String(err) });
    }
  };

  const parseFindings = (findings: string) => {
    try {
      return JSON.parse(findings) as Array<{
        title: string;
        description: string;
        severity: string;
      }>;
    } catch {
      return [];
    }
  };

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Diagnostic Reports</h1>
          <p className="mt-1 text-gray-400">AI-generated reports from system scans.</p>
        </div>
      </div>

      <form onSubmit={handleSearch} className="flex gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-500" />
          <input
            type="search"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search reports..."
            className="input pl-10"
          />
        </div>
        <button type="submit" className="btn-secondary">
          Search
        </button>
      </form>

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="space-y-3 lg:col-span-1">
          {loading ? (
            <div className="card flex h-40 items-center justify-center">
              <div className="h-6 w-6 animate-spin rounded-full border-2 border-thorpe-500 border-t-transparent" />
            </div>
          ) : reports.length === 0 ? (
            <div className="card flex flex-col items-center gap-3 py-8">
              <FileText className="h-10 w-10 text-gray-600" />
              <p className="text-sm text-gray-400">No reports yet. Run a scan first.</p>
            </div>
          ) : (
            reports.map((report) => (
              <button
                key={report.id}
                onClick={() => setSelected(report)}
                className={`card w-full text-left transition-all hover:border-thorpe-500/30 ${
                  selected?.id === report.id ? "border-thorpe-500/50 bg-thorpe-600/5" : ""
                }`}
              >
                <div className="flex items-center justify-between">
                  <p className="text-sm font-medium text-gray-200 line-clamp-1">{report.title}</p>
                  <RiskBadge level={report.risk_level} />
                </div>
                <p className="mt-1 text-xs text-gray-500">
                  {new Date(report.created_at).toLocaleString()}
                </p>
                <div className="mt-2 flex items-center gap-2">
                  <span className="text-lg font-bold text-white">{report.health_score}</span>
                  <span className="text-xs text-gray-400">/ 100</span>
                </div>
              </button>
            ))
          )}
        </div>

        <div className="lg:col-span-2">
          {selected ? (
            <div className="card space-y-6">
              <div className="flex items-start justify-between">
                <div>
                  <h2 className="text-lg font-bold text-white">{selected.title}</h2>
                  <p className="text-sm text-gray-400">
                    {new Date(selected.created_at).toLocaleString()}
                  </p>
                </div>
                <HealthScoreRing score={selected.health_score} size="sm" />
              </div>

              <div>
                <h3 className="mb-2 text-sm font-medium text-gray-400">Summary</h3>
                <p className="text-gray-200">{selected.summary}</p>
              </div>

              <div>
                <h3 className="mb-2 text-sm font-medium text-gray-400">Plain Language</h3>
                <p className="text-gray-200">{selected.plain_language}</p>
              </div>

              <div>
                <h3 className="mb-2 text-sm font-medium text-gray-400">Findings</h3>
                <div className="space-y-2">
                  {parseFindings(selected.findings).map((f, i) => (
                    <div key={i} className="flex items-start gap-2 rounded-lg bg-surface p-3">
                      <RiskBadge level={f.severity} />
                      <div>
                        <p className="text-sm font-medium text-gray-200">{f.title}</p>
                        <p className="text-xs text-gray-400">{f.description}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div className="flex gap-3 border-t border-surface-border pt-4">
                <button onClick={() => handleExport(selected)} className="btn-primary text-sm">
                  <Download className="h-4 w-4" /> Export PDF
                </button>
                <button onClick={() => handleDelete(selected.id)} className="btn-danger text-sm">
                  <Trash2 className="h-4 w-4" /> Delete
                </button>
              </div>
            </div>
          ) : (
            <div className="card flex h-64 flex-col items-center justify-center gap-3">
              <Eye className="h-10 w-10 text-gray-600" />
              <p className="text-sm text-gray-400">Select a report to view details</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
