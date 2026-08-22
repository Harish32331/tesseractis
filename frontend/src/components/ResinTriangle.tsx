"use client";

/**
 * The Tesseractis signature visual.
 *
 * A resin-identification-code triangle (the real stamp found on plastic
 * packaging) whose fill communicates confidence directly: solid and
 * filled at high confidence, faint at medium, and an open dashed outline
 * with a question mark when the system genuinely doesn't know — so the
 * product's core promise (never fake certainty) is visible in the
 * artwork itself, not just explained in a paragraph next to it.
 */
interface ResinTriangleProps {
  code: string; // "1".."7" or "?"
  confidence: number | null; // 0-1, or null for unknown
  color: string;
  size?: number;
}

export function ResinTriangle({ code, confidence, color, size = 120 }: ResinTriangleProps) {
  const c = confidence ?? 0;
  const isUncertain = confidence === null || confidence < 0.45;
  const fillOpacity = isUncertain ? 0 : 0.15 + c * 0.55;
  const strokeDash = isUncertain ? "6 5" : "none";
  const strokeColor = isUncertain ? "var(--color-uncertainty)" : color;
  const displayCode = isUncertain ? "?" : code;

  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 100 100"
      role="img"
      aria-label={isUncertain ? "Uncertain classification" : `Resin identification code ${code}`}
    >
      <path
        d="M50 6 L92 84 A10 10 0 0 1 83 94 L17 94 A10 10 0 0 1 8 84 Z"
        fill={strokeColor}
        fillOpacity={fillOpacity}
        stroke={strokeColor}
        strokeWidth="4"
        strokeDasharray={strokeDash}
        strokeLinejoin="round"
      />
      {/* recycling arrows suggestion, simplified */}
      <path
        d="M50 6 L92 84 A10 10 0 0 1 83 94 L17 94 A10 10 0 0 1 8 84 Z"
        fill="none"
        stroke={strokeColor}
        strokeOpacity="0.35"
        strokeWidth="1"
      />
      <text
        x="50"
        y="66"
        textAnchor="middle"
        fontSize="34"
        fontFamily="var(--font-mono), ui-monospace, monospace"
        fill={isUncertain ? "var(--color-uncertainty)" : "var(--color-text)"}
      >
        {displayCode}
      </text>
    </svg>
  );
}
