"use client";

import { useState } from "react";
import { Card } from "@/components/Card";
import { Button } from "@/components/Button";
import { ResinTriangle } from "@/components/ResinTriangle";
import { getMaterialMeta, confidenceBandLabel, confidenceBandColor } from "@/lib/materials";
import { api, ApiError } from "@/lib/api";
import type { ScanPublic } from "@/types/api";

export function ResultCard({ scan, onDeleted }: { scan: ScanPublic; onDeleted?: () => void }) {
  const [guidance, setGuidance] = useState<Record<string, string> | null>(null);
  const [guidanceLoading, setGuidanceLoading] = useState(false);
  const [feedbackSent, setFeedbackSent] = useState<string | null>(null);
  const [feedbackError, setFeedbackError] = useState<string | null>(null);
  const [deleting, setDeleting] = useState(false);

  const primary = scan.objects[0];
  const isUncertain = scan.confidence_band === "low" || !primary;

  async function loadGuidance() {
    setGuidanceLoading(true);
    try {
      const res = await api.get<{ guidance: Record<string, string> }>(`/api/v1/scans/${scan.id}/guidance`);
      setGuidance(res.guidance);
    } catch {
      setGuidance(null);
    } finally {
      setGuidanceLoading(false);
    }
  }

  async function sendFeedback(verdict: "correct" | "incorrect" | "unsure") {
    setFeedbackError(null);
    try {
      await api.post(`/api/v1/scans/${scan.id}/feedback`, { verdict });
      setFeedbackSent(verdict);
    } catch (err) {
      setFeedbackError(err instanceof ApiError ? err.message : "Couldn't submit feedback.");
    }
  }

  async function handleDelete() {
    setDeleting(true);
    try {
      await api.delete(`/api/v1/scans/${scan.id}`);
      onDeleted?.();
    } finally {
      setDeleting(false);
    }
  }

  if (scan.status === "failed") {
    return (
      <Card className="p-6">
        <p className="font-display text-lg text-[var(--color-danger)]">Analysis failed</p>
        <p className="mt-2 text-sm text-[var(--color-muted)]">
          {scan.error_message || "Something went wrong while analyzing this image. Please try another photo."}
        </p>
      </Card>
    );
  }

  return (
    <Card className="p-6 sm:p-8">
      {scan.is_mock_result && (
        <p className="mb-4 inline-block rounded-full border border-[var(--color-uncertainty)] px-3 py-1 font-tess-mono text-xs text-[var(--color-uncertainty)]">
          DEMO / MOCK AI RESULT
        </p>
      )}

      <div className="flex flex-col items-center gap-6 sm:flex-row sm:items-start">
        <ResinTriangle
          code={primary ? getMaterialMeta(primary.category_code).ric : "?"}
          confidence={isUncertain ? null : scan.overall_confidence}
          color={primary ? getMaterialMeta(primary.category_code).color : "var(--color-unknown)"}
        />
        <div className="flex-1 text-center sm:text-left">
          {isUncertain ? (
            <>
              <h2 className="font-display text-xl">Unable to confidently identify this material.</h2>
              <p className="mt-2 text-sm text-[var(--color-muted)]">
                The image doesn&apos;t provide enough evidence for a reliable classification.
                Try a clearer, closer photo with better lighting, and photograph one item at a time.
              </p>
            </>
          ) : (
            <>
              <h2 className="font-display text-xl">{getMaterialMeta(primary.category_code).label}</h2>
              <p
                className="mt-1 font-tess-mono text-sm"
                style={{ color: confidenceBandColor(scan.confidence_band) }}
              >
                {confidenceBandLabel(scan.confidence_band)} · {Math.round((scan.overall_confidence ?? 0) * 100)}%
              </p>
            </>
          )}

          {scan.objects.length > 1 && (
            <p className="mt-2 text-xs text-[var(--color-muted)]">
              Multiple materials detected — mixed or overlapping objects reduce reliability of a single classification.
            </p>
          )}
        </div>
      </div>

      {scan.explanation && (
        <div className="mt-6 border-t border-[var(--color-border)] pt-6">
          <p className="text-xs uppercase tracking-wide text-[var(--color-faint)]">Why this result?</p>
          <p className="mt-2 text-sm text-[var(--color-muted)]">{scan.explanation}</p>
        </div>
      )}

      {scan.limitations.length > 0 && (
        <div className="mt-4">
          <p className="text-xs uppercase tracking-wide text-[var(--color-faint)]">Could this be wrong?</p>
          <ul className="mt-2 list-inside list-disc text-sm text-[var(--color-muted)]">
            {scan.limitations.map((l, i) => (
              <li key={i}>{l}</li>
            ))}
          </ul>
        </div>
      )}

      {!isUncertain && (
        <div className="mt-6 border-t border-[var(--color-border)] pt-6">
          <div className="flex items-center justify-between">
            <p className="text-xs uppercase tracking-wide text-[var(--color-faint)]">
              Recycling guidance{" "}
              <span className="text-[var(--color-faint)]">(from Tesseractis&apos; rule engine, not the AI)</span>
            </p>
            {!guidance && (
              <Button variant="ghost" onClick={loadGuidance} disabled={guidanceLoading} className="!px-2 !py-1 text-xs">
                {guidanceLoading ? "Loading…" : "Show guidance"}
              </Button>
            )}
          </div>
          {guidance && (
            <div className="mt-3 space-y-2">
              {Object.entries(guidance).map(([code, text]) => (
                <p key={code} className="text-sm text-[var(--color-muted)]">
                  <span className="font-tess-mono text-[var(--color-text)]">{code}:</span> {text}
                </p>
              ))}
            </div>
          )}
        </div>
      )}

      <div className="mt-6 border-t border-[var(--color-border)] pt-6">
        <p className="text-xs uppercase tracking-wide text-[var(--color-faint)]">Was this correct?</p>
        {feedbackSent ? (
          <p className="mt-2 text-sm text-[var(--color-success)]">Thanks — feedback recorded.</p>
        ) : (
          <div className="mt-2 flex gap-2">
            <Button variant="secondary" onClick={() => sendFeedback("correct")} className="!px-4 !py-1.5 text-xs">
              Correct
            </Button>
            <Button variant="secondary" onClick={() => sendFeedback("incorrect")} className="!px-4 !py-1.5 text-xs">
              Incorrect
            </Button>
            <Button variant="secondary" onClick={() => sendFeedback("unsure")} className="!px-4 !py-1.5 text-xs">
              Unsure
            </Button>
          </div>
        )}
        {feedbackError && <p className="mt-2 text-xs text-[var(--color-danger)]">{feedbackError}</p>}
      </div>

      {onDeleted && (
        <div className="mt-6 flex justify-end">
          <Button variant="danger" onClick={handleDelete} loading={deleting} className="!px-4 !py-1.5 text-xs">
            Delete this analysis
          </Button>
        </div>
      )}
    </Card>
  );
}
