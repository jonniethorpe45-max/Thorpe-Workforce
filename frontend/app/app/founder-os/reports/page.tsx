"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import { EmptyState } from "@/components/ui/EmptyState";
import { ErrorState } from "@/components/ui/ErrorState";
import { LoadingState } from "@/components/ui/LoadingState";
import { api } from "@/services/api";
import type { FounderOSReportListResponse, FounderOSReportRead } from "@/types";

const reportTypeOptions: Array<{ value: string; label: string }> = [
  { value: "", label: "All report types" },
  { value: "daily_briefing", label: "Daily Briefing" },
  { value: "growth_campaign", label: "Growth Campaign" },
  { value: "creator_recruitment", label: "Creator Recruitment" },
  { value: "investor_update", label: "Investor Update" },
  { value: "weekly_content_engine", label: "Weekly Content Engine" }
];

export default function FounderOSReportsPage() {
  const [reports, setReports] = useState<FounderOSReportRead[] | null>(null);
  const [total, setTotal] = useState(0);
  const [reportType, setReportType] = useState("");
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    setError("");
    const params = new URLSearchParams({ limit: "100", offset: "0" });
    if (reportType) params.set("report_type", reportType);
    const response = await api.get<FounderOSReportListResponse>(`/founder-os/reports?${params.toString()}`);
    setReports(response.items);
    setTotal(response.total);
  }, [reportType]);

  useEffect(() => {
    load().catch((err) => setError(err instanceof Error ? err.message : "Failed to load founder reports"));
  }, [load]);

  if (error && !reports) return <ErrorState message={error} />;
  if (!reports) return <LoadingState label="Loading founder reports..." />;

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <h2 className="text-2xl font-semibold">Founder OS Reports</h2>
          <p className="text-sm text-slate-600">Browse saved outputs from Founder OS chains.</p>
        </div>
        <label className="text-sm">
          <span className="mr-2 text-slate-600">Type</span>
          <select
            className="rounded-lg border border-slate-200 px-3 py-2"
            onChange={(event) => setReportType(event.target.value)}
            value={reportType}
          >
            {reportTypeOptions.map((option) => (
              <option key={option.value || "all"} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </label>
      </div>

      {error ? <ErrorState message={error} /> : null}

      {!reports.length ? (
        <EmptyState title="No reports yet" description="Run a Founder OS chain to generate report history." />
      ) : (
        <div className="card p-0">
          <table className="min-w-full text-sm">
            <thead className="bg-slate-100 text-left text-slate-600">
              <tr>
                <th className="px-4 py-3">Title</th>
                <th className="px-4 py-3">Type</th>
                <th className="px-4 py-3">Created</th>
                <th className="px-4 py-3">Summary</th>
                <th className="px-4 py-3">Action</th>
              </tr>
            </thead>
            <tbody>
              {reports.map((report) => (
                <tr key={report.id} className="border-t border-slate-200">
                  <td className="px-4 py-3 font-medium text-slate-800">{report.title}</td>
                  <td className="px-4 py-3 text-slate-700">{report.report_type}</td>
                  <td className="px-4 py-3 text-slate-700">{new Date(report.created_at).toLocaleString()}</td>
                  <td className="max-w-lg px-4 py-3 text-slate-700">{report.summary || "—"}</td>
                  <td className="px-4 py-3">
                    <Link className="text-brand-600 hover:underline" href={`/app/founder-os/reports/${report.id}`}>
                      View
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <div className="border-t border-slate-200 px-4 py-2 text-xs text-slate-500">Showing {reports.length} of {total} reports</div>
        </div>
      )}
    </div>
  );
}
