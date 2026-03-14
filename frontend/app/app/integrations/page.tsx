"use client";

import { useState } from "react";

import { ErrorState } from "@/components/ui/ErrorState";
import { api } from "@/services/api";

export default function IntegrationsPage() {
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  return (
    <div className="space-y-4">
      <h2 className="text-2xl font-semibold">Integrations</h2>
      {error ? <ErrorState message={error} /> : null}
      {message ? <div className="card border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-700">{message}</div> : null}
      <div className="card p-6">
        <h3 className="text-lg font-semibold">Google Calendar</h3>
        <p className="mt-1 text-sm text-slate-600">
          Connect Google Calendar for meeting scheduling. Outlook support is structured for later extension.
        </p>
        <button
          className="btn-primary mt-4"
          onClick={async () => {
            setError("");
            try {
              const data = await api.post<{ connected: boolean }>("/calendar/connect/google", {});
              setMessage(data.connected ? "Google Calendar connected." : "Connection failed.");
            } catch (err) {
              setError(err instanceof Error ? err.message : "Connection failed");
            }
          }}
        >
          Connect Google Calendar
        </button>
      </div>
      <div className="card p-6">
        <h3 className="text-lg font-semibold">Email Provider</h3>
        <p className="mt-1 text-sm text-slate-600">
          SendGrid is supported behind a provider abstraction so additional providers can be added safely.
        </p>
      </div>
    </div>
  );
}
