"use client";

import { useEffect, useState } from "react";
import { useRequireAdmin } from "@/hooks/useRequireAuth";
import { Card } from "@/components/Card";
import { api } from "@/lib/api";
import type { AdminAnalytics } from "@/types/api";

interface AuditEventRow {
  id: string;
  actor_user_id: string | null;
  action: string;
  target_type: string | null;
  target_id: string | null;
  created_at: string;
}

interface FeedbackRow {
  id: string;
  scan_id: string;
  verdict: string;
  comment: string | null;
  created_at: string;
}

function StatCard({ label, value }: { label: string; value: number | string }) {
  return (
    <Card className="p-5">
      <p className="text-xs uppercase tracking-wide text-[var(--color-faint)]">{label}</p>
      <p className="mt-2 font-tess-mono text-2xl">{value}</p>
    </Card>
  );
}

export default function AdminPage() {
  const { user, loading: authLoading } = useRequireAdmin();
  const [analytics, setAnalytics] = useState<AdminAnalytics | null>(null);
  const [audit, setAudit] = useState<AuditEventRow[] | null>(null);
  const [feedback, setFeedback] = useState<FeedbackRow[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!user || user.role !== "admin") return;
    Promise.all([
      api.get<AdminAnalytics>("/api/v1/admin/analytics"),
      api.get<AuditEventRow[]>("/api/v1/admin/audit-events?limit=20"),
      api.get<FeedbackRow[]>("/api/v1/admin/feedback?limit=20"),
    ])
      .then(([a, ev, fb]) => {
        setAnalytics(a);
        setAudit(ev);
        setFeedback(fb);
      })
      .catch(() => setError("Couldn't load admin data."));
  }, [user]);

  if (authLoading || !user || user.role !== "admin") {
    return <div className="mx-auto max-w-4xl px-6 py-20 text-center text-[var(--color-muted)]">Loading…</div>;
  }

  return (
    <div className="mx-auto max-w-4xl px-6 py-16">
      <h1 className="font-display text-2xl">Admin</h1>
      {error && <p className="mt-4 text-sm text-[var(--color-danger)]">{error}</p>}

      {analytics && (
        <>
          <p className="mt-2 text-xs text-[var(--color-faint)]">{analytics.note}</p>
          <div className="mt-6 grid grid-cols-2 gap-4 sm:grid-cols-3">
            <StatCard label="Total users" value={analytics.total_users} />
            <StatCard label="Total scans" value={analytics.total_scans} />
            <StatCard label="Completed" value={analytics.completed_scans} />
            <StatCard label="Needs review" value={analytics.needs_review_scans} />
            <StatCard label="Failed" value={analytics.failed_scans} />
          </div>
        </>
      )}

      <div className="mt-10 grid gap-8 md:grid-cols-2">
        <div>
          <h2 className="font-display text-lg">Recent feedback</h2>
          <div className="mt-3 space-y-2">
            {feedback === null && <p className="text-sm text-[var(--color-muted)]">Loading…</p>}
            {feedback?.length === 0 && <p className="text-sm text-[var(--color-muted)]">No feedback yet.</p>}
            {feedback?.map((f) => (
              <Card key={f.id} className="p-4">
                <p className="text-sm capitalize">{f.verdict}</p>
                {f.comment && <p className="mt-1 text-xs text-[var(--color-muted)]">{f.comment}</p>}
                <p className="mt-1 font-tess-mono text-xs text-[var(--color-faint)]">
                  {new Date(f.created_at).toLocaleString()}
                </p>
              </Card>
            ))}
          </div>
        </div>

        <div>
          <h2 className="font-display text-lg">Audit log</h2>
          <div className="mt-3 space-y-2">
            {audit === null && <p className="text-sm text-[var(--color-muted)]">Loading…</p>}
            {audit?.map((e) => (
              <Card key={e.id} className="p-4">
                <p className="font-tess-mono text-xs text-[var(--color-text)]">{e.action}</p>
                <p className="mt-1 font-tess-mono text-xs text-[var(--color-faint)]">
                  {new Date(e.created_at).toLocaleString()}
                </p>
              </Card>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
