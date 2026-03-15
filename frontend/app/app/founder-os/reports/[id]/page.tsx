"use client";

import { useParams, useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

import { ErrorState } from "@/components/ui/ErrorState";
import { LoadingState } from "@/components/ui/LoadingState";
import { api } from "@/services/api";
import type { FounderOSReportRead } from "@/types";

function sectionEntries(report: FounderOSReportRead): Array<{ key: string; value: unknown }> {
  const output = report.output_json || {};
  const finalOutput = (output.final_output as Record<string, unknown> | undefined) || {};
  return Object.entries(finalOutput).map(([key, value]) => ({ key, value }));
}

export default function FounderOSReportDetailPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const [report, setReport] = useState<FounderOSReportRead | null>(null);
  const [error, setError] = useState("");
  const [copyState, setCopyState] = useState("");

  useEffect(() => {
    api
      .get<FounderOSReportRead>(`/founder-os/reports/${params.id}`)
      .then(setReport)
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load report"));
  }, [params.id]);

  const sections = useMemo(() => (report ? sectionEntries(report) : []), [report]);
  const rawJson = useMemo(() => JSON.stringify(report?.output_json || {}, null, 2), [report]);

  const copy = async (text: string, label: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopyState(`${label} copied.`);
      setTimeout(() => setCopyState(""), 1500);
    } catch {
      setCopyState("Copy failed.");
      setTimeout(() => setCopyState(""), 1500);
    }
  };

  if (error && !report) return <ErrorState message={error} />;
  if (!report) return <LoadingState label="Loading Founder OS report..." />;

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <button className="text-sm text-brand-600 hover:underline" onClick={() => router.push("/app/founder-os/reports")}>
            ← Back to reports
          </button>
          <h2 className="text-2xl font-semibold">{report.title}</h2>
          <p className="text-sm text-slate-600">
            {report.report_type} • {new Date(report.created_at).toLocaleString()}
          </p>
        </div>
        <div className="flex gap-2">
          <button className="btn-secondary" onClick={() => copy(report.summary || "", "Summary")}>
            Copy Summary
          </button>
          <button className="btn-secondary" onClick={() => copy(rawJson, "Raw JSON")}>
            Copy JSON
          </button>
        </div>
      </div>

      {error ? <ErrorState message={error} /> : null}
      {copyState ? <div className="card border-emerald-200 bg-emerald-50 p-2 text-sm text-emerald-700">{copyState}</div> : null}

      <div className="card p-4">
        <h3 className="text-base font-semibold">Summary</h3>
        <p className="mt-2 text-sm text-slate-700">{report.summary || "No summary available."}</p>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <div className="card p-4">
          <h3 className="text-base font-semibold">Structured Sections</h3>
          {!sections.length ? (
            <p className="mt-2 text-sm text-slate-600">No structured output sections found.</p>
          ) : (
            <div className="mt-3 space-y-3">
              {sections.map((section) => (
                <div key={section.key} className="rounded-lg border border-slate-200 p-3">
                  <p className="text-sm font-medium text-slate-800">{section.key}</p>
                  <pre className="mt-2 whitespace-pre-wrap text-xs text-slate-700">{JSON.stringify(section.value, null, 2)}</pre>
                </div>
              ))}
            </div>
          )}
        </div>
        <div className="card p-4">
          <h3 className="text-base font-semibold">Raw JSON</h3>
          <pre className="mt-2 max-h-[36rem] overflow-auto rounded bg-slate-900 p-3 text-xs text-slate-100">{rawJson}</pre>
        </div>
      </div>
    </div>
  );
}
