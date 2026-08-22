"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/features/auth/AuthContext";
import { Button } from "@/components/Button";

export function Navbar() {
  const { user, logout, loading } = useAuth();
  const pathname = usePathname();

  return (
    <header className="sticky top-0 z-40 border-b border-[var(--color-border)] bg-[var(--color-ink)]/90 backdrop-blur">
      <nav className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4" aria-label="Primary">
        <Link href="/" className="font-display text-lg tracking-tight text-[var(--color-text)]">
          THE TESSERACTIS
        </Link>
        <div className="flex items-center gap-6 text-sm">
          <Link
            href="/#how-it-works"
            className="hidden text-[var(--color-muted)] hover:text-[var(--color-text)] sm:inline"
          >
            How it works
          </Link>
          {!loading && user && (
            <>
              <Link
                href="/history"
                className={`hidden sm:inline ${pathname === "/history" ? "text-[var(--color-text)]" : "text-[var(--color-muted)] hover:text-[var(--color-text)]"}`}
              >
                History
              </Link>
              {user.role === "admin" && (
                <Link
                  href="/admin"
                  className={`hidden sm:inline ${pathname?.startsWith("/admin") ? "text-[var(--color-text)]" : "text-[var(--color-muted)] hover:text-[var(--color-text)]"}`}
                >
                  Admin
                </Link>
              )}
              <span className="hidden text-[var(--color-faint)] md:inline">{user.email}</span>
              <Button variant="secondary" onClick={() => logout()} className="!px-4 !py-2 text-xs">
                Log out
              </Button>
            </>
          )}
          {!loading && !user && (
            <>
              <Link href="/login" className="text-[var(--color-muted)] hover:text-[var(--color-text)]">
                Log in
              </Link>
              <Link href="/register">
                <Button className="!px-4 !py-2 text-xs">Sign up</Button>
              </Link>
            </>
          )}
        </div>
      </nav>
    </header>
  );
}
