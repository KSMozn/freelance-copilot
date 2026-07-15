// examples.mjs — generates "/{field} student CV example" pages.
//
// Pure module (no server-only imports). Reuses FIELDS from facets.mjs as the
// single source of field names/slugs, and adds one realistic FICTIONAL sample
// CV per field. Every sample person is invented — no real personal data.
//
// Route: /cv-examples/{field}  (e.g. /cv-examples/nursing)

import { FIELDS } from "./facets.mjs";
import { site } from "./site.mjs";

const APP = site.appUrl;

// Fictional sample CVs, keyed by field slug. Kept realistic but clearly
// invented (generic names, example.com emails, no real institutions implied
// as endorsers). Each is genuinely field-specific — different education,
// projects, skills and experience — so pages are not templated duplicates.
export const SAMPLES = {
  "computer-science": {
    name: "Alex Rivera",
    headline: "Aspiring Software Engineer",
    summary:
      "Final-year computer science student who enjoys turning ideas into working software. Comfortable across the full stack and keen to keep shipping.",
    education:
      "BSc Computer Science, expected First — modules: Algorithms, Databases, Web Development, Machine Learning.",
    projects: [
      "Built a full-stack expense tracker in React, Node.js and MongoDB used by 30 classmates; added authentication and interactive charts.",
      "Created a CLI weather tool in Python that caches API responses, cutting repeat lookups by 80%.",
    ],
    experience:
      "Open-source: contributed three merged pull requests to a popular charting library.",
    skills: "JavaScript, TypeScript, React, Node.js, Python, SQL, Git, Docker",
  },
  engineering: {
    name: "Priya Nair",
    headline: "Mechanical Engineering Student",
    summary:
      "Third-year mechanical engineering student with hands-on design and simulation experience and a focus on efficient, safe design.",
    education:
      "BEng Mechanical Engineering, 2:1 expected — modules: Thermodynamics, Solid Mechanics, CAD, Materials.",
    projects: [
      "Designed and tested a load-bearing bracket in SolidWorks that cut mass 18% while meeting the required safety factor.",
      "Team lead on a Formula Student subsystem; ran FEA and presented results to faculty reviewers.",
    ],
    experience:
      "Two-week engineering insight placement: shadowed design engineers and documented a test rig procedure.",
    skills: "SolidWorks, MATLAB, FEA, technical drawing, prototyping, teamwork",
  },
  business: {
    name: "Sam O'Connor",
    headline: "Business & Management Student",
    summary:
      "Business student with society leadership and part-time experience, focused on turning activity into measurable results.",
    education:
      "BA Business Management, 2:1 expected — modules: Marketing, Finance, Operations, Strategy.",
    projects: [
      "As society treasurer, managed a £4k budget and cut event costs 15% by renegotiating supplier rates.",
      "Group consultancy project: delivered a market-entry recommendation adopted by a local startup client.",
    ],
    experience:
      "Retail sales assistant: handled 100+ transactions per shift and resolved complaints, improving repeat custom.",
    skills: "Excel, market research, budgeting, presenting, teamwork, leadership",
  },
  nursing: {
    name: "Maria Santos",
    headline: "Student Nurse",
    summary:
      "Compassionate nursing student with placement experience across surgical and community settings, committed to safe, patient-centred care.",
    education:
      "BSc Nursing (Adult), on track for 2:1 — modules: Anatomy & Physiology, Pharmacology, Evidence-Based Practice.",
    projects: [
      "Completed a 6-week surgical-ward placement supporting observations, medication rounds and discharge planning under supervision.",
      "Community placement: conducted supervised home visits and health-promotion sessions.",
    ],
    experience:
      "Healthcare assistant (bank): supported daily living activities and documented patient care accurately.",
    skills: "Patient observations, safeguarding awareness, BLS certified, clear communication, record-keeping",
  },
  law: {
    name: "Daniel Okafor",
    headline: "Law Student",
    summary:
      "Law student with strong academics and mooting experience, developing sharp research, advocacy and analytical skills.",
    education:
      "LLB Law, First expected — modules: Contract, Tort, Public Law, Criminal Law.",
    projects: [
      "Reached the semi-final of the university mooting competition, drafting skeleton arguments and presenting orally.",
      "Volunteered at a pro bono legal clinic, researching client queries under solicitor supervision.",
    ],
    experience:
      "Debating society secretary: organised weekly sessions and an inter-university competition.",
    skills: "Legal research, drafting, advocacy, analysis, attention to detail",
  },
  psychology: {
    name: "Emma Larsson",
    headline: "Psychology Student",
    summary:
      "Psychology student with research and data-analysis experience and a strong interest in applied, evidence-based work.",
    education:
      "BSc Psychology, 2:1 expected — modules: Research Methods, Cognitive Psychology, Statistics.",
    projects: [
      "Designed and ran a 40-participant study on memory and sleep; analysed results in SPSS and presented findings to the department.",
      "Literature review on adolescent wellbeing interventions, graded distinction.",
    ],
    experience:
      "Volunteer on a peer-support helpline: active listening and signposting under supervision.",
    skills: "SPSS, R, experimental design, qualitative & quantitative methods, report writing",
  },
  "accounting-and-finance": {
    name: "Hassan Malik",
    headline: "Accounting & Finance Student",
    summary:
      "Detail-focused finance student progressing toward professional qualifications, with practical modelling and reconciliation experience.",
    education:
      "BSc Accounting & Finance, First expected — modules: Financial Accounting, Corporate Finance, Audit; ACCA F1–F3 passed.",
    projects: [
      "Reconciled monthly accounts for a £4k society budget with zero discrepancies across the year.",
      "Built a DCF model in Excel for a coursework company valuation, graded distinction.",
    ],
    experience:
      "Finance intern (2 weeks): supported invoice processing and month-end checks.",
    skills: "Excel, financial modelling, reconciliation, ACCA (in progress), attention to detail",
  },
  marketing: {
    name: "Chloe Bennett",
    headline: "Marketing Student",
    summary:
      "Creative marketing student who pairs content and social skills with a habit of measuring what works.",
    education:
      "BA Marketing, 2:1 expected — modules: Consumer Behaviour, Digital Marketing, Brand Management.",
    projects: [
      "Grew a society Instagram from 200 to 1,500 followers in a term and drove 90+ event sign-ups.",
      "Ran a coursework campaign that lifted a mock brand's simulated engagement 35%.",
    ],
    experience:
      "Content volunteer for a local charity: scheduled posts and wrote newsletter copy.",
    skills: "Canva, Google Analytics, social media, copywriting, SEO basics",
  },
  education: {
    name: "Grace Thompson",
    headline: "Trainee Teacher",
    summary:
      "Education student with tutoring and classroom experience and a genuine commitment to helping every learner progress.",
    education:
      "BA Education Studies, 2:1 expected — modules: Pedagogy, Child Development, Inclusive Practice.",
    projects: [
      "Tutored five GCSE maths students weekly for a year; all improved by at least one grade.",
      "School placement: planned and delivered supervised lessons to a Year 8 class.",
    ],
    experience:
      "Holiday club leader: supervised and engaged groups of 20+ children safely.",
    skills: "Lesson planning, classroom management, communication, patience, safeguarding awareness",
  },
  "data-science": {
    name: "Yuki Tanaka",
    headline: "Data Science Student",
    summary:
      "Data science student who enjoys the full pipeline — from messy data to a clear, communicated insight.",
    education:
      "BSc Data Science, First expected — modules: Statistics, Machine Learning, Data Visualisation.",
    projects: [
      "Analysed 10k survey responses in Python to identify three churn drivers; built a dashboard used by the society committee.",
      "Trained a classifier to flag spam with 94% accuracy and documented the trade-offs.",
    ],
    experience:
      "Kaggle: top-20% finish in a beginner competition, sharing a reproducible notebook.",
    skills: "Python, pandas, SQL, scikit-learn, visualisation, statistics",
  },
};

