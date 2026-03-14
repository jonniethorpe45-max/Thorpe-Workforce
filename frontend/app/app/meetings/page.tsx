"use client";

import { useEffect, useState } from "react";

import { EmptyState } from "@/components/ui/EmptyState";
import { ErrorState } from "@/components/ui/ErrorState";
import { LoadingState } from "@/components/ui/LoadingState";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { api } from "@/services/api";
import type { Meeting } from "@/types";

export default function MeetingsPage() {
  const [meetings, setMeetings] = useState<Meeting[] | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api
      .get<Meeting[]>("/meetings")
      .then(setMeetings)
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load meetings"));
  }, []);

  if (error) return <ErrorState message={error} />;
  if (!meetings) return <LoadingState label="Loading meetings..." />;
  if (!meetings.length) {
    return <EmptyState title="No meetings booked yet" description="Positive replies can be converted into booked meetings." />;
  }

  return (
    <div className="space-y-4">
      <h2 className="text-2xl font-semibold">Meetings</h2>
      <div className="card overflow-hidden">
        <table className="min-w-full text-sm">
          <thead className="bg-slate-100 text-left text-slate-600">
            <tr>
              <th className="px-4 py-3">Provider</th>
              <th className="px-4 py-3">Start</th>
              <th className="px-4 py-3">End</th>
              <th className="px-4 py-3">Status</th>
            </tr>
          </thead>
          <tbody>
            {meetings.map((meeting) => (
              <tr key={meeting.id} className="border-t border-slate-200">
                <td className="px-4 py-3">{meeting.calendar_provider}</td>
                <td className="px-4 py-3">{new Date(meeting.scheduled_start).toLocaleString()}</td>
                <td className="px-4 py-3">{new Date(meeting.scheduled_end).toLocaleString()}</td>
                <td className="px-4 py-3">
                  <StatusBadge status={meeting.meeting_status} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
