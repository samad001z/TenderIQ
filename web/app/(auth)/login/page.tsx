"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { createClient } from "@/lib/supabase/client";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    const supabase = createClient();
    const { error } = await supabase.auth.signInWithPassword({ email, password });
    if (error) {
      setError(error.message);
      setLoading(false);
      return;
    }
    // Root redirector sends the user to onboarding or their role home.
    router.push("/");
    router.refresh();
  }

  return (
    <div className="space-y-8">
      <div className="space-y-2">
        <h2 className="font-serif text-[32px] font-medium leading-tight text-cream">Sign in</h2>
        <p className="text-[13px] text-cream-muted">Welcome back to TenderIQ.</p>
      </div>

      <form onSubmit={onSubmit} className="space-y-4">
        <div className="space-y-2">
          <label className="font-sans text-[12px] font-medium text-cream-muted">Email</label>
          <Input
            type="email"
            autoComplete="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="you@department.gov.in"
          />
        </div>
        <div className="space-y-2">
          <label className="font-sans text-[12px] font-medium text-cream-muted">Password</label>
          <Input
            type="password"
            autoComplete="current-password"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="••••••••"
          />
        </div>

        {error && (
          <p className="rounded-sm border border-verdict-fail/40 bg-verdict-fail/10 px-3 py-2 text-[12px] text-verdict-fail">
            {error}
          </p>
        )}

        <Button type="submit" className="w-full" disabled={loading}>
          {loading ? "Signing in…" : "Sign in"}
        </Button>
      </form>

      <p className="text-[13px] text-cream-muted">
        New to TenderIQ?{" "}
        <Link href="/signup" className="text-gold hover:underline">
          Create an account
        </Link>
      </p>
    </div>
  );
}
