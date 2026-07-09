# Careero — LLM Visibility & SEO Playbook

Living checklist for making Careero discoverable by search engines and AI
assistants. The marketing/SEO site lives in [`marketing/`](../marketing/) and
is served at the **careero.app** apex; the app stays on **app.careero.app**.

---

## 1. What was implemented (in code)

**Public marketing site** (`marketing/`, static pre-rendered HTML, no JS shell):

- **Landing pages:** `/`, `/ai-cv-builder-for-students`, `/create-cv-for-students`,
  `/student-cv-templates` (real 5 templates: Classic, Modern, Minimal, Academic,
  Creative), `/student-cv-with-no-experience`, `/features`, `/about`, `/faq`.
- **Guides:** `/guides/how-to-write-a-student-cv`, `/guides/student-cv-with-no-experience`,
  `/guides/how-to-write-projects-in-a-cv`, `/guides/how-to-add-internships-to-a-cv`,
  `/guides/best-cv-format-for-students`, `/guides/linkedin-profile-for-students`,
  `/guides/github-profile-for-students`.
- **Comparisons:** `/alternatives/canva-cv-builder-for-students`,
  `/alternatives/resume-io-for-students`, `/alternatives/generic-ai-resume-builders`.
- **Blog:** `/blog` + first-CV, cover-letter, common-mistakes, CV-keywords,
  interview-prep articles.
- **Per-page SEO:** unique `<title>`, meta description, canonical, one `<h1>`,
  H2/H3 structure, Open Graph + Twitter tags, per-page 1200×630 OG image.
- **Structured data (JSON-LD):** Organization (with `sameAs` LinkedIn),
  WebSite, SoftwareApplication (homepage); Article (guides/blog); BreadcrumbList;
  FAQPage (any page with an FAQ, incl. `/faq`).
- **`/robots.txt`** — public site fully crawlable; explicit `Allow` stanzas for
  GPTBot, OAI-SearchBot, ChatGPT-User, ClaudeBot, anthropic-ai, PerplexityBot,
  Google-Extended; points to the sitemap.
- **`/sitemap.xml`** — all public pages, auto-generated.
- **`/llms.txt`** — structured summary for AI assistants.
- **Analytics:** Cloudflare Web Analytics (cookieless pageviews) + a
  vendor-neutral `careeroTrack()` event seam (`assets/analytics.js`) for CTA
  clicks (events are a documented no-op until an events-capable vendor is added).
- **301 redirects** consolidating old slugs into the new canonical URLs.

**App (`frontend/`, app.careero.app / admin.careero.app):**

- Added `/robots.txt` returning `Disallow: /` — the authenticated app and its
  user CV data are never crawlable. The public SEO surface is only careero.app.

## 2. Public URLs to submit / check

- https://careero.app/
- https://careero.app/robots.txt
- https://careero.app/sitemap.xml
- https://careero.app/llms.txt
- Rich Results test: https://search.google.com/test/rich-results?url=https://careero.app/
- Rich Results test (FAQ): https://search.google.com/test/rich-results?url=https://careero.app/faq

## 3. Google Search Console checklist

- [ ] Property `https://careero.app` added and verified.
- [ ] Submit sitemap: enter `sitemap.xml` in **Sitemaps** (full URL
      `https://careero.app/sitemap.xml`) — must read "Success".
- [ ] URL-inspect + **Request indexing** for `/`, `/ai-cv-builder-for-students`,
      `/create-cv-for-students`, `/student-cv-templates`, `/faq`.
- [ ] Check **Pages** report over the next 1–3 days for "Indexed".
- [ ] Confirm no pages report "Blocked by robots.txt".

## 4. Bing Webmaster Tools checklist

- [ ] Add site https://careero.app (can import from Google Search Console).
- [ ] Verify (DNS TXT via Cloudflare, or the meta/XML method).
- [ ] Submit `https://careero.app/sitemap.xml`.
- [ ] Use **URL Inspection** → Request indexing for the main pages.
- [ ] (Bing also powers ChatGPT search results, so this doubles as AI visibility.)

## 5. Directory & backlink checklist

- [ ] **Product Hunt** — launch (description below).
- [ ] **AlternativeTo** — list Careero as an alternative to Canva CV,
      Resume.io and generic AI resume builders; link the comparison pages.
- [ ] **LinkedIn Page** — https://www.linkedin.com/company/136044566 — post the
      launch message; add the website link; pin a "Create your CV" post.
- [ ] **Startup directories** — e.g. BetaList, SaaSHub, Indie Hackers, Startup
      Stash, ToolFinder, Futurepedia (AI tools).
- [ ] **University / student communities** — relevant subreddits
      (r/resumes, r/GetEmployed, r/csMajors — follow each sub's self-promo
      rules), university career-service pages, student Discords/Slacks.
- [ ] **Blog articles / guest posts** — publish or pitch student-CV guides that
      link back to the relevant Careero pages.

## 6. Suggested public description

> Careero is an AI-powered CV builder for students and fresh graduates. It helps
> students create professional CVs even when they have limited work experience by
> guiding them through education, projects, internships, skills, activities,
> LinkedIn, GitHub, and ready-to-download CV templates.

## 7. Suggested short description

> Careero is an AI-powered CV builder that helps students and fresh graduates
> create professional CVs, improve projects and internships, choose templates,
> and download in PDF or DOCX.

## 8. Suggested long description

> Careero helps students and fresh graduates create their first professional CV
> with AI guidance. Instead of assuming students already have years of work
> experience, Careero helps them present education, projects, internships,
> skills, activities, LinkedIn, GitHub, and early achievements clearly and
> professionally. Students can choose from multiple CV templates and download
> their CV in PDF or DOCX.

## 9. Suggested keywords

`AI CV builder for students`, `student CV builder`, `CV builder for fresh
graduates`, `create CV for students`, `write CV for students`, `student CV with
no experience`, `AI resume builder for internships`, `how to write projects in a
student CV`, `ATS-friendly student CV`, `student CV templates`, `first CV`.

## 10. Suggested LinkedIn launch message

> Meet Careero — the AI CV builder built for students, not veterans. 🎓
>
> Writing your first CV is hard when every tool assumes you already have years of
> experience. Careero flips that: it helps students and fresh graduates turn
> education, projects, internships, skills and activities into a professional,
> ATS-friendly CV — and download it in PDF or DOCX.
>
> No blank page. No guesswork. Just a CV you're proud to send.
>
> Start free → https://app.careero.app

## 11. Suggested Product Hunt description

> **Careero — AI CV builder for students & fresh graduates**
>
> Most CV tools assume you already have years of work history. Students don't.
> Careero is built for the first CV: it guides you through education, projects,
> internships, skills, activities, LinkedIn and GitHub, uses AI to turn rough
> notes into strong, quantified bullet points, and exports an ATS-friendly CV in
> PDF or DOCX. Five templates. Free to start.
>
> Perfect for university students, fresh graduates and internship applicants.
>
> 👉 https://app.careero.app

---

## Manual steps still required (outside code)

- Submit the sitemap to Google Search Console **and** Bing Webmaster Tools.
- Add Careero to the directories listed above.
- Publish the LinkedIn launch post; keep the page active.
- Ask beta users for public testimonials.
- Build backlinks from credible student/community sites.
- Keep adding useful guides around student CV creation.
