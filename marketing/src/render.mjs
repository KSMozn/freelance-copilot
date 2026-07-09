// Rendering layer: turns a page object (see pages.mjs) into a complete,
// pre-rendered HTML document. No client framework — the HTML IS the content.

import { nav, site } from "./site.mjs";

const esc = (s = "") =>
  String(s)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");

// Canonical absolute URL for an internal path ("" → homepage).
export const absUrl = (path = "") => {
  if (!path || path === "/") return site.origin + "/";
  const clean = path.startsWith("/") ? path : `/${path}`;
  return site.origin + clean;
};

const isInternal = (href) => href.startsWith("/") || href.startsWith("#");

// ---- inline brand mark (self-contained SVG, matches app.careero.app) -------
const brandMark = (size = 30) => `
<svg viewBox="0 0 64 64" width="${size}" height="${size}" aria-hidden="true" class="brand-mark">
  <defs>
    <linearGradient id="cg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="${site.brand.from}"/>
      <stop offset="55%" stop-color="${site.brand.mid}"/>
      <stop offset="100%" stop-color="${site.brand.to}"/>
    </linearGradient>
  </defs>
  <path d="M 46.6 21.4 A 18 18 0 1 0 46.6 42.6" fill="none" stroke="url(#cg)"
        stroke-width="7.5" stroke-linecap="round"/>
  <path d="M 46 32 L 50 30 L 46 28 L 44 24 L 42 28 L 38 30 L 42 32 L 44 36 Z"
        fill="url(#cg)"/>
</svg>`;

// ---- primary CTA -----------------------------------------------------------
export const cta = (text, href = site.appUrl, cls = "btn btn-primary") => {
  const ext = !isInternal(href);
  const attrs = ext ? ' rel="noopener"' : "";
  return `<a class="${cls}" href="${esc(href)}"${attrs}>${esc(text)}</a>`;
};

// ---- header / nav ----------------------------------------------------------
const navGroup = (group) => `
  <li class="nav-item">
    <button type="button" class="nav-trigger" aria-haspopup="true" aria-expanded="false">
      ${esc(group.label)}<span class="caret" aria-hidden="true">▾</span>
    </button>
    <ul class="nav-menu">
      ${group.items
        .map((it) => {
          const ext = !isInternal(it.href);
          return `<li><a href="${esc(it.href)}"${
            ext ? ' rel="noopener"' : ""
          }>${esc(it.label)}</a></li>`;
        })
        .join("")}
    </ul>
  </li>`;

const header = () => `
<header class="site-header">
  <div class="container header-inner">
    <a class="brand" href="/" aria-label="Careero home">
      ${brandMark(30)}<span class="brand-word">Careero</span>
    </a>
    <input type="checkbox" id="nav-toggle" class="nav-toggle" aria-hidden="true">
    <label for="nav-toggle" class="nav-burger" aria-label="Toggle navigation">
      <span></span><span></span><span></span>
    </label>
    <nav class="site-nav" aria-label="Primary">
      <ul class="nav-list">
        ${nav.map(navGroup).join("")}
      </ul>
      <div class="nav-actions">
        <a class="btn btn-ghost" href="${esc(site.loginUrl)}" rel="noopener">Login</a>
        <a class="btn btn-primary" href="${esc(site.appUrl)}" rel="noopener">Start Free</a>
      </div>
    </nav>
  </div>
</header>`;

const footer = () => {
  const cols = nav
    .map(
      (g) => `
      <div class="foot-col">
        <h4>${esc(g.label)}</h4>
        <ul>${g.items
          .map(
            (it) =>
              `<li><a href="${esc(it.href)}"${
                isInternal(it.href) ? "" : ' rel="noopener"'
              }>${esc(it.label)}</a></li>`,
          )
          .join("")}</ul>
      </div>`,
    )
    .join("");
  return `
<footer class="site-footer">
  <div class="container">
    <div class="foot-grid">
      <div class="foot-brand">
        <a class="brand" href="/" aria-label="Careero home">${brandMark(28)}<span class="brand-word">Careero</span></a>
        <p>${esc(site.description)}</p>
        ${cta("Create your CV now", site.appUrl, "btn btn-primary")}
      </div>
      ${cols}
    </div>
    <div class="foot-bottom">
      <span>© ${new Date().getUTCFullYear()} Careero. A PersonaArmory product.</span>
      <span><a href="/sitemap.xml">Sitemap</a></span>
    </div>
  </div>
</footer>`;
};

// ---- content blocks --------------------------------------------------------
const bulletList = (items = []) =>
  items.length
    ? `<ul class="ticks">${items
        .map((b) => `<li>${b}</li>`)
        .join("")}</ul>`
    : "";

