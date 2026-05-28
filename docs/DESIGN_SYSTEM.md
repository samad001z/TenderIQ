# TenderIQ — DESIGN_SYSTEM.md

> ⚠️ **PROVENANCE NOTE (read me):** This file was **authored by Claude from the Phase 0 constraints** (obsidian + gold + cream; Cormorant Garamond / DM Sans / JetBrains Mono; spacing 4→96; radius ≤6px; gold is the only accent). The real DESIGN_SYSTEM.md was not pasted before Phase 1. **Paste the canonical version to override** — swapping the hex tokens below is a ~5-minute edit in `web/tailwind.config.ts` + `web/app/globals.css`. Until then, these are the source of truth the build uses.

Vibe: **Bloomberg terminal × Linear × Stripe Dashboard.** Dense, calm, audit-grade. Information first, decoration never.

---

## 1. Color tokens

### Surfaces (obsidian family) — dark, near-black, faint cool cast
| Token | Hex | Use |
|---|---|---|
| `obsidian` (bg) | `#0B0D0F` | app background, sidebar |
| `obsidian-surface` | `#14171A` | cards, panels |
| `obsidian-elevated` | `#1C2024` | popovers, hover rows, inputs |
| `smoke` (border) | `#2A2F35` | hairline borders, dividers, topbar border-bottom |
| `smoke-strong` | `#3A4047` | focus borders, stronger separators |

### Text (cream family)
| Token | Hex | Use |
|---|---|---|
| `cream` | `#F5F1E8` | primary text, headings |
| `cream-muted` | `#9BA1A8` | secondary text, labels |
| `cream-faint` | `#5E646B` | tertiary, placeholders, disabled |

### Accent — **GOLD is the ONLY accent** (brand, primary action, active nav, focus glow)
| Token | Hex | Use |
|---|---|---|
| `gold` | `#C8A14A` | primary buttons, active nav strip, links, status dot |
| `gold-hover` | `#D9B45E` | hover state |
| `gold-press` | `#B08B38` | active/pressed |
| `gold-faint` | `rgba(200,161,74,0.12)` | subtle gold fills (active row tint, pill bg) |

### Semantic / status — **functional state colors, NOT decorative accents** (verdict pills, severity). Documented exception to "gold only": a review tool must distinguish PASS/FAIL at a glance.
| Token | Hex | Meaning |
|---|---|---|
| `verdict-pass` | `#3FB950` | PASS (green) |
| `verdict-fail` | `#E5484D` | FAIL (red) |
| `verdict-flag` | `#E0A23B` | FLAG (amber — distinct from brand gold) |
| `verdict-info` | `#5B8DEF` | INFO (slate blue) |

Each verdict also has a `-faint` background at ~12% alpha for pill fills.

### Severity (used by agents on findings)
| Token | Hex |
|---|---|
| `severity-low` | `#5B8DEF` |
| `severity-medium` | `#E0A23B` |
| `severity-high` | `#F0883E` |
| `severity-critical` | `#E5484D` |

---

## 2. Typography

| Family | Font | Role |
|---|---|---|
| `font-serif` | **Cormorant Garamond** (next/font, Latin + Devanagari) | display / hero / large headings only |
| `font-sans` | **DM Sans** (next/font, Latin + Devanagari) | all UI, body, labels, buttons |
| `font-mono` | **JetBrains Mono** (next/font, Latin) | numeric cells, page numbers, citations, code, IDs |

Devanagari subset on serif + sans now so Hindi tender text renders later without a refactor.

**Type scale** (DM Sans unless noted):
- `display` — Cormorant 48px / 1.1 / 500 (hero)
- `h1` — Cormorant 32px / 1.15 / 500
- `h2` — DM Sans 22px / 1.25 / 600
- `h3` — DM Sans 16px / 1.4 / 600
- `body` — DM Sans 14px / 1.55 / 400
- `small` — DM Sans 13px / 1.5 / 400
- `label` — DM Sans 12px / 1.4 / 500, tracking +0.02em, often uppercase for section labels
- `mono` — JetBrains Mono 13px (tabular-nums for numeric columns)

