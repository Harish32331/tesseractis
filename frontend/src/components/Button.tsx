"use client";

import { ButtonHTMLAttributes, forwardRef } from "react";

type Variant = "primary" | "secondary" | "ghost" | "danger";

const base =
  "inline-flex items-center justify-center gap-2 rounded-md font-medium transition-colors duration-150 disabled:opacity-50 disabled:cursor-not-allowed px-5 py-2.5 text-sm";

const variants: Record<Variant, string> = {
  primary: "bg-[var(--color-uncertainty)] text-[#12211f] hover:brightness-110 active:brightness-95",
  secondary: "bg-[var(--color-card-raised)] text-[var(--color-text)] border border-[var(--color-border)] hover:bg-[#2a4640]",
  ghost: "text-[var(--color-muted)] hover:text-[var(--color-text)]",
  danger: "bg-[var(--color-danger)] text-[#1b1210] hover:brightness-110",
};

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  loading?: boolean;
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ variant = "primary", loading, disabled, children, className = "", ...props }, ref) => (
    <button
      ref={ref}
      disabled={disabled || loading}
      className={`${base} ${variants[variant]} ${className}`}
      aria-busy={loading || undefined}
      {...props}
    >
      {loading && (
        <span className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-current border-t-transparent" aria-hidden="true" />
      )}
      {children}
    </button>
  )
);
Button.displayName = "Button";
