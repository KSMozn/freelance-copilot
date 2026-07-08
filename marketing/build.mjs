// Static-site generator for the Careero marketing site.
// Emits fully pre-rendered HTML (no client framework), plus sitemap.xml and
// robots.txt, into ./dist. Zero dependencies — run with `node build.mjs`.

import { cpSync, mkdirSync, rmSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

import { pages } from "./src/pages.mjs";
import { absUrl, renderPage } from "./src/render.mjs";
import { site } from "./src/site.mjs";

const __dirname = dirname(fileURLToPath(import.meta.url));
const DIST = join(__dirname, "dist");
const ASSETS = join(__dirname, "assets");

// Pretty URLs: "" -> /index.html, "a/b" -> /a/b/index.html. So every page is
// served at a clean directory path with no .html extension.
const outputPath = (slug) =>
  slug ? join(DIST, slug, "index.html") : join(DIST, "index.html");

const lastmod = "2026-07-08";

function priorityFor(slug) {
  if (!slug) return "1.0";
  if (slug.startsWith("blog/")) return "0.7";
  if (slug === "blog") return "0.6";
  return "0.8";
}

function buildSitemap() {
  const urls = pages
    .map(
      (p) => `  <url>
    <loc>${absUrl(p.slug)}</loc>
    <lastmod>${lastmod}</lastmod>
    <changefreq>weekly</changefreq>
    <priority>${priorityFor(p.slug)}</priority>
  </url>`,
    )
    .join("\n");
  return `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
${urls}
</urlset>
`;
}

function buildRobots() {
  // Everything is public and crawlable. Only point crawlers at the sitemap.
  return `User-agent: *
Allow: /

Sitemap: ${site.origin}/sitemap.xml
`;
}

function main() {
  rmSync(DIST, { recursive: true, force: true });
  mkdirSync(DIST, { recursive: true });

  // Static assets (styles.css, icons, og image) copied verbatim to the root.
  cpSync(ASSETS, DIST, { recursive: true });

  let count = 0;
  for (const page of pages) {
    const out = outputPath(page.slug);
    mkdirSync(dirname(out), { recursive: true });
    writeFileSync(out, renderPage(page), "utf8");
    count += 1;
  }

  writeFileSync(join(DIST, "sitemap.xml"), buildSitemap(), "utf8");
  writeFileSync(join(DIST, "robots.txt"), buildRobots(), "utf8");

  console.log(`Built ${count} pages + sitemap.xml + robots.txt → dist/`);
}

main();
