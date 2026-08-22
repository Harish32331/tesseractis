import type { Metadata } from "next";
import "./globals.css";
import { AuthProvider } from "@/features/auth/AuthContext";
import { Navbar } from "@/components/Navbar";

// NOTE: This build environment cannot reach fonts.googleapis.com, so we
// use curated system-font stacks (defined as CSS custom properties in
// globals.css) instead of next/font/google. Same type hierarchy and
// intent (a characterful geometric display face, a neutral body face,
// a monospace data face) — swap in the real webfonts in an environment
// with normal internet access by restoring next/font/google here.

export const metadata: Metadata = {
  title: "The Tesseractis — Identify plastic waste from a photograph",
  description:
    "Upload a photo of plastic waste. Get an AI-estimated material read, an honest confidence level, and recycling guidance — never a confident guess dressed up as certainty.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="h-full antialiased">
      <body className="min-h-full flex flex-col">
        <AuthProvider>
          <Navbar />
          <main className="flex-1">{children}</main>
        </AuthProvider>
      </body>
    </html>
  );
}
