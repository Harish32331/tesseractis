"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRequireAuth } from "@/hooks/useRequireAuth";
import { Card } from "@/components/Card";
import { Button } from "@/components/Button";
import { api } from "@/lib/api";
import { confidenceBandColor } from "@/lib/materials";
import type { ScanSummary } from "@/types/api";

const PAGE_SIZE = 10;

export default function HistoryPage() {
  const { user, loading: authLoading } = useRequireAuth();
  const [scans, setScans] = useState<ScanSummary[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [offset, setOffset] = useState(0);

  useEffect(() => {
    if (!user) return;
    let cancelled = false;
    api
      .get<ScanSummary[]>(`/api/v1/scans?limit=${PAGE_SIZE}&offset=${offset}`)
      .then((data) => {
        if (!cancelled) setScans(data);
      })
      .catch(() => {
        if (!cancelled) setError("Couldn't load your history. Please try again.");
      });
    return () => {
      cancelled = true;
    };
  }, [user, offset]);

  if (authLoading || !user) {
    return <div className="mx-auto max-w-3xl px-6 py-20 text-center text-[var(--color-muted)]">Loading…</div>;
  }

  return (
    <div className="mx-auto max-w-3xl px-6 py-16">
      <h1 className="font-display text-2xl">Analysis history</h1>

      {error && <p className="mt-6 text-sm text-[var(--color-danger)]">{error}</p>}

      {scans === null && !error && (
        <div className="mt-8 space-y-3">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="h-20 animate-pulse rounded-xl bg-[var(--color-card)]" />
          ))}
        </div>
      )}

      {scans !== null && scans.length === 0 && (
        <Card className="mt-8 p-10 text-center">
          <p className="text-[var(--color-muted)]">No analyses yet.</p>
          <Link href="/dashboard">
            <Button className="mt-4">Identify your first material</Button>
          </Link>
        </Card>
      )}

      {scans !== null && scans.length > 0 && (
        <>
          <div className="mt-8 space-y-3">
            {scans.map((s) => (
              <Link key={s.id} href={`/scans/${s.id}`}>
                <Card className="flex items-center justify-between p-5 transition-colors hover:bg-[var(--color-card-raised)]">
                  <div>
                    <p className="font-tess-mono text-xs text-[var(--color-faint)]">
                      {new Date(s.created_at).toLocaleString()}
                    </p>
                    <p className="mt-1 text-sm capitalize" style={{ color: confidenceBandColor(s.confidence_band) }}>
                      {s.status === "failed" ? "Failed" : s.confidence_band ?? "unknown"} confidence
                      {s.needs_review ? " · needs review" : ""}
                    </p>
                  </div>
                  {s.overall_confidence !== null && (
                    <span className="font-tess-mono text-sm text-[var(--color-muted)]">
                      {Math.round(s.overall_confidence * 100)}%
                    </span>
                  )}
                </Card>
              </Link>
            ))}
          </div>
          <div className="mt-6 flex justify-between">
            <Button variant="secondary" disabled={offset === 0} onClick={() => setOffset(Math.max(0, offset - PAGE_SIZE))}>
              Previous
            </Button>
            <Button
              variant="secondary"
              disabled={scans.length < PAGE_SIZE}
              onClick={() => setOffset(offset + PAGE_SIZE)}
            >
              Next
            </Button>
          </div>
        </>
      )}
    </div>
  );
}
