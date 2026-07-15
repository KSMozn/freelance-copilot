// Per-page Open Graph image generator (LOCAL tool — needs Chrome, which the
// Docker build image doesn't have). Produces a 1200x630 PNG per page into
// assets/og/, which are committed and copied verbatim by build.mjs.
//
// Run from the marketing/ dir:  node tools/og-gen.mjs
// Re-run whenever you add pages or change an H1.

import { execFileSync } from "node:child_process";
import { mkdirSync, rmSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

import { buildFacetPages } from "../src/facets.mjs";
import { pages } from "../src/pages.mjs";
import { site } from "../src/site.mjs";

// Bespoke OG images for the authored pages + the generated field-base "hubs".
// The long-tail {field}/{goal} pages fall back to the shared default OG
// (render.mjs), so we don't render dozens of near-identical share cards.
const fieldBaseHubs = buildFacetPages(
  new Set(pages.map((p) => p.slug)),
).pages.filter((p) => !p.slug.includes("/"));

const __dirname = dirname(fileURLToPath(import.meta.url));
const OUT = join(__dirname, "../assets/og");
const TMP = join(__dirname, "../.ogtmp");
const CHROME =
  process.env.CHROME ||
  "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";

const xml = (s = "") =>
  String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");

// Decode the handful of HTML entities that appear in H1 text so the OG image
// shows real characters, not entity codes.
const deent = (s = "") =>
  s
    .replace(/&amp;/g, "&")
    .replace(/&ldquo;|&rdquo;/g, '"')
    .replace(/&rsquo;/g, "'");

function wrap(text, max, maxLines) {
  const words = text.split(/\s+/);
  const lines = [];
  let line = "";
  for (const w of words) {
    if ((line + " " + w).trim().length > max && line) {
      lines.push(line);
      line = w;
    } else {
      line = (line + " " + w).trim();
    }
  }
  if (line) lines.push(line);
  if (lines.length > maxLines) {
    lines.length = maxLines;
    lines[maxLines - 1] += "…";
  }
  return lines;
}

const keyFor = (slug) => (slug ? slug.replace(/\//g, "-") : "home");

function svgFor(page) {
  const hero = (page.blocks || []).find((b) => b.type === "hero");
  const kicker = xml((hero?.kicker || site.tagline).toUpperCase());
  const h1 = deent(page.h1 || page.title);
  const lines = wrap(h1, 24, 3);
  const fs = lines.length >= 3 ? 58 : 64;
  const startY = 330 - (lines.length - 1) * (fs * 0.5);
  const textEls = lines
    .map(
      (ln, i) =>
        `<text x="96" y="${startY + i * (fs + 12)}" font-family="ui-sans-serif, system-ui, Segoe UI, Roboto, Arial, sans-serif" font-size="${fs}" font-weight="700" fill="#ffffff">${xml(ln)}</text>`,
    )
    .join("\n  ");
  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 630" width="1200" height="630">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#0f172a"/><stop offset="100%" stop-color="#1e1b4b"/>
    </linearGradient>
    <linearGradient id="g" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="${site.brand.from}"/><stop offset="55%" stop-color="${site.brand.mid}"/><stop offset="100%" stop-color="${site.brand.to}"/>
    </linearGradient>
  </defs>
  <rect width="1200" height="630" fill="url(#bg)"/>
  <circle cx="1080" cy="110" r="340" fill="#6C5CE7" opacity="0.16"/>
  <g transform="translate(96,120)">
    <path d="M 61 13 A 37 37 0 1 0 61 87" fill="none" stroke="url(#g)" stroke-width="15" stroke-linecap="round"/>
    <path d="M 60 50 L 69 46 L 60 42 L 56 33 L 52 42 L 43 46 L 52 50 L 56 59 Z" fill="url(#g)"/>
    <text x="100" y="62" font-family="ui-sans-serif, system-ui, Segoe UI, Roboto, Arial, sans-serif" font-size="46" font-weight="700" fill="#ffffff">Careero</text>
  </g>
  <text x="96" y="248" font-family="ui-sans-serif, system-ui, Segoe UI, Roboto, Arial, sans-serif" font-size="26" font-weight="600" letter-spacing="1" fill="#8B5CF6">${kicker}</text>
  ${textEls}
  <text x="96" y="560" font-family="ui-sans-serif, system-ui, Segoe UI, Roboto, Arial, sans-serif" font-size="28" font-weight="400" fill="#94a3b8">AI CV Builder for Students · PDF &amp; DOCX · ATS-friendly</text>
</svg>`;
}

function main() {
  rmSync(TMP, { recursive: true, force: true });
  mkdirSync(TMP, { recursive: true });
  mkdirSync(OUT, { recursive: true });

  let n = 0;
  const selectedPages = process.env.OG_SLUG
    ? [...pages, ...fieldBaseHubs].filter(
        (page) => page.slug === process.env.OG_SLUG,
      )
    : [...pages, ...fieldBaseHubs];
  if (selectedPages.length === 0) {
    throw new Error(`Unknown OG_SLUG: ${process.env.OG_SLUG}`);
  }
  for (const page of selectedPages) {
    const key = keyFor(page.slug);
    const svgPath = join(TMP, `${key}.svg`);
    writeFileSync(svgPath, svgFor(page), "utf8");
    execFileSync(
      CHROME,
      [
        "--headless=new",
        "--disable-gpu",
        "--hide-scrollbars",
        "--force-device-scale-factor=1",
        "--window-size=1200,630",
        `--screenshot=${join(OUT, `${key}.png`)}`,
        `file://${svgPath}`,
      ],
      { stdio: "ignore" },
    );
    n += 1;
  }
  rmSync(TMP, { recursive: true, force: true });
  console.log(`Generated ${n} per-page OG images → assets/og/`);
}

main();
