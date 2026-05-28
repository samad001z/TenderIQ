/** Drive the live web app via headless chromium and snapshot the gov-portal pages. */
import { chromium } from "playwright";
import { fileURLToPath } from "node:url";
import path from "node:path";
import fs from "node:fs";

const OUT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..", "..", "tests", "screenshots");
fs.mkdirSync(OUT, { recursive: true });

const BASE = "http://localhost:3000";
const EMAIL = "officer@tenderiq.test";
const PASS = "TenderIQ#2026";

(async () => {
  const browser = await chromium.launch({ headless: true });
  const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  const page = await ctx.newPage();

  // 0. Landing (root /)
  await page.goto(`${BASE}/`, { waitUntil: "networkidle" }).catch(() => {});
  await page.screenshot({ path: path.join(OUT, "00-landing.png"), fullPage: true });
  console.log("✔ /");

  // 1. Login page.
  await page.goto(`${BASE}/login`, { waitUntil: "networkidle" });
  await page.screenshot({ path: path.join(OUT, "01-login.png"), fullPage: true });
  console.log("✔ /login");

  // 1b. Signup page.
  await page.goto(`${BASE}/signup`, { waitUntil: "networkidle" });
  await page.screenshot({ path: path.join(OUT, "01b-signup.png"), fullPage: true });
  console.log("✔ /signup");

  // Back to /login to actually sign in.
  await page.goto(`${BASE}/login`, { waitUntil: "networkidle" });

  // 2. Sign in.
  await page.fill('input[type="email"]', EMAIL);
  await page.fill('input[type="password"]', PASS);
  await Promise.all([
    page.waitForURL(/officer|bidder|onboarding/, { timeout: 30000 }),
    page.click('button[type="submit"]'),
  ]);
  await page.waitForLoadState("networkidle");
  console.log("✔ signed in →", page.url());

  // 3. Dashboard.
  await page.goto(`${BASE}/officer/dashboard`, { waitUntil: "networkidle" });
  await page.screenshot({ path: path.join(OUT, "02-officer-dashboard.png"), fullPage: true });
  console.log("✔ /officer/dashboard");

  // 4. Tenders list.
  await page.goto(`${BASE}/officer/tenders`, { waitUntil: "networkidle" });
  await page.screenshot({ path: path.join(OUT, "03-officer-tenders.png"), fullPage: true });
  console.log("✔ /officer/tenders");

  // 5. Review page (already reviewed → shows matrix).
  await page.goto(`${BASE}/officer/tenders/24941876-6111-44af-bbff-e9cd793805c9/review`, { waitUntil: "networkidle" });
  // Wait for the ranking header to appear.
  await page.waitForSelector("text=/Recommended for award|HUMAN REVIEW REQUIRED|No bid recommended/i", { timeout: 20000 }).catch(() => {});
  await page.screenshot({ path: path.join(OUT, "04-officer-review.png"), fullPage: true });
  console.log("✔ /officer/tenders/[id]/review");

  await browser.close();
  console.log(`\nWrote to ${OUT}`);
})().catch((e) => {
  console.error(e);
  process.exit(1);
});
