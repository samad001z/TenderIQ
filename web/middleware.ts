import { createServerClient } from "@supabase/ssr";
import { NextResponse, type NextRequest } from "next/server";

import { homePathForRole } from "@/lib/auth";

/**
 * Refreshes the Supabase session cookie on every request AND enforces routing:
 *  - unauthenticated -> /login for /bidder, /officer, /onboarding
 *  - authenticated on /login|/signup -> their role home
 *  - authenticated but not onboarded -> /onboarding (when hitting protected routes)
 *  - role mismatch (bidder hitting /officer or vice versa) -> their own home
 *
 * role + onboarding_complete come from user_metadata (set at signup / onboarding)
 * — RLS in the DB is the real access boundary; this is just navigation.
 */
export async function middleware(request: NextRequest) {
  let supabaseResponse = NextResponse.next({ request });

  const supabase = createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        getAll() {
          return request.cookies.getAll();
        },
        setAll(cookiesToSet) {
          cookiesToSet.forEach(({ name, value }) => request.cookies.set(name, value));
          supabaseResponse = NextResponse.next({ request });
          cookiesToSet.forEach(({ name, value, options }) =>
            supabaseResponse.cookies.set(name, value, options),
          );
        },
      },
    },
  );

  const {
    data: { user },
  } = await supabase.auth.getUser();

  const path = request.nextUrl.pathname;
  const isAuthPage = path === "/login" || path === "/signup";
  const isOnboarding = path === "/onboarding";
  const isProtected = path.startsWith("/bidder") || path.startsWith("/officer");

  const role = (user?.user_metadata?.role as string | undefined) ?? undefined;
  const onboarded = Boolean(user?.user_metadata?.onboarding_complete);

  const redirect = (to: string) => {
    const url = request.nextUrl.clone();
    url.pathname = to;
    url.search = "";
    const res = NextResponse.redirect(url);
    // carry over any refreshed auth cookies
    supabaseResponse.cookies.getAll().forEach((c) => res.cookies.set(c));
    return res;
  };

  if (!user) {
    if (isProtected || isOnboarding) return redirect("/login");
    return supabaseResponse;
  }

  // Signed in.
  if (isAuthPage) return redirect(onboarded ? homePathForRole(role) : "/onboarding");
  if (onboarded && isOnboarding) return redirect(homePathForRole(role));
  if (!onboarded && isProtected) return redirect("/onboarding");

  if (onboarded && isProtected) {
    if (path.startsWith("/officer") && role !== "officer") return redirect("/bidder/tenders");
    if (path.startsWith("/bidder") && role !== "bidder") return redirect("/officer/dashboard");
  }

  return supabaseResponse;
}

export const config = {
  matcher: [
    "/((?!api/|_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp|ico)$).*)",
  ],
};
