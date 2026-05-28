"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { homePathForRole, type Role } from "@/lib/auth";
import { createClient } from "@/lib/supabase/client";

export default function OnboardingPage() {
  const router = useRouter();
  const supabase = createClient();

  const [role, setRole] = useState<Role | null>(null);
  const [userId, setUserId] = useState<string | null>(null);
  const [form, setForm] = useState({
    org_name: "",
    gst_number: "",
    pan_number: "",
    ministry: "",
    department: "",
    phone: "",
  });
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    supabase.auth.getUser().then(({ data: { user } }) => {
      if (!user) {
        router.replace("/login");
        return;
      }
      setUserId(user.id);
      setRole(((user.user_metadata?.role as Role) ?? "bidder") as Role);
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const set = (k: keyof typeof form) => (e: React.ChangeEvent<HTMLInputElement>) =>
    setForm((f) => ({ ...f, [k]: e.target.value }));

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!userId || !role) return;
    setLoading(true);
    setError(null);

    const profilePatch =
      role === "officer"
        ? {
            org_name: form.org_name,
            ministry: form.ministry,
            department: form.department,
            phone: form.phone,
            onboarding_complete: true,
          }
        : {
            org_name: form.org_name,
            gst_number: form.gst_number,
            pan_number: form.pan_number,
            phone: form.phone,
            onboarding_complete: true,
          };

    const { error: dbError } = await supabase.from("profiles").update(profilePatch).eq("id", userId);
    if (dbError) {
      setError(dbError.message);
      setLoading(false);
      return;
    }
    // Mirror onboarding flag into user_metadata so middleware can gate without a DB hit.
    await supabase.auth.updateUser({ data: { onboarding_complete: true } });

    router.push(homePathForRole(role));
    router.refresh();
  }

  if (!role) {
    return <p className="text-[13px] text-cream-muted">Loading…</p>;
  }

  const isOfficer = role === "officer";

  return (
    <div className="space-y-8">
      <div className="space-y-2">
        <p className="font-mono text-[11px] uppercase tracking-wide text-gold">
          {isOfficer ? "Officer profile" : "Bidder profile"}
        </p>
        <h2 className="font-serif text-[32px] font-medium leading-tight text-cream">
          Complete your profile
        </h2>
        <p className="text-[13px] text-cream-muted">
          {isOfficer
            ? "Tell us which department you procure for."
            : "Add your firm’s registration details to bid."}
        </p>
      </div>

      <form onSubmit={onSubmit} className="space-y-4">
        <div className="space-y-2">
          <label className="font-sans text-[12px] font-medium text-cream-muted">
            {isOfficer ? "Organisation" : "Company name"}
          </label>
          <Input
            required
            value={form.org_name}
            onChange={set("org_name")}
            placeholder={isOfficer ? "Ministry of Road Transport & Highways" : "Meridian Infra Pvt Ltd"}
          />
        </div>

        {isOfficer ? (
          <>
            <div className="space-y-2">
              <label className="font-sans text-[12px] font-medium text-cream-muted">Ministry</label>
              <Input required value={form.ministry} onChange={set("ministry")} placeholder="MoRTH" />
            </div>
            <div className="space-y-2">
              <label className="font-sans text-[12px] font-medium text-cream-muted">Department</label>
              <Input
                required
                value={form.department}
                onChange={set("department")}
                placeholder="National Highways"
              />
            </div>
          </>
        ) : (
          <>
            <div className="space-y-2">
              <label className="font-sans text-[12px] font-medium text-cream-muted">GST number</label>
              <Input
                required
                value={form.gst_number}
                onChange={set("gst_number")}
                placeholder="27ABCDE1234F1Z5"
              />
            </div>
            <div className="space-y-2">
              <label className="font-sans text-[12px] font-medium text-cream-muted">PAN</label>
              <Input
                required
                value={form.pan_number}
                onChange={set("pan_number")}
                placeholder="ABCDE1234F"
              />
            </div>
          </>
        )}

        <div className="space-y-2">
          <label className="font-sans text-[12px] font-medium text-cream-muted">Phone</label>
          <Input
            type="tel"
            value={form.phone}
            onChange={set("phone")}
            placeholder="+91 90000 00000"
          />
        </div>

        {error && (
          <p className="rounded-sm border border-verdict-fail/40 bg-verdict-fail/10 px-3 py-2 text-[12px] text-verdict-fail">
            {error}
          </p>
        )}

        <Button type="submit" className="w-full" disabled={loading}>
          {loading ? "Saving…" : "Enter TenderIQ"}
        </Button>
      </form>
    </div>
  );
}
