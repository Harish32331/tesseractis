export interface MaterialMeta {
  label: string;
  ric: string; // resin identification code number, "?" if not applicable
  color: string; // CSS var reference
}

const MATERIAL_META: Record<string, MaterialMeta> = {
  PET: { label: "PET — Polyethylene Terephthalate", ric: "1", color: "var(--color-pet)" },
  HDPE: { label: "HDPE — High-Density Polyethylene", ric: "2", color: "var(--color-hdpe)" },
  PVC: { label: "PVC — Polyvinyl Chloride", ric: "3", color: "var(--color-ps)" },
  LDPE: { label: "LDPE — Low-Density Polyethylene", ric: "4", color: "var(--color-ldpe)" },
  PP: { label: "PP — Polypropylene", ric: "5", color: "var(--color-pp)" },
  PS: { label: "PS — Polystyrene", ric: "6", color: "var(--color-ps)" },
  "Multi-layer/Mixed": { label: "Mixed / Multi-layer plastic", ric: "7", color: "var(--color-unknown)" },
  UNKNOWN: { label: "Unable to determine", ric: "?", color: "var(--color-unknown)" },
};

export function getMaterialMeta(code: string): MaterialMeta {
  return MATERIAL_META[code] ?? { label: code, ric: "?", color: "var(--color-unknown)" };
}

export function confidenceBandLabel(band: string | null): string {
  switch (band) {
    case "high":
      return "High confidence";
    case "medium":
      return "Medium confidence";
    case "low":
      return "Low confidence — needs review";
    default:
      return "Unknown";
  }
}

export function confidenceBandColor(band: string | null): string {
  switch (band) {
    case "high":
      return "var(--color-success)";
    case "medium":
      return "var(--color-uncertainty)";
    case "low":
      return "var(--color-danger)";
    default:
      return "var(--color-unknown)";
  }
}
