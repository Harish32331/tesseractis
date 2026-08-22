"use client";

import { InputHTMLAttributes } from "react";

interface FieldProps extends InputHTMLAttributes<HTMLInputElement> {
  label: string;
  error?: string;
}

export function Field({ label, error, id, ...props }: FieldProps) {
  const fieldId = id || label.toLowerCase().replace(/\s+/g, "-");
  return (
    <div>
      <label htmlFor={fieldId} className="mb-1.5 block text-sm text-[var(--color-muted)]">
        {label}
      </label>
      <input
        id={fieldId}
        aria-invalid={!!error}
        aria-describedby={error ? `${fieldId}-error` : undefined}
        className="w-full rounded-md border border-[var(--color-border)] bg-[var(--color-card-raised)] px-3.5 py-2.5 text-sm text-[var(--color-text)] outline-none focus:border-[var(--color-uncertainty)]"
        {...props}
      />
      {error && (
        <p id={`${fieldId}-error`} className="mt-1.5 text-xs text-[var(--color-danger)]">
          {error}
        </p>
      )}
    </div>
  );
}
