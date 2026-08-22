"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { useRequireAuth } from "@/hooks/useRequireAuth";
import { ResultCard } from "@/features/scan/ResultCard";
import { api, ApiError } from "@/lib/api";
import type { ScanPublic } from "@/types/api";

export default function ScanDetailPage() {
  const { user, loading: authLoading } = useRequireAuth();
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const [scan, setScan] = useState<ScanPublic | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!user) return;
    api
      .get<ScanPublic>(`/api/v1/scans/${params.id}`)
      .then(setScan)
      .catch((err) => {
        if (err instanceof ApiError && err.status === 403) {
          setError("You don't have access to this analysis.");
        } else if (err instanceof ApiError && err.status === 404) {
          setError("This analysis was not found.");
        } else {
          setError("Couldn't load this analysis.");
        }
      });
  }, [user, params.id]);

  if (authLoading || !user) {
    return <div className="mx-auto max-w-2xl px-6 py-20 text-center text-[var(--color-muted)]">Loading…</div>;
  }

  return (
    <div className="mx-auto max-w-2xl px-6 py-16">
      {error && <p className="text-sm text-[var(--color-danger)]">{error}</p>}
      {!error && !scan && <p className="text-[var(--color-muted)]">Loading…</p>}
      {scan && <ResultCard scan={scan} onDeleted={() => router.push("/history")} />}
    </div>
  );
}
