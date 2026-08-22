"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { Button } from "@/components/Button";
import { Card } from "@/components/Card";
import { ResinTriangle } from "@/components/ResinTriangle";
import { getMaterialMeta } from "@/lib/materials";

const DEMO_STATES = [
  { code: "PET", confidence: 0.91 },
  { code: "PP", confidence: 0.52 },
  { code: "UNKNOWN", confidence: 0.22 },
];

export default function LandingPage() {
  const [demoIndex, setDemoIndex] = useState(0);

  useEffect(() => {
    const id = setInterval(() => setDemoIndex((i) => (i + 1) % DEMO_STATES.length), 3200);
    return () => clearInterval(id);
  }, []);

  const demo = DEMO_STATES[demoIndex];
  const meta = getMaterialMeta(demo.code);

  return (
    <div>
      <section className="mx-auto max-w-6xl px-6 pb-20 pt-16 sm:pt-24">
        <div className="grid items-center gap-12 md:grid-cols-2">
          <div>
            <p className="mb-4 font-tess-mono text-xs uppercase tracking-[0.2em] text-[var(--color-uncertainty)]">
              AI material identification
            </p>
            <h1 className="font-display text-4xl leading-tight tracking-tight sm:text-5xl">
              Know what you&apos;re holding.
            </h1>
            <p className="mt-5 max-w-md text-[var(--color-muted)]">
              Photograph mixed plastic waste. Tesseractis reads the visible material,
              tells you honestly how sure it is, and gives you recycling guidance —
              never a confident guess dressed up as fact.
            </p>
            <div className="mt-8 flex flex-wrap gap-3">
              <Link href="/dashboard">
                <Button>Identify a Material</Button>
              </Link>
              <a href="#how-it-works">
                <Button variant="secondary">How It Works</Button>
              </a>
            </div>
          </div>

          <Card className="flex flex-col items-center gap-5 p-8">
            <div key={demoIndex}>
              <ResinTriangle code={meta.ric} confidence={demo.confidence} color={meta.color} size={140} />
            </div>
            <div className="text-center">
              <p className="font-display text-lg">
                {demo.confidence < 0.45 ? "Unable to confidently identify this material." : meta.label}
              </p>
              <p className="mt-1 font-tess-mono text-sm text-[var(--color-muted)]">
                {demo.confidence < 0.45
                  ? "Low confidence — needs a clearer photo"
                  : `${Math.round(demo.confidence * 100)}% confidence`}
              </p>
            </div>
            <p className="text-center text-xs text-[var(--color-faint)]">
              Live demo — cycles through real confidence states the system can return
            </p>
          </Card>
        </div>
      </section>

      <section id="how-it-works" className="border-t border-[var(--color-border)] bg-[var(--color-card)]/40 py-20">
        <div className="mx-auto max-w-6xl px-6">
          <h2 className="font-display text-2xl">How it works</h2>
          <div className="mt-10 grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
            {[
              { step: "1", title: "Photograph", body: "Upload or capture a photo of the plastic item." },
              { step: "2", title: "AI reads it", body: "Vision analysis identifies visible material characteristics." },
              { step: "3", title: "Honest confidence", body: "High, medium, or low — never a hidden guess." },
              { step: "4", title: "Recycling guidance", body: "Rule-based guidance, separate from the AI's read." },
            ].map((s) => (
              <Card key={s.step} className="p-6">
                <span className="font-tess-mono text-2xl text-[var(--color-uncertainty)]">{s.step}</span>
                <h3 className="mt-3 font-display text-lg">{s.title}</h3>
                <p className="mt-2 text-sm text-[var(--color-muted)]">{s.body}</p>
              </Card>
            ))}
          </div>
        </div>
      </section>

      <section className="py-20">
        <div className="mx-auto max-w-6xl px-6">
          <h2 className="font-display text-2xl">Material categories the system currently supports</h2>
          <p className="mt-2 max-w-2xl text-sm text-[var(--color-muted)]">
            This is an initial, expandable technical taxonomy — not a claim that every
            photograph can determine exact polymer composition.
          </p>
          <div className="mt-8 flex flex-wrap gap-3">
            {["PET", "HDPE", "PVC", "LDPE", "PP", "PS", "Multi-layer/Mixed", "UNKNOWN"].map((code) => {
              const m = getMaterialMeta(code);
              return (
                <span
                  key={code}
                  className="flex items-center gap-2 rounded-full border border-[var(--color-border)] px-4 py-2 text-sm"
                >
                  <span className="h-2.5 w-2.5 rounded-full" style={{ background: m.color }} aria-hidden="true" />
                  {m.label}
                </span>
              );
            })}
          </div>
        </div>
      </section>

      <section className="border-t border-[var(--color-border)] bg-[var(--color-card)]/40 py-20">
        <div className="mx-auto max-w-3xl px-6">
          <h2 className="font-display text-2xl">Why uncertainty matters</h2>
          <p className="mt-4 text-[var(--color-muted)]">
            A confident wrong answer is worse than an honest &ldquo;we don&apos;t know.&rdquo;
            AI predictions are probabilistic and photographs can be ambiguous — lighting,
            angle, and image quality all affect the result. Tesseractis is built to say
            so plainly rather than mask it, and low-confidence results are always flagged
            for a closer look. Recycling guidance reflects general categories; always
            check your local recycling rules for what your facility actually accepts.
          </p>
        </div>
      </section>

      <section className="py-20 text-center">
        <h2 className="font-display text-2xl">Try it on your own photo.</h2>
        <div className="mt-6">
          <Link href="/dashboard">
            <Button>Identify a Material</Button>
          </Link>
        </div>
      </section>

      <footer className="border-t border-[var(--color-border)] py-8 text-center text-xs text-[var(--color-faint)]">
        The Tesseractis — AI-assisted material identification. Not a substitute for
        official recycling certification.
      </footer>
    </div>
  );
}
