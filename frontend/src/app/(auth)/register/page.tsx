"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Card } from "@/components/Card";
import { Button } from "@/components/Button";
import { Field } from "@/components/Field";
import { useAuth, friendlyAuthError } from "@/features/auth/AuthContext";

function clientPasswordError(password: string): string | undefined {
  if (password.length === 0) return undefined;
  if (password.length < 10) return "Password must be at least 10 characters.";
  if (!/[A-Za-z]/.test(password) || !/[0-9]/.test(password)) return "Password must contain both letters and numbers.";
  return undefined;
}

export default function RegisterPage() {
  const { register } = useAuth();
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const passwordHint = clientPasswordError(password);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    if (passwordHint) {
      setError(passwordHint);
      return;
    }
    setLoading(true);
    try {
      await register(email, password);
      router.push("/dashboard");
    } catch (err) {
      setError(friendlyAuthError(err));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="mx-auto flex max-w-md flex-col px-6 py-20">
      <h1 className="font-display text-2xl">Create an account</h1>
      <Card className="mt-6 p-6">
        <form onSubmit={onSubmit} className="flex flex-col gap-4" noValidate>
          <Field
            label="Email"
            type="email"
            autoComplete="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
          <Field
            label="Password"
            type="password"
            autoComplete="new-password"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            error={passwordHint}
          />
          <p className="text-xs text-[var(--color-faint)]">At least 10 characters, with letters and numbers.</p>
          {error && !passwordHint && (
            <p role="alert" className="text-sm text-[var(--color-danger)]">
              {error}
            </p>
          )}
          <Button type="submit" loading={loading} className="mt-2 w-full">
            Sign up
          </Button>
        </form>
      </Card>
      <p className="mt-6 text-center text-sm text-[var(--color-muted)]">
        Already have an account?{" "}
        <Link href="/login" className="text-[var(--color-uncertainty)]">
          Log in
        </Link>
      </p>
    </div>
  );
}