---

## 3. Spacing scale (the ONLY allowed steps)

`4 · 8 · 12 · 16 · 24 · 32 · 48 · 64 · 96` (px)

Exposed as named Tailwind tokens so intent is explicit, and they coincide with default Tailwind steps `1/2/3/4/6/8/12/16/24` (all multiples of 4):

| Token | px | Tailwind default equivalent |
|---|---|---|
| `space-1` | 4 | `1` |
| `space-2` | 8 | `2` |
| `space-3` | 12 | `3` |
| `space-4` | 16 | `4` |
| `space-5` | 24 | `6` |
| `space-6` | 32 | `8` |
| `space-7` | 48 | `12` |
| `space-8` | 64 | `16` |
| `space-9` | 96 | `24` |

Use these steps only. Avoid 20/28/36/40/44/etc.

---

## 4. Border radius — **4–6px MAX**

| Token | px | Use |
|---|---|---|
| `rounded-sm` | 4 | pills, inputs, small chips |
| `rounded-md` | 5 | buttons |
| `rounded-lg` | 6 | cards, panels (the cap) |
| `rounded-full` | 9999 | **shape primitives only** — status dots, avatars (not containers) |

Larger Tailwind radii (`xl`, `2xl`, `3xl`) are removed. No oversized rounded pills.

---

## 5. Layout shell

- **Sidebar:** 240px wide, `obsidian` bg, `smoke` right border. Active item gets a 2px `gold` left strip + `gold-faint` row tint + `cream` text; inactive `cream-muted`.
- **Topbar:** 56px tall, `obsidian` bg, `smoke` border-bottom (1px). Holds page title (DM Sans h3) + right-aligned actions.
- **Content:** centered, `max-width: 1440px`, padding `space-6` (32px) horizontal.
- Hairline borders everywhere (`1px solid smoke`); elevation via border + faint bg, not big shadows. Shadows are subtle (`0 1px 2px rgba(0,0,0,.4)` max).

---

## 6. Component conventions

- **Button / primary:** gold bg, obsidian text, `rounded-md`, h-36px (`space-1`-derived padding: 8/16), DM Sans 13px 600. Hover → `gold-hover`. Focus → 2px gold ring at low alpha.
- **Button / secondary:** transparent bg, `smoke` border, `cream` text. Hover → `obsidian-elevated`.
- **Input:** `obsidian-elevated` bg, `smoke` border, `cream` text, `cream-faint` placeholder, `rounded-sm`, focus → `gold` border.
- **Card:** `obsidian-surface` bg, `smoke` border, `rounded-lg`, padding `space-5` (24px).
- **Table row:** hairline `smoke` bottom border, hover → `obsidian-elevated`. Numeric columns use `font-mono` + `tabular-nums`, right-aligned.
- **Citation pill:** `obsidian-elevated` bg, `smoke` border, `rounded-sm`, `font-mono` 12px, shape `[ filename.pdf · p.NN ]`. Filename in `cream`, ` · p.NN ` in `gold`.
- **Verdict pill:** `rounded-sm`, `font-sans` 11px 600 uppercase, colored text on matching `-faint` bg + 1px matching border. PASS/FAIL/FLAG/INFO.
- **Agent card:** `obsidian-surface` panel, agent name (DM Sans 600), a **pulsing gold status dot** (`rounded-full`, 8px, `gold`, CSS `pulse` keyframe on opacity/scale) when running, status label in `cream-muted`.
- **Mono numeric cell:** JetBrains Mono, `tabular-nums`, `cream`, right-aligned.

## 7. Hard rules
- No emoji anywhere in product UI.
- No purple gradients. No gradients as decoration.
- Gold is the only brand accent; semantic verdict/severity colors are the sole exception and are functional.
- Radius never exceeds 6px on containers.
- Spacing only from the scale in §3.
