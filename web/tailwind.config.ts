import type { Config } from "tailwindcss";
import tailwindcssAnimate from "tailwindcss-animate";

/**
 * TenderIQ design tokens — see docs/DESIGN_SYSTEM.md.
 * borderRadius is REPLACED (not extended) to cap container radius at 6px.
 * Spacing keeps Tailwind defaults (multiples of 4) and adds named scale tokens.
 */
const config: Config = {
  darkMode: "class",
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    // REPLACE radius scale — disables Tailwind's larger defaults (xl/2xl/3xl).
    borderRadius: {
      none: "0px",
      sm: "4px",
      DEFAULT: "5px",
      md: "5px",
      lg: "6px", // the cap for containers
      full: "9999px", // shape primitives only (dots, avatars)
    },
    extend: {
      colors: {
        // shadcn semantic slots, mapped directly to our palette (single dark theme).
        background: "#0B0D0F",
        foreground: "#F5F1E8",
        card: { DEFAULT: "#14171A", foreground: "#F5F1E8" },
        popover: { DEFAULT: "#1C2024", foreground: "#F5F1E8" },
        primary: { DEFAULT: "#C8A14A", foreground: "#0B0D0F" },
        secondary: { DEFAULT: "#1C2024", foreground: "#F5F1E8" },
        muted: { DEFAULT: "#14171A", foreground: "#9BA1A8" },
        accent: { DEFAULT: "#1C2024", foreground: "#F5F1E8" },
        destructive: { DEFAULT: "#E5484D", foreground: "#F5F1E8" },
        border: "#2A2F35",
        input: "#2A2F35",
        ring: "#C8A14A",
        // --- Government Procurement Portal palette (Phase 7) ---
        // Light, institutional. Used by the officer review workspace; bidder + auth
        // pages still use the obsidian/carbon dark variants below.
        gov: {
          bg: "#F4F6F9",          // page background
          surface: "#FFFFFF",     // cards / tables
          elevated: "#FBFCFE",    // raised surface (hover, drawer)
          border: "#D6DCE3",      // primary border
          "border-strong": "#B8C0CC",
          ink: "#0B2545",         // primary text — institutional navy
          "ink-muted": "#455A75",
          "ink-faint": "#6F8094",
          navy: "#003875",        // primary CTA / brand
          "navy-hover": "#00477E",
          "navy-press": "#002E63",
          saffron: "#FF9933",     // national saffron — used in tricolor strip + L1 emphasis
          green: "#138808",       // national green — used in tricolor strip + PASS emphasis
          maroon: "#7A1B2E",      // emblem / formal accent
          "maroon-soft": "#FBEDF0",
          "navy-soft": "#E8EEF6", // tinted strip / row hover
          "saffron-soft": "#FFF1E0",
          "green-soft": "#E6F4E0",
        },
        // --- Original obsidian dark tokens (auth, bidder portal) ---
        obsidian: { DEFAULT: "#0B0D0F", surface: "#14171A", elevated: "#1C2024" },
        // Bidder portal — slightly warmer dark variant.
        carbon: { DEFAULT: "#14110D", surface: "#1C1813", elevated: "#241F18" },
        smoke: { DEFAULT: "#2A2F35", strong: "#3A4047" },
        cream: { DEFAULT: "#F5F1E8", muted: "#9BA1A8", faint: "#5E646B" },
        gold: {
          DEFAULT: "#C8A14A",
          hover: "#D9B45E",
          press: "#B08B38",
          faint: "rgba(200,161,74,0.12)",
        },
        verdict: {
          pass: "#3FB950",
          fail: "#E5484D",
          flag: "#E0A23B",
          info: "#5B8DEF",
        },
        severity: {
          low: "#5B8DEF",
          medium: "#E0A23B",
          high: "#F0883E",
          critical: "#E5484D",
        },
      },
      fontFamily: {
        sans: ["var(--font-sans)", "var(--font-sans-deva)", "system-ui", "sans-serif"],
        serif: ["var(--font-serif)", "var(--font-serif-deva)", "Georgia", "serif"],
        mono: ["var(--font-mono)", "ui-monospace", "SFMono-Regular", "monospace"],
      },
      spacing: {
        // Named scale tokens (px) — the only allowed steps. See DESIGN_SYSTEM §3.
        "space-1": "4px",
        "space-2": "8px",
        "space-3": "12px",
        "space-4": "16px",
        "space-5": "24px",
        "space-6": "32px",
        "space-7": "48px",
        "space-8": "64px",
        "space-9": "96px",
      },
      maxWidth: { content: "1440px" },
      boxShadow: {
        hair: "0 1px 2px rgba(0,0,0,0.4)",
        // Gov-portal surfaces (modern, subtle — Stripe-like).
        "gov-sm": "0 1px 2px 0 rgba(11,37,69,0.04), 0 1px 1px 0 rgba(11,37,69,0.03)",
        "gov-md": "0 1px 3px 0 rgba(11,37,69,0.06), 0 4px 8px -2px rgba(11,37,69,0.05)",
        "gov-lg": "0 4px 12px -2px rgba(11,37,69,0.08), 0 10px 20px -5px rgba(11,37,69,0.06)",
        "gov-ring": "0 0 0 4px rgba(0,56,117,0.10)",
      },
      keyframes: {
        "pulse-dot": {
          "0%, 100%": { opacity: "1", transform: "scale(1)" },
          "50%": { opacity: "0.4", transform: "scale(0.82)" },
        },
      },
      animation: {
        "pulse-dot": "pulse-dot 1.4s ease-in-out infinite",
      },
    },
  },
  plugins: [tailwindcssAnimate],
};

export default config;