const renderHero = (b) => `
<section class="hero">
  <div class="container hero-inner">
    ${b.kicker ? `<p class="kicker">${esc(b.kicker)}</p>` : ""}
    <h1>${esc(b.h1)}</h1>
    ${b.lead ? `<p class="lead">${b.lead}</p>` : ""}
    <div class="hero-cta">
      ${cta(b.primaryCta?.text || "Start your student CV", b.primaryCta?.href)}
      ${
        b.secondaryCta
          ? cta(b.secondaryCta.text, b.secondaryCta.href, "btn btn-ghost")
          : ""
      }
    </div>
    ${b.note ? `<p class="hero-note">${b.note}</p>` : ""}
    ${b.bullets ? `<div class="hero-bullets">${bulletList(b.bullets)}</div>` : ""}
  </div>
</section>`;

const renderProse = (b) => `
<section class="section"${b.id ? ` id="${esc(b.id)}"` : ""}>
  <div class="container narrow">
    <h2>${esc(b.h2)}</h2>
    ${(b.paragraphs || []).map((p) => `<p>${p}</p>`).join("")}
    ${bulletList(b.bullets)}
    ${(b.subsections || [])
      .map(
        (s) =>
          `<h3>${esc(s.h3)}</h3>${(s.paragraphs || [])
            .map((p) => `<p>${p}</p>`)
            .join("")}${bulletList(s.bullets)}`,
      )
      .join("")}
  </div>
</section>`;

const renderCards = (b) => `
<section class="section"${b.id ? ` id="${esc(b.id)}"` : ""}>
  <div class="container">
    <h2>${esc(b.h2)}</h2>
    ${b.intro ? `<p class="section-intro">${b.intro}</p>` : ""}
    <div class="card-grid">
      ${b.items
        .map(
          (it) => `
        <div class="card">
          ${it.icon ? `<div class="card-icon">${it.icon}</div>` : ""}
          <h3>${esc(it.title)}</h3>
          <p>${it.text}</p>
          ${it.href ? `<a class="card-link" href="${esc(it.href)}">Learn more →</a>` : ""}
        </div>`,
        )
        .join("")}
    </div>
  </div>
</section>`;

const renderSteps = (b) => `
<section class="section"${b.id ? ` id="${esc(b.id)}"` : ""}>
  <div class="container narrow">
    <h2>${esc(b.h2)}</h2>
    ${b.intro ? `<p class="section-intro">${b.intro}</p>` : ""}
    <ol class="steps">
      ${b.items
        .map(
          (s) =>
            `<li><h3>${esc(s.title)}</h3><p>${s.text}</p></li>`,
        )
        .join("")}
    </ol>
  </div>
</section>`;

const renderFaq = (b) => `
<section class="section faq" id="faq">
  <div class="container narrow">
    <h2>${esc(b.h2 || "Frequently asked questions")}</h2>
    <div class="faq-list">
      ${b.items
        .map(
          (f) => `
        <details class="faq-item">
          <summary>${esc(f.q)}</summary>
          <div class="faq-a">${f.a}</div>
        </details>`,
        )
        .join("")}
    </div>
  </div>
</section>`;

const renderCtaBlock = (b) => `
<section class="section cta-band">
  <div class="container narrow cta-band-inner">
    <h2>${esc(b.h2)}</h2>
    ${b.text ? `<p>${b.text}</p>` : ""}
    ${cta(b.buttonText || "Try Careero for free", b.href || site.appUrl)}
  </div>
</section>`;

const RENDERERS = {
  hero: renderHero,
  prose: renderProse,
  cards: renderCards,
  steps: renderSteps,
  faq: renderFaq,
  cta: renderCtaBlock,
};

const renderBlocks = (blocks = []) =>
  blocks.map((b) => (RENDERERS[b.type] || (() => ""))(b)).join("\n");

// ---- structured data -------------------------------------------------------
const jsonLdScript = (obj) =>
  `<script type="application/ld+json">${JSON.stringify(obj)}</script>`;

const breadcrumbLd = (page) => {
  if (!page.slug) return null;
  const parts = page.slug.split("/").filter(Boolean);
  const items = [{ name: "Home", url: absUrl("/") }];
  let acc = "";
  parts.forEach((p, i) => {
    acc += `/${p}`;
    const isLast = i === parts.length - 1;
    items.push({ name: isLast ? page.h1 || page.title : titleCase(p), url: absUrl(acc) });
  });
  return {
    "@context": "https://schema.org",
    "@type": "BreadcrumbList",
    itemListElement: items.map((it, i) => ({
      "@type": "ListItem",
      position: i + 1,
      name: it.name,
      item: it.url,
    })),
  };
};

const titleCase = (s) =>
  s.replace(/-/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());

const faqLdFromBlocks = (page) => {
  const faq = (page.blocks || []).find((b) => b.type === "faq");
  if (!faq) return null;
  return {
    "@context": "https://schema.org",
    "@type": "FAQPage",
    mainEntity: faq.items.map((f) => ({
      "@type": "Question",
      name: f.q,
      acceptedAnswer: { "@type": "Answer", text: stripTags(f.a) },
    })),
  };
};