export const exampleSlug = (field) => `cv-examples/${field.slug}`;

export const exampleTitle = (field) =>
  `${field.name} Student CV Example (2026) | Careero`;

export const exampleDescription = (field, sample) =>
  `A realistic ${field.name.toLowerCase()} student CV example — see how to present education, projects, skills and experience. Then build yours free with Careero.`;

const closingCta = (h2, text, buttonText) => ({ type: "cta", h2, text, buttonText, href: APP });

const buildExamplePage = (field) => {
  const s = SAMPLES[field.slug];
  if (!s) return null;
  const slug = exampleSlug(field);
  return {
    slug,
    title: exampleTitle(field),
    description: exampleDescription(field, s),
    h1: `${field.name} student CV example`,
    type: "website",
    breadcrumbTrail: [
      { name: "CV Examples", slug: "student-cv-examples" },
      { name: `${field.name} CV Example`, slug },
    ],
    blocks: [
      {
        type: "hero",
        kicker: `CV Example · ${field.name}`,
        h1: `${field.name} student CV example`,
        lead: `A realistic ${field.name.toLowerCase()} student CV example you can learn from — then build your own in minutes. (Sample is fictional.)`,
        primaryCta: { text: "Build my CV free", href: APP },
        secondaryCta: { text: `${field.name} CV guide`, href: `/cv-for-${field.slug}-students` },
        note: "Free to start · ATS-friendly · PDF &amp; DOCX",
      },
      {
        type: "prose",
        h2: `Sample: ${s.name} — ${s.headline}`,
        paragraphs: [`<em>${s.summary}</em>`],
        subsections: [
          { h3: "Education", paragraphs: [s.education] },
          { h3: "Projects", bullets: s.projects },
          { h3: "Experience", paragraphs: [s.experience] },
          { h3: "Skills", paragraphs: [s.skills] },
        ],
      },
      {
        type: "prose",
        h2: "Why this CV works",
        bullets: [
          "Leads with the strongest evidence for the field, not a long work history.",
          "Every bullet is achievement-focused and quantified where possible.",
          "Skills are relevant and grouped so recruiters and ATS can scan them.",
          "It fits one page and uses clean, standard headings.",
        ],
      },
      {
        type: "faq",
        items: [
          {
            q: `Is this a real ${field.name.toLowerCase()} CV?`,
            a: "No — the sample person is fictional and provided as an example. Use it as a structure to write your own.",
          },
          {
            q: "How do I build a CV like this?",
            a: 'Start free at <a href="' + APP + '" rel="noopener">app.careero.app</a> — Careero guides you through each section and writes strong bullets for you.',
          },
        ],
      },
      {
        type: "prose",
        h2: "More CV help",
        bullets: [
          `<a href="/cv-for-${field.slug}-students">How to write a ${field.name.toLowerCase()} CV</a>`,
          `<a href="/student-cv-examples">More student CV examples</a>`,
          `<a href="/student-cv-templates">Student CV templates</a>`,
        ],
      },
      closingCta(
        `Build your ${field.name.toLowerCase()} CV`,
        "Use this example as a guide and let Careero write yours, ATS-friendly and ready to download.",
        "Build my CV free",
      ),
    ],
  };
};

export function buildExamplePages(existingSlugs = new Set(), { cap = 100 } = {}) {
  const out = [];
  for (const field of FIELDS) {
    const page = buildExamplePage(field);
    if (!page) continue;
    if (existingSlugs.has(page.slug)) continue;
    out.push(page);
  }
  const skipped = out.length > cap ? out.splice(cap).length : 0;
  return { pages: out, generated: out.length, skipped };
}
