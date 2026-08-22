"use client";

import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from "react";
import { api, ApiError } from "@/lib/api";
import type { UserPublic } from "@/types/api";

interface AuthContextValue {
  user: UserPublic | null;
  loading: boolean;
  refresh: () => Promise<void>;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserPublic | null>(null);
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    try {
      const me = await api.get<UserPublic>("/api/v1/auth/me");
      setUser(me);
    } catch {
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const me = await api.get<UserPublic>("/api/v1/auth/me");
        if (!cancelled) setUser(me);
      } catch {
        if (!cancelled) setUser(null);
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    const u = await api.post<UserPublic>("/api/v1/auth/login", { email, password });
    setUser(u);
  }, []);

  const register = useCallback(async (email: string, password: string) => {
    const u = await api.post<UserPublic>("/api/v1/auth/register", { email, password });
    setUser(u);
  }, []);

  const logout = useCallback(async () => {
    await api.post("/api/v1/auth/logout");
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider value={{ user, loading, refresh, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}

export function friendlyAuthError(err: unknown): string {
  if (err instanceof ApiError) {
    if (err.code === "INVALID_CREDENTIALS") return "Incorrect email or password.";
    if (err.code === "RATE_LIMITED") return "Too many attempts. Please wait a moment and try again.";
    if (err.code === "REGISTRATION_FAILED") return "We couldn't create that account. Try a different email.";
    return err.message;
  }
  return "Something went wrong. Please try again.";
}