const stripTags = (html = "") =>
  html.replace(/<[^>]+>/g, "").replace(/\s+/g, " ").trim();

const organizationLd = () => ({
  "@context": "https://schema.org",
  "@type": "Organization",
  name: "Careero",
  url: site.origin + "/",
  logo: absUrl("/icon.svg"),
  description: site.description,
  sameAs: [site.appUrl],
});

const websiteLd = () => ({
  "@context": "https://schema.org",
  "@type": "WebSite",
  name: "Careero",
  url: site.origin + "/",
  description: site.description,
});

const articleLd = (page) => ({
  "@context": "https://schema.org",
  "@type": "Article",
  headline: page.h1 || page.title,
  description: page.description,
  datePublished: page.datePublished,
  dateModified: page.dateModified || page.datePublished,
  author: { "@type": "Organization", name: "Careero" },
  publisher: {
    "@type": "Organization",
    name: "Careero",
    logo: { "@type": "ImageObject", url: absUrl("/icon.svg") },
  },
  mainEntityOfPage: { "@type": "WebPage", "@id": absUrl(page.slug) },
  image: absUrl(page.ogImage || "/og-default.png"),
});

const buildJsonLd = (page) => {
  const blocks = [];
  if (!page.slug) {
    blocks.push(organizationLd(), websiteLd());
  } else if (page.type === "article") {
    blocks.push(articleLd(page));
  }
  const crumbs = breadcrumbLd(page);
  if (crumbs) blocks.push(crumbs);
  const faq = faqLdFromBlocks(page);
  if (faq) blocks.push(faq);
  (page.extraJsonLd || []).forEach((o) => blocks.push(o));
  return blocks.map(jsonLdScript).join("\n");
};

// ---- <head> ----------------------------------------------------------------
// Per-page OG image path: /og/<slug-with-dashes>.png (homepage -> /og/home.png).
// Pre-generated PNGs live in assets/og/. Falls back to the shared image.
export const ogImagePath = (slug) =>
  `/og/${slug ? slug.replace(/\//g, "-") : "home"}.png`;

const head = (page) => {
  const url = absUrl(page.slug);
  const ogImage = absUrl(page.ogImage || ogImagePath(page.slug));
  const ogType = page.type === "article" ? "article" : "website";
  return `
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>${esc(page.title)}</title>
  <meta name="description" content="${esc(page.description)}">
  <link rel="canonical" href="${esc(url)}">
  <meta name="robots" content="index, follow, max-image-preview:large">${
    site.googleSiteVerification
      ? `\n  <meta name="google-site-verification" content="${esc(site.googleSiteVerification)}">`
      : ""
  }
  <meta name="theme-color" content="${site.brand.from}">
  <link rel="icon" type="image/svg+xml" href="/icon.svg">
  <link rel="apple-touch-icon" href="/icon.svg">
  <link rel="stylesheet" href="/styles.css">
  <link rel="sitemap" type="application/xml" href="/sitemap.xml">
  <!-- Open Graph (LinkedIn / Facebook) -->
  <meta property="og:type" content="${ogType}">
  <meta property="og:site_name" content="Careero">
  <meta property="og:title" content="${esc(page.ogTitle || page.title)}">
  <meta property="og:description" content="${esc(page.description)}">
  <meta property="og:url" content="${esc(url)}">
  <meta property="og:image" content="${esc(ogImage)}">
  <meta property="og:image:type" content="image/png">
  <meta property="og:image:width" content="1200">
  <meta property="og:image:height" content="630">
  <meta property="og:image:alt" content="${esc(page.ogTitle || page.title)}">
  <meta property="og:locale" content="${site.locale}">
  ${
    page.type === "article"
      ? `<meta property="article:published_time" content="${esc(page.datePublished || "")}">
  <meta property="article:modified_time" content="${esc(page.dateModified || page.datePublished || "")}">`
      : ""
  }
  <!-- Twitter -->
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="${esc(page.ogTitle || page.title)}">
  <meta name="twitter:description" content="${esc(page.description)}">
  <meta name="twitter:image" content="${esc(ogImage)}">
  ${buildJsonLd(page)}`;
};

// Cookieless Cloudflare Web Analytics beacon (only when a token is configured).
const analytics = () =>
  site.cloudflareAnalyticsToken
    ? `<script defer src="https://static.cloudflareinsights.com/beacon.min.js" data-cf-beacon='{"token": "${site.cloudflareAnalyticsToken}"}'></script>`
    : "";

// ---- full document ---------------------------------------------------------
export const renderPage = (page) => `<!doctype html>
<html lang="en">
<head>${head(page)}
</head>
<body>
${header()}
<main id="main">
${renderBlocks(page.blocks)}
</main>
${footer()}
${analytics()}
</body>
</html>`;
