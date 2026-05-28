import type { Metadata } from "next";
import {
  Cormorant_Garamond,
  DM_Sans,
  JetBrains_Mono,
  Noto_Sans_Devanagari,
  Noto_Serif_Devanagari,
} from "next/font/google";

import "./globals.css";

// Latin display / UI / mono.
const serif = Cormorant_Garamond({
  variable: "--font-serif",
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
  display: "swap",
});
const sans = DM_Sans({ variable: "--font-sans", subsets: ["latin"], display: "swap" });
const mono = JetBrains_Mono({ variable: "--font-mono", subsets: ["latin"], display: "swap" });

// Devanagari companions (Cormorant Garamond + DM Sans have no Devanagari glyphs on
// Google Fonts). Wired into the font stacks so Hindi tender text renders later.
const serifDeva = Noto_Serif_Devanagari({
  variable: "--font-serif-deva",
  subsets: ["devanagari"],
  display: "swap",
});
const sansDeva = Noto_Sans_Devanagari({
  variable: "--font-sans-deva",
  subsets: ["devanagari"],
  display: "swap",
});

// Every TenderIQ route needs a Supabase session at request time, so opt the
// whole tree out of Next's static prerender. Without this, `next build`
// evaluates client modules at build time and trips on the publishable env
// vars before Vercel has injected them — making CI deploys brittle.
export const dynamic = "force-dynamic";

export const metadata: Metadata = {
  title: "TenderIQ",
  description:
    "AI-native, two-sided bidding & audit platform for Indian government procurement.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html
      lang="en"
      className={`${serif.variable} ${sans.variable} ${mono.variable} ${serifDeva.variable} ${sansDeva.variable}`}
    >
      <body>{children}</body>
    </html>
  );
}
