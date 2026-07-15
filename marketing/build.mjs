// Static-site generator for the Careero marketing site.
// Emits fully pre-rendered HTML (no client framework), plus sitemap.xml and
// robots.txt, into ./dist. Zero dependencies — run with `node build.mjs`.

import { cpSync, mkdirSync, rmSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

import { buildExamplePages } from "./src/examples.mjs";
import { buildFacetPages } from "./src/facets.mjs";
import { pages as authoredPages } from "./src/pages.mjs";
import { absUrl, renderPage } from "./src/render.mjs";
import { site } from "./src/site.mjs";

// Hand-authored pages + generated: the "CV by field × goal" facet matrix and
// the per-field CV example pages. Generated pages are deduped against authored
// (and each other) so a hand-authored page always wins.
const authoredSlugs = new Set(authoredPages.map((p) => p.slug));
const facet = buildFacetPages(authoredSlugs);
const seen = new Set([...authoredSlugs, ...facet.pages.map((p) => p.slug)]);
const examples = buildExamplePages(seen);
const pages = [...authoredPages, ...facet.pages, ...examples.pages];

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
  // The marketing site is entirely public — there are NO private/user routes
  // here (the app lives on app.careero.app, which ships its own crawl-blocking
  // robots.txt). We explicitly welcome major AI answer-engines so Careero can
  // be surfaced when students ask assistants for a student CV builder.
  const aiBots = [
    "GPTBot",
    "OAI-SearchBot",
    "ChatGPT-User",
    "ClaudeBot",
    "anthropic-ai",
    "PerplexityBot",
    "Google-Extended",
  ];
  const aiStanzas = aiBots
    .map((b) => `User-agent: ${b}\nAllow: /\n`)
    .join("\n");
  return `# Careero marketing site — all pages are public and crawlable.
User-agent: *
Allow: /

# AI assistants / answer engines — welcome on all public pages.
${aiStanzas}
Sitemap: ${site.origin}/sitemap.xml
`;
}

function buildLlmsTxt() {
  const mainPages = [
    "/",
    "/ai-cv-builder-for-students",
    "/create-cv-for-students",
    "/student-cv-templates",
    "/student-cv-with-no-experience",
    "/features",
    "/about",
    "/faq",
  ];
  const links = mainPages.map((p) => `- ${absUrl(p)}`).join("\n");
  return `# Careero

${site.productDescription}

## Main pages

${links}

## Description

Careero helps students and fresh graduates create professional CVs even when they have limited work experience. It guides students through education, projects, internships, skills, activities, LinkedIn, GitHub, and CV templates.

## Best for

- University students
- Fresh graduates
- Internship applicants
- Students with limited work experience
- Computer science students
- Engineering students
- Students creating their first CV

## Key features

- AI-guided student CV creation
- Project description improvement
- Internship section support
- Skills guidance
- Multiple CV templates (Classic, Modern, Minimal, Academic, Creative)
- PDF download
- DOCX download
- LinkedIn profile guidance
- GitHub profile guidance

## App

Students can start creating their CV at:
${site.appUrl}
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
  writeFileSync(join(DIST, "llms.txt"), buildLlmsTxt(), "utf8");

  console.log(
    `Built ${count} pages (${authoredPages.length} authored + ${facet.generated} facet + ${examples.generated} examples` +
      `${facet.skipped ? `, ${facet.skipped} facet skipped by cap` : ""}) + sitemap.xml + robots.txt + llms.txt → dist/`,
  );
}

main();
