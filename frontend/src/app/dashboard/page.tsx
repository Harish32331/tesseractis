"use client";

import { useState } from "react";
import { useRequireAuth } from "@/hooks/useRequireAuth";
import { UploadDropzone } from "@/features/scan/UploadDropzone";
import { ResultCard } from "@/features/scan/ResultCard";
import { Button } from "@/components/Button";
import { api, ApiError } from "@/lib/api";
import type { ScanPublic } from "@/types/api";

type Stage = "idle" | "analyzing" | "done" | "error";

export default function DashboardPage() {
  const { user, loading } = useRequireAuth();
  const [file, setFile] = useState<File | null>(null);
  const [stage, setStage] = useState<Stage>("idle");
  const [result, setResult] = useState<ScanPublic | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function analyze() {
    if (!file) return;
    setStage("analyzing");
    setError(null);
    try {
      const form = new FormData();
      form.append("file", file);
      const scan = await api.postForm<ScanPublic>("/api/v1/scans", form);
      setResult(scan);
      setStage("done");
    } catch (err) {
      setStage("error");
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("Something went wrong while analyzing this image. Please try again.");
      }
    }
  }

  function startOver() {
    setFile(null);
    setResult(null);
    setError(null);
    setStage("idle");
  }

  if (loading || !user) {
    return <div className="mx-auto max-w-2xl px-6 py-20 text-center text-[var(--color-muted)]">Loading…</div>;
  }

  return (
    <div className="mx-auto max-w-2xl px-6 py-16">
      <h1 className="font-display text-2xl">Identify a plastic item</h1>
      <p className="mt-2 text-sm text-[var(--color-muted)]">
        Upload a clear photo of one plastic item for the most reliable result.
      </p>

      <div className="mt-8">
        {stage !== "done" && (
          <UploadDropzone onFileSelected={setFile} disabled={stage === "analyzing"} />
        )}

        {stage === "idle" && file && (
          <div className="mt-6 flex justify-center">
            <Button onClick={analyze}>Analyze</Button>
          </div>
        )}

        {stage === "analyzing" && (
          <p className="mt-6 text-center font-tess-mono text-sm text-[var(--color-uncertainty)]" role="status">
            Inspecting material…
          </p>
        )}

        {stage === "error" && (
          <div className="mt-6 text-center">
            <p role="alert" className="text-sm text-[var(--color-danger)]">
              {error}
            </p>
            <Button variant="secondary" onClick={startOver} className="mt-4">
              Try another photo
            </Button>
          </div>
        )}

        {stage === "done" && result && (
          <div className="mt-6">
            <ResultCard scan={result} />
            <div className="mt-6 flex justify-center">
              <Button variant="secondary" onClick={startOver}>
                Analyze another photo
              </Button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
