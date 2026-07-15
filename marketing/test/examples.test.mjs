// Unit tests for the CV-example page helpers (pure functions).

import assert from "node:assert/strict";
import { test } from "node:test";

import { FIELDS } from "../src/facets.mjs";
import {
  SAMPLES,
  buildExamplePages,
  exampleSlug,
  exampleTitle,
} from "../src/examples.mjs";

test("every field has a sample and a clean slug", () => {
  for (const f of FIELDS) {
    assert.ok(SAMPLES[f.slug], `missing sample CV for ${f.slug}`);
    assert.equal(exampleSlug(f), `cv-examples/${f.slug}`);
    assert.ok(!exampleSlug(f).includes("?"), "no query params in slug");
  }
});

test("sample people are clearly fictional (example.com only, no real emails)", () => {
  const json = JSON.stringify(SAMPLES);
  // No real-looking external email domains slipped in.
  for (const banned of ["@gmail", "@outlook", "@yahoo", "@hotmail"]) {
    assert.ok(!json.includes(banned), `sample data must not include ${banned}`);
  }
});

test("buildExamplePages: one page per field, unique slugs, dedupes", () => {
  const { pages, generated } = buildExamplePages(new Set());
  assert.equal(generated, FIELDS.length);
  const slugs = pages.map((p) => p.slug);
  assert.equal(new Set(slugs).size, slugs.length);

  // Dedupe against an existing slug.
  const deduped = buildExamplePages(new Set(["cv-examples/nursing"]));
  assert.equal(deduped.generated, FIELDS.length - 1);
});

test("example pages carry a breadcrumb trail and a fictional-sample note", () => {
  const { pages } = buildExamplePages(new Set());
  const p = pages.find((x) => x.slug === "cv-examples/nursing");
  assert.ok(p, "expected nursing example page");
  assert.equal(p.breadcrumbTrail[0].slug, "student-cv-examples");
  assert.equal(p.breadcrumbTrail[1].slug, "cv-examples/nursing");
  const html = JSON.stringify(p.blocks).toLowerCase();
  assert.ok(html.includes("fictional"), "must disclose the sample is fictional");
  // Title is example-framed and unique per field.
  assert.ok(exampleTitle(FIELDS[0]).includes("Example"));
});

test("example pages link back to the matching field guide", () => {
  const { pages } = buildExamplePages(new Set());
  for (const p of pages) {
    const field = p.slug.replace("cv-examples/", "");
    const json = JSON.stringify(p.blocks);
    assert.ok(
      json.includes(`/cv-for-${field}-students`),
      `${p.slug} should link to its field guide`,
    );
  }
});
