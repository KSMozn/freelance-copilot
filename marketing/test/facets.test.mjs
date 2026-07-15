// Unit tests for the pure facet helpers (paths, titles, descriptions, matrix).
// Run with `npm test` (node --test). No DOM, no network — pure functions.

import assert from "node:assert/strict";
import { test } from "node:test";

import {
  FIELDS,
  GOALS,
  buildFacetPages,
  fieldDescription,
  fieldGoalDescription,
  fieldGoalSlug,
  fieldGoalTitle,
  fieldSlug,
  fieldTitle,
} from "../src/facets.mjs";

const CS = FIELDS.find((f) => f.slug === "computer-science");
const NURSING = FIELDS.find((f) => f.slug === "nursing");
const INTERNSHIP = GOALS.find((g) => g.slug === "internship");

test("path builders produce clean, canonical-safe slugs (no query params)", () => {
  assert.equal(fieldSlug(CS), "cv-for-computer-science-students");
  assert.equal(
    fieldGoalSlug(CS, INTERNSHIP),
    "cv-for-computer-science-students/internship",
  );
  // No locale prefix for the default locale.
  assert.equal(fieldSlug(CS, "en"), "cv-for-computer-science-students");
  // Forward-compatible: a non-default locale prefixes the path.
  assert.equal(fieldSlug(CS, "ar"), "ar/cv-for-computer-science-students");
  // Never any query string.
  for (const s of [fieldSlug(NURSING), fieldGoalSlug(NURSING, INTERNSHIP)]) {
    assert.ok(!s.includes("?"), `slug must not contain '?': ${s}`);
  }
});

test("base description names the FULL goal set (intent-framed, not boilerplate)", () => {
  const d = fieldDescription(CS);
  for (const g of GOALS) {
    assert.ok(d.includes(g.phrase), `base description should name goal '${g.phrase}'`);
  }
  assert.ok(d.length > 60 && d.length < 320, "description within a sane meta length");
});

test("facet description names its SINGLE goal, framed by intent", () => {
  const d = fieldGoalDescription(NURSING, INTERNSHIP);
  assert.ok(d.toLowerCase().includes("nursing"));
  assert.ok(d.includes(INTERNSHIP.phrase));
  // It should not list every goal — it's the single-facet variant.
  const otherGoals = GOALS.filter((g) => g.slug !== INTERNSHIP.slug);
  const namesAll = otherGoals.every((g) => d.includes(g.phrase));
  assert.ok(!namesAll, "facet description must not enumerate the full goal set");
});

test("titles are unique per field and per field×goal", () => {
  const titles = new Set();
  for (const f of FIELDS) {
    const t = fieldTitle(f);
    assert.ok(!titles.has(t), `duplicate field title: ${t}`);
    titles.add(t);
    for (const g of GOALS) {
      const tg = fieldGoalTitle(f, g);
      assert.ok(!titles.has(tg), `duplicate facet title: ${tg}`);
      titles.add(tg);
    }
  }
});

test("buildFacetPages: correct count, dedupes authored bases, unique slugs", () => {
  const authored = new Set([
    "cv-for-computer-science-students",
    "cv-for-engineering-students",
    "cv-for-business-students",
  ]);
  const { pages, generated } = buildFacetPages(authored);
  assert.equal(pages.length, generated);

  const handAuthoredCount = FIELDS.filter((f) => f.handAuthoredBase).length;
  const expectedBases = FIELDS.length - handAuthoredCount;
  const expectedGoals = FIELDS.length * GOALS.length;
  assert.equal(generated, expectedBases + expectedGoals);

  // None of the authored base slugs are regenerated.
  for (const p of pages) assert.ok(!authored.has(p.slug), `regenerated authored slug ${p.slug}`);

  // All slugs unique.
  const slugs = pages.map((p) => p.slug);
  assert.equal(new Set(slugs).size, slugs.length, "facet slugs must be unique");
});

test("goal pages carry a 3-level breadcrumb trail and facet JSON-LD", () => {
  const { pages } = buildFacetPages(new Set());
  const goalPage = pages.find(
    (p) => p.slug === "cv-for-nursing-students/internship",
  );
  assert.ok(goalPage, "expected a nursing/internship page");
  assert.equal(goalPage.breadcrumbTrail.length, 2); // Field, Field+Goal (Home added in render)
  assert.equal(goalPage.breadcrumbTrail[0].slug, "cv-for-nursing-students");
  assert.equal(goalPage.breadcrumbTrail[1].slug, "cv-for-nursing-students/internship");
  assert.ok(Array.isArray(goalPage.extraJsonLd) && goalPage.extraJsonLd.length === 1);
  assert.equal(goalPage.extraJsonLd[0]["@type"], "WebPage");
  // No fabricated ratings/prices/counts in facet structured data.
  const json = JSON.stringify(goalPage.extraJsonLd[0]);
  for (const banned of ["aggregateRating", "ratingValue", "price", "offerCount"]) {
    assert.ok(!json.includes(banned), `facet JSON-LD must not invent ${banned}`);
  }
});

test("buildFacetPages honours a defensive cap", () => {
  const { pages, generated, skipped } = buildFacetPages(new Set(), { cap: 10 });
  assert.equal(pages.length, 10);
  assert.equal(generated, 10);
  assert.ok(skipped > 0, "pages beyond the cap are reported as skipped");
});

test("bases generated only for non-authored fields; every goal generated", () => {
  const { pages } = buildFacetPages(new Set());
  const slugs = new Set(pages.map((p) => p.slug));
  for (const f of FIELDS) {
    if (f.handAuthoredBase) {
      // Hand-authored bases (CS/engineering/business) are never regenerated —
      // they live in pages.mjs and win the dedupe.
      assert.ok(!slugs.has(fieldSlug(f)), `authored base wrongly regenerated: ${f.slug}`);
    } else {
      assert.ok(slugs.has(fieldSlug(f)), `missing generated base ${f.slug}`);
    }
    for (const g of GOALS)
      assert.ok(slugs.has(fieldGoalSlug(f, g)), `missing ${f.slug}/${g.slug}`);
  }
});
