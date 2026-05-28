"use client";

import { Building2, Gavel } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";
import { createClient } from "@/lib/supabase/client";

type Role = "bidder" | "officer";

const ROLES: { value: Role; label: string; blurb: string; icon: typeof Gavel }[] = [
  { value: "bidder", label: "Bidder", blurb: "Apply to tenders & submit bids", icon: Gavel },
  { value: "officer", label: "Officer", blurb: "Publish tenders & review bids", icon: Building2 },
];

export default function SignupPage() {
  const router = useRouter();
  const [role, setRole] = useState<Role>("bidder");
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setNotice(null);

    // Server route creates an auto-confirmed user (service role) so signup works
    // regardless of the Supabase "Confirm email" setting.
    const res = await fetch("/api/auth/signup", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password, role, full_name: fullName }),
    });
    const result = await res.json().catch(() => ({}));
    if (!res.ok) {
      setError(result.error ?? "Sign-up failed. Please try again.");
      setLoading(false);
      return;
    }

    // Establish the session client-side (sets cookies for middleware/SSR).
    const supabase = createClient();
    const { error: signInError } = await supabase.auth.signInWithPassword({ email, password });
    if (signInError) {
      setError(signInError.message);
      setLoading(false);
      return;
    }
    router.push("/onboarding");
    router.refresh();
  }

  return (
    <div className="space-y-8">
      <div className="space-y-2">
        <h2 className="font-serif text-[32px] font-medium leading-tight text-cream">
          Create your account
        </h2>
        <p className="text-[13px] text-cream-muted">Pick how you’ll use TenderIQ.</p>
      </div>

      <form onSubmit={onSubmit} className="space-y-4">
        {/* Role selector */}
        <div className="grid grid-cols-2 gap-3">
          {ROLES.map(({ value, label, blurb, icon: Icon }) => {
            const selected = role === value;
            return (
              <button
                type="button"
                key={value}
                onClick={() => setRole(value)}
                className={cn(
                  "flex flex-col items-start gap-2 rounded-md border p-3 text-left transition-colors",
                  selected
                    ? "border-gold bg-gold-faint"
                    : "border-smoke bg-obsidian-elevated hover:border-smoke-strong",
                )}
              >
                <Icon className={cn("size-4", selected ? "text-gold" : "text-cream-muted")} />
                <span className="font-sans text-[13px] font-semibold text-cream">{label}</span>
                <span className="text-[11px] leading-tight text-cream-muted">{blurb}</span>
              </button>
            );
          })}
        </div>

        <div className="space-y-2">
          <label className="font-sans text-[12px] font-medium text-cream-muted">Full name</label>
          <Input
            required
            value={fullName}
            onChange={(e) => setFullName(e.target.value)}
            placeholder={role === "officer" ? "Anita Deshpande" : "Your name"}
          />
        </div>
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
            autoComplete="new-password"
            required
            minLength={8}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="At least 8 characters"
          />
        </div>

        {error && (
          <p className="rounded-sm border border-verdict-fail/40 bg-verdict-fail/10 px-3 py-2 text-[12px] text-verdict-fail">
            {error}
          </p>
        )}
        {notice && (
          <p className="rounded-sm border border-verdict-info/40 bg-verdict-info/10 px-3 py-2 text-[12px] text-verdict-info">
            {notice}
          </p>
        )}

        <Button type="submit" className="w-full" disabled={loading}>
          {loading ? "Creating account…" : "Continue"}
        </Button>
      </form>

      <p className="text-[13px] text-cream-muted">
        Already have an account?{" "}
        <Link href="/login" className="text-gold hover:underline">
          Sign in
        </Link>
      </p>
    </div>
  );
}
