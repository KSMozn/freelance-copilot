// facets.mjs — SINGLE SOURCE OF TRUTH for the "CV by field × goal" facet matrix.
//
// Pure module: no server-only imports, so the static generator (build.mjs) and
// any future client code can both consume it. Every URL, <title> and meta
// description for a faceted page is built here — never inline in a template.
//
// Locale-parametrised by design (`locale` threads through every builder) but
// only "en" is implemented today. Arabic (/ar/…) is deliberately deferred: the
// app is English-only with no RTL/i18n, so shipping Arabic marketing pages that
// hreflang into an English product would be a poor experience. When the app
// gains Arabic, add an "ar" branch to the copy builders and a locale prefix to
// the path builders — no structural change needed.
//
// Anti-doorway note: pages are a CURATED matrix (10 fields × 5 goals), and each
// page is genuinely differentiated — goal-specific "what matters" cards, a
// field-specific prose section, and a composed FAQ. We never mass-produce
// thousands of near-duplicate shells.

import { site } from "./site.mjs";

export const DEFAULT_LOCALE = "en";
export const LOCALES = ["en"]; // "ar" intentionally deferred (see header)
const APP = site.appUrl;

// ---------------------------------------------------------------- GOALS ----
// The facet. Each goal carries its own intent framing, "what matters" cards
// and FAQ so a {field}/{goal} page differs meaningfully from its siblings.
export const GOALS = [
  {
    slug: "internship",
    name: "Internship",
    titleNoun: "an Internship",
    phrase: "an internship",
    intro:
      "Internship recruiters know you're early-career — they're screening for relevant skills, enthusiasm and evidence you can contribute quickly.",
    cards: [
      {
        icon: "🎯",
        title: "Relevance over length",
        text: "Lead with the coursework, projects and skills closest to the internship — not a full history.",
      },
      {
        icon: "🌱",
        title: "Show potential",
        text: "Enthusiasm, quick learning and initiative matter as much as a track record at this stage.",
      },
      {
        icon: "🧾",
        title: "A tailored summary",
        text: "Two lines naming the internship area and what you bring beat a generic objective.",
      },
    ],
    faq: [
      {
        q: "How do I write an internship CV with no experience?",
        a: 'Lead with education, projects and transferable skills, and tailor a short summary to the internship. See our <a href="/student-cv-with-no-experience">no-experience guide</a>.',
      },
      {
        q: "How long should an internship CV be?",
        a: "One page. Internship recruiters scan quickly, so keep it focused on the most relevant projects and skills.",
      },
    ],
  },
  {
    slug: "scholarship",
    name: "Scholarship",
    titleNoun: "a Scholarship",
    phrase: "a scholarship",
    intro:
      "A scholarship CV rewards merit and potential — committees look for academic strength, leadership and community impact, not job history.",
    cards: [
      {
        icon: "🏆",
        title: "Academics first",
        text: "Lead with grades, awards, honours and academic achievements — they anchor the decision.",
      },
      {
        icon: "🤝",
        title: "Leadership & service",
        text: "Committees value initiative: society roles, mentoring, volunteering and organising.",
      },
      {
        icon: "🎯",
        title: "A clear goal",
        text: "A short line on what the scholarship will help you achieve strengthens your case.",
      },
    ],
    faq: [
      {
        q: "How is a scholarship CV different from a job CV?",
        a: 'It foregrounds academic merit, leadership and potential over work experience. See our <a href="/cv-for-scholarship-application">scholarship CV guide</a>.',
      },
      {
        q: "How long should a scholarship CV be?",
        a: "One page is ideal; up to two is acceptable if you have substantial achievements, publications or leadership to evidence.",
      },
    ],
  },
  {
    slug: "part-time-job",
    name: "Part-Time Job",
    titleNoun: "a Part-Time Job",
    phrase: "a part-time job",
    intro:
      "For part-time roles, employers care about reliability, attitude and availability far more than a polished career history.",
    cards: [
      {
        icon: "⏰",
        title: "State availability",
        text: "Evenings, weekends, term-time or holidays — availability is often the deciding factor.",
      },
      {
        icon: "🤝",
        title: "Reliability & attitude",
        text: "Punctuality, teamwork and willingness to learn outweigh a long history.",
      },
      {
        icon: "📄",
        title: "Short & scannable",
        text: "Half a page to one page is plenty for a busy manager to read at a glance.",
      },
    ],
    faq: [
      {
        q: "What do I put on a part-time job CV with no experience?",
        a: 'Education, a friendly summary, your availability, and transferable skills from school, clubs and volunteering. See our <a href="/cv-for-part-time-job-students">part-time job CV guide</a>.',
      },
      {
        q: "How long should a part-time job CV be?",
        a: "Half a page to one page — keep it short and easy to skim.",
      },
    ],
  },
  {
    slug: "first-job",
    name: "First Job",
    titleNoun: "Your First Job",
    phrase: "your first job",
    intro:
      "Your first graduate-level job CV should convert your degree, projects and any experience into evidence you can do the role from day one.",
    cards: [
      {
        icon: "🎓",
        title: "Lead with your degree",
        text: "Your qualification and strongest projects are your main proof this early.",
      },
      {
        icon: "🧩",
        title: "Turn study into skills",
        text: "Frame coursework and projects as the practical skills the role asks for.",
      },
      {
        icon: "🧭",
        title: "Tailor to the role",
        text: "Mirror the job description's language so both recruiters and ATS see the fit.",
      },
    ],
    faq: [
      {
        q: "What goes on a CV for my first job?",
        a: 'Contact details, a short summary, education, projects, any experience (including part-time and volunteering) and skills. Our <a href="/first-cv">first-CV guide</a> walks through it.',
      },
      {
        q: "How do I stand out for my first job with little experience?",
        a: "Quantify projects, tailor the CV to each role, and keep it to one clean, ATS-friendly page.",
      },
    ],
  },
  {
    slug: "graduate-scheme",
    name: "Graduate Scheme",
    titleNoun: "a Graduate Scheme",
    phrase: "a graduate scheme",
    intro:
      "Graduate schemes are competitive and heavily screened — recruiters want evidence of competencies, commercial awareness and measurable impact.",
    cards: [
      {
        icon: "📊",
        title: "Evidence competencies",
        text: "Map your examples to the scheme's competencies: teamwork, leadership, problem-solving.",
      },
      {
        icon: "🔢",
        title: "Quantify everything",
        text: "Numbers signal impact — budgets, users, results, team sizes and improvements.",
      },
      {
        icon: "✅",
        title: "Flawless & ATS-safe",
        text: "Large employers screen at scale, so keep it clean, consistent and error-free.",
      },
    ],
    faq: [
      {
        q: "What do graduate scheme recruiters look for on a CV?",
        a: "Evidence of their target competencies, quantified achievements, and a tailored, error-free one-page CV that passes ATS screening.",
      },
      {
        q: "Should I tailor my CV to each graduate scheme?",
        a: "Yes — mirror each scheme's competencies and language. Careero makes it fast to adapt your CV per application.",
      },
    ],
  },
];

// --------------------------------------------------------------- FIELDS ----
// The entity. Each field carries field-specific cards, a prose section and a
// FAQ so per-field pages are genuinely distinct (not a swapped word).
export const FIELDS = [
  {
    slug: "computer-science",
    name: "Computer Science",
    handAuthoredBase: true, // /cv-for-computer-science-students already exists
    lead:
      "Tech recruiters scan for projects, a public GitHub and the right stack — not a long work history.",
    angle: "showcasing projects, a GitHub and the right stack",
    cards: [
      { icon: "🧩", title: "Projects over jobs", text: "Coursework and side projects are your strongest evidence — describe each by problem, stack and outcome." },
      { icon: "🐙", title: "A linked GitHub", text: "A tidy GitHub with pinned repos turns claims into proof." },
      { icon: "🛠️", title: "A focused skills section", text: "Group languages, frameworks and tools you can actually discuss." },
      { icon: "✅", title: "ATS-safe formatting", text: "Tech employers screen heavily, so keep headings standard and layout clean." },
    ],
    prose: {
      h2: "How to describe a coding project",
      paragraphs: [
        "The best computer science bullets read like mini case studies: what you built, the stack, and the result. &ldquo;Built a full-stack expense tracker in React and Node.js used by 30 classmates&rdquo; beats &ldquo;made a website.&rdquo;",
      ],
    },
    faq: [
      { q: "How many projects should a CS student CV have?", a: "Two to four strong projects beat a long list — choose the ones with the clearest outcome and most relevant stack." },
    ],
    related: ["data-science", "engineering"],
  },
  {
    slug: "engineering",
    name: "Engineering",
    handAuthoredBase: true,
    lead:
      "Engineering recruiters look for hands-on projects, technical tools and evidence you can solve real problems.",
    angle: "highlighting technical projects, tools and measurable results",
    cards: [
      { icon: "📐", title: "Technical projects", text: "Design, final-year and competition projects — described by objective, method and result." },
      { icon: "🧰", title: "Tools & software", text: "CAD, MATLAB, SolidWorks and lab equipment you've genuinely used belong in a clear skills block." },
      { icon: "🏭", title: "Placements & labs", text: "Industrial placements, lab modules and workshops all count as practical experience." },
      { icon: "✅", title: "Clean, ATS-safe layout", text: "Large employers screen at scale, so keep formatting simple." },
    ],
    prose: {
      h2: "Turn a design project into strong bullets",
      paragraphs: [
        "Quantify wherever you can — loads, tolerances, cost savings, efficiency, team size. &ldquo;Designed a bracket that cut mass 18% while meeting the safety factor&rdquo; is far stronger than &ldquo;did a design project.&rdquo;",
      ],
    },
    faq: [
      { q: "Should I include my final-year project?", a: "Yes — it's often your most substantial work. Describe the objective, method, tools and outcome." },
    ],
    related: ["computer-science", "data-science"],
  },
  {
    slug: "business",
    name: "Business",
    handAuthoredBase: true,
    lead:
      "For business and management roles, recruiters want commercial awareness, leadership and measurable impact.",
    angle: "leading with results, leadership and commercial awareness",
    cards: [
      { icon: "📈", title: "Quantified results", text: "Revenue raised, budgets managed, members recruited — numbers make a business CV credible." },
      { icon: "👥", title: "Leadership & teamwork", text: "Society committees, group projects and supervision show the soft skills employers screen for." },
      { icon: "🧠", title: "Commercial awareness", text: "Tie coursework and projects to real business outcomes." },
      { icon: "✅", title: "Polished & ATS-safe", text: "Consultancies and banks use heavy screening — keep it clean and error-free." },
    ],
    prose: {
      h2: "Make everyday experience sound commercial",
      paragraphs: [
        "A retail job becomes &ldquo;Handled 100+ transactions per shift and resolved complaints, improving repeat custom.&rdquo; A treasurer role becomes &ldquo;Managed a £4k budget and cut event costs 15%.&rdquo; The result matters more than the activity.",
      ],
    },
    faq: [
      { q: "Is society and part-time experience enough for a business CV?", a: "Yes — described well, they show the leadership, numeracy and teamwork employers want." },
    ],
    related: ["accounting-and-finance", "marketing"],
  },
  {
    slug: "nursing",
    name: "Nursing",
    lead:
      "Nursing and healthcare recruiters look for clinical placements, patient-care skills and the values behind good care.",
    angle: "foregrounding placements, clinical skills and care values",
    cards: [
      { icon: "🏥", title: "Clinical placements", text: "Placements are your strongest evidence — name the setting, your responsibilities and skills practised." },
      { icon: "💙", title: "Values & communication", text: "Compassion, safeguarding awareness and clear communication are core to a nursing CV." },
      { icon: "📋", title: "Skills & competencies", text: "List clinical skills, procedures and any certifications you hold (e.g. BLS)." },
      { icon: "✅", title: "Clear, professional layout", text: "Healthcare CVs must be easy to scan and completely accurate." },
    ],
    prose: {
      h2: "How to describe a clinical placement",
      paragraphs: [
        "Name the setting, your duties and the skills you developed: &ldquo;Completed a 6-week placement on a surgical ward, supporting patient observations, medication rounds and discharge planning under supervision.&rdquo;",
      ],
    },
    faq: [
      { q: "What should a nursing student put on a CV?", a: "Placements, clinical skills, relevant modules, certifications, and the values and communication skills central to care." },
    ],
    related: ["psychology", "education"],
  },
  {
    slug: "law",
    name: "Law",
    lead:
      "Law recruiters value academic strength, precise written communication and evidence of commercial or legal awareness.",
    angle: "emphasising academics, legal skills and attention to detail",
    cards: [
      { icon: "⚖️", title: "Academic record", text: "Grades and relevant modules matter — lead with them, especially for training contracts and vacation schemes." },
      { icon: "✍️", title: "Written precision", text: "A flawless, well-structured CV is itself evidence of the accuracy law demands." },
      { icon: "🏛️", title: "Legal & commercial awareness", text: "Mooting, pro bono, debating and relevant reading show genuine interest." },
      { icon: "✅", title: "Impeccable formatting", text: "Zero typos, consistent structure — attention to detail is assessed." },
    ],
    prose: {
      h2: "Show legal skills without a training contract",
      paragraphs: [
        "Mooting, pro bono clinics, debating, student law societies and relevant modules all demonstrate research, advocacy and analysis. Describe each by what you did and the skill it evidences.",
      ],
    },
    faq: [
      { q: "How do I write a law student CV for a vacation scheme?", a: "Lead with academics, evidence legal and commercial awareness (mooting, pro bono, reading), and keep it flawless and one page." },
    ],
    related: ["business", "psychology"],
  },
  {
    slug: "psychology",
    name: "Psychology",
    lead:
      "Psychology recruiters and postgraduate courses look for research skills, data literacy and relevant experience.",
    angle: "highlighting research, data skills and relevant experience",
    cards: [
      { icon: "🔬", title: "Research experience", text: "Dissertations, lab work and studies show methodology and analysis — describe design, method and findings." },
      { icon: "📊", title: "Data & stats skills", text: "SPSS, R and quantitative/qualitative methods are strong, screenable skills." },
      { icon: "🤝", title: "Relevant experience", text: "Volunteering, support roles and helplines show applied understanding of people." },
      { icon: "✅", title: "Clear, evidence-led layout", text: "Structure the CV as clearly as you'd structure a study." },
    ],
    prose: {
      h2: "How to describe research on a psychology CV",
      paragraphs: [
        "Name the question, your method and the outcome: &ldquo;Designed and ran a 40-participant study on memory and sleep; analysed results in SPSS and presented findings to the department.&rdquo;",
      ],
    },
    faq: [
      { q: "What experience counts on a psychology CV?", a: "Research projects, data-analysis skills, and relevant volunteering or support roles — all show applied understanding." },
    ],
    related: ["nursing", "education"],
  },
  {
    slug: "accounting-and-finance",
    name: "Accounting & Finance",
    lead:
      "Accounting and finance recruiters want numeracy, accuracy, relevant software and any progress toward professional qualifications.",
    angle: "showing numeracy, accuracy and qualification progress",
    cards: [
      { icon: "🔢", title: "Numeracy & accuracy", text: "Evidence careful, quantified work — the core of an accounting CV." },
      { icon: "📑", title: "Qualifications", text: "Note progress toward ACCA, ACA, CFA or similar, plus relevant modules." },
      { icon: "💻", title: "Software skills", text: "Excel, financial modelling and any accounting software are strong, screenable skills." },
      { icon: "✅", title: "Precise & ATS-safe", text: "Accuracy is assessed — a clean, error-free CV is essential." },
    ],
    prose: {
      h2: "Make finance experience quantified",
      paragraphs: [
        "Lead with numbers: &ldquo;Reconciled monthly accounts for a £4k society budget with zero discrepancies&rdquo; or &ldquo;Built a DCF model in Excel for a coursework valuation.&rdquo; Precision signals the mindset the field rewards.",
      ],
    },
    faq: [
      { q: "What goes on an accounting and finance student CV?", a: "Numeracy-focused achievements, qualification progress (ACCA/ACA/CFA), software skills (Excel, modelling), and relevant modules." },
    ],
    related: ["business", "data-science"],
  },
  {
    slug: "marketing",
    name: "Marketing",
    lead:
      "Marketing recruiters look for creativity backed by results, plus hands-on experience with content, social and analytics.",
    angle: "pairing creativity with measurable results",
    cards: [
      { icon: "📣", title: "Campaigns & content", text: "Society promotion, blogs, social accounts and events are real marketing experience." },
      { icon: "📈", title: "Measurable results", text: "Reach, engagement, followers gained, attendance — quantify the impact." },
      { icon: "🧰", title: "Tools", text: "Canva, Google Analytics, Meta/LinkedIn ads and SEO basics are strong skills." },
      { icon: "✅", title: "Clean but personable", text: "Professional and ATS-safe, while showing a bit of your voice." },
    ],
    prose: {
      h2: "Turn a society or side project into marketing results",
      paragraphs: [
        "&ldquo;Grew a society Instagram from 200 to 1,500 followers in a term and drove 90+ event sign-ups&rdquo; shows exactly the creativity-plus-results marketing teams want.",
      ],
    },
    faq: [
      { q: "What experience counts on a marketing CV with no job?", a: "Running social accounts, promoting societies or events, blogging, and any analytics or design tools you've used." },
    ],
    related: ["business", "data-science"],
  },
  {
    slug: "education",
    name: "Education",
    lead:
      "Education and teaching recruiters want classroom or tutoring experience, communication skills and a genuine commitment to learners.",
    angle: "foregrounding teaching experience and communication",
    cards: [
      { icon: "🍎", title: "Classroom experience", text: "Placements, tutoring, mentoring and coaching are your strongest evidence." },
      { icon: "🗣️", title: "Communication", text: "Explaining clearly, patience and adapting to different learners are core skills." },
      { icon: "📚", title: "Subject knowledge", text: "Name your subject specialisms and relevant modules." },
      { icon: "✅", title: "Warm but professional", text: "Clear, accurate and easy to read for a busy school." },
    ],
    prose: {
      h2: "How to describe teaching or tutoring",
      paragraphs: [
        "Name the learners, what you taught and the outcome: &ldquo;Tutored 5 GCSE students in maths weekly for a year; all improved by at least one grade.&rdquo;",
      ],
    },
    faq: [
      { q: "What should an education student put on a CV?", a: "Classroom or tutoring experience, communication skills, subject specialisms, and any work with children or young people." },
    ],
    related: ["psychology", "nursing"],
  },
  {
    slug: "data-science",
    name: "Data Science",
    lead:
      "Data and analytics recruiters look for projects, statistical and programming skills, and the ability to turn data into insight.",
    angle: "showcasing data projects, stats and programming skills",
    cards: [
      { icon: "📊", title: "Data projects", text: "End-to-end projects — question, data, method, insight — are your strongest evidence." },
      { icon: "🐍", title: "Tools & languages", text: "Python, R, SQL, pandas and visualisation libraries are core, screenable skills." },
      { icon: "🧮", title: "Statistics & ML", text: "Name the methods you've genuinely applied — regression, classification, clustering." },
      { icon: "✅", title: "Clear, ATS-safe layout", text: "Keep it clean so both humans and screening software parse it." },
    ],
    prose: {
      h2: "How to describe a data project",
      paragraphs: [
        "Frame it as a question and an insight: &ldquo;Analysed 10k survey responses in Python to identify three churn drivers; visualised findings in a dashboard used by the society committee.&rdquo;",
      ],
    },
    faq: [
      { q: "What projects should a data science student CV include?", a: "Two to four end-to-end projects that show the full pipeline — sourcing data, analysis, and a clear, communicated insight." },
    ],
    related: ["computer-science", "accounting-and-finance"],
  },
];

// Guard against a `related` slug that doesn't exist in FIELDS (keeps internal
// links valid — the build validator would otherwise flag a broken link).
const FIELD_SLUGS = new Set(FIELDS.map((f) => f.slug));
const relatedFields = (field) =>
  (field.related || []).filter((s) => FIELD_SLUGS.has(s));

// --------------------------------------------------------- PATH BUILDERS ----
const localePrefix = (locale) => (locale && locale !== DEFAULT_LOCALE ? `${locale}/` : "");
export const fieldSlug = (field, locale = DEFAULT_LOCALE) =>
  `${localePrefix(locale)}cv-for-${field.slug}-students`;
export const fieldGoalSlug = (field, goal, locale = DEFAULT_LOCALE) =>
  `${localePrefix(locale)}cv-for-${field.slug}-students/${goal.slug}`;

// --------------------------------------------------------- COPY BUILDERS ----
// Intent-framed, never bare boilerplate. The base variant names the FULL goal
// set; each facet variant names its SINGLE goal value.
const goalSetPhrase = () => {
  const names = GOALS.map((g) => g.phrase);
  return `${names.slice(0, -1).join(", ")} and ${names[names.length - 1]}`;
};

export const fieldTitle = (field, locale = DEFAULT_LOCALE) =>
  `${field.name} Student CV: Guide & Examples (2026) | Careero`;

export const fieldDescription = (field, locale = DEFAULT_LOCALE) =>
  `Write a ${field.name.toLowerCase()} student CV for ${goalSetPhrase()} — ${field.angle}. Free, ATS-friendly, PDF & DOCX with Careero.`;

export const fieldGoalTitle = (field, goal, locale = DEFAULT_LOCALE) =>
  `${field.name} CV for ${goal.titleNoun} — Student Guide | Careero`;

export const fieldGoalDescription = (field, goal, locale = DEFAULT_LOCALE) =>
  `Write a ${field.name.toLowerCase()} student CV for ${goal.phrase} — ${field.angle}, framed for ${goal.phrase}. Free, ATS-friendly with Careero.`;

// ----------------------------------------------------- STRUCTURED DATA ------
// Facet-scoped WebPage: honest `about` (the field) + `audience` (students).
// No invented ratings, prices, counts, or relationships.
const facetWebPageLd = (field, goal, path) => ({
  "@context": "https://schema.org",
  "@type": "WebPage",
  name: goal ? fieldGoalTitle(field, goal) : fieldTitle(field),
  url: site.origin + "/" + path,
  about: { "@type": "Thing", name: `${field.name} student CV` },
  audience: { "@type": "EducationalAudience", educationalRole: "student" },
});

// --------------------------------------------------------- PAGE BUILDERS ----
const closingCta = (h2, text, buttonText) => ({
  type: "cta",
  h2,
  text,
  buttonText,
  href: APP,
});

// Crawlable internal-links block: on a field base page, link to EVERY goal
// variant (the "navigate to the indexable per-facet URL" requirement, realised
// as plain server-rendered links — no client refetch).
const goalLinksBlock = (field, locale) => ({
  type: "cards",
  h2: `Writing your ${field.name.toLowerCase()} CV for a specific goal?`,
  items: GOALS.map((goal) => ({
    icon: "→",
    title: `For ${goal.phrase}`,
    text: goal.intro,
    href: "/" + fieldGoalSlug(field, goal, locale),
  })),
});

const relatedFieldsBlock = (field, locale) => {
  const rel = relatedFields(field);
  if (!rel.length) return null;
  return {
    type: "prose",
    h2: "More CV guides by field",
    bullets: rel.map((slug) => {
      const f = FIELDS.find((x) => x.slug === slug);
      return `<a href="/${fieldSlug(f, locale)}">CV for ${f.name.toLowerCase()} students</a>`;
    }),
  };
};

const buildFieldPage = (field, locale = DEFAULT_LOCALE) => {
  const slug = fieldSlug(field, locale);
  const blocks = [
    {
      type: "hero",
      kicker: `CV by Field · ${field.name}`,
      h1: `How to write a ${field.name.toLowerCase()} student CV`,
      lead: field.lead,
      primaryCta: { text: `Build my ${field.name} CV`, href: APP },
      secondaryCta: { text: "See CV examples", href: "/student-cv-examples" },
      note: "Free to start · ATS-friendly · PDF &amp; DOCX",
    },
    {
      type: "cards",
      h2: `What matters most on a ${field.name.toLowerCase()} CV`,
      items: field.cards,
    },
    { type: "prose", ...field.prose },
    goalLinksBlock(field, locale),
    {
      type: "faq",
      items: [
        ...field.faq,
        {
          q: "Is Careero free for students?",
          a: 'Yes — build your CV free and download it as PDF or DOCX at <a href="' + APP + '" rel="noopener">app.careero.app</a>.',
        },
      ],
    },
  ];
  const rel = relatedFieldsBlock(field, locale);
  if (rel) blocks.push(rel);
  blocks.push(
    closingCta(
      `Build your ${field.name.toLowerCase()} CV`,
      `Add your details and let Careero write recruiter-ready, ATS-friendly bullets.`,
      `Build my ${field.name} CV`,
    ),
  );
  return {
    slug,
    title: fieldTitle(field, locale),
    description: fieldDescription(field, locale),
    h1: `How to write a ${field.name.toLowerCase()} student CV`,
    type: "website",
    blocks,
    extraJsonLd: [facetWebPageLd(field, null, slug)],
  };
};

const buildFieldGoalPage = (field, goal, locale = DEFAULT_LOCALE) => {
  const slug = fieldGoalSlug(field, goal, locale);
  const baseSlug = fieldSlug(field, locale);
  const siblings = GOALS.filter((g) => g.slug !== goal.slug);
  return {
    slug,
    title: fieldGoalTitle(field, goal, locale),
    description: fieldGoalDescription(field, goal, locale),
    h1: `${field.name} student CV for ${goal.phrase}`,
    type: "website",
    breadcrumbTrail: [
      { name: `${field.name} Student CV`, slug: baseSlug },
      { name: `CV for ${goal.titleNoun}`, slug },
    ],
    blocks: [
      {
        type: "hero",
        kicker: `${field.name} · ${goal.name}`,
        h1: `How to write a ${field.name.toLowerCase()} student CV for ${goal.phrase}`,
        lead: `${goal.intro} Here's how to do it as a ${field.name.toLowerCase()} student.`,
        primaryCta: { text: "Build my CV free", href: APP },
        secondaryCta: { text: `All ${field.name.toLowerCase()} CV tips`, href: "/" + baseSlug },
        note: "Free to start · ATS-friendly · PDF &amp; DOCX",
      },
      {
        type: "cards",
        h2: `What matters for ${goal.phrase}`,
        items: goal.cards,
      },
      {
        type: "prose",
        h2: `${field.name} specifics`,
        paragraphs: [
          `${field.lead} ${field.prose.paragraphs[0]}`,
        ],
      },
      {
        type: "faq",
        items: [...goal.faq, ...field.faq],
      },
      {
        type: "prose",
        h2: `${field.name} CV for other goals`,
        bullets: [
          `<a href="/${baseSlug}">All ${field.name.toLowerCase()} CV tips</a>`,
          ...siblings.map(
            (g) =>
              `<a href="/${fieldGoalSlug(field, g, locale)}">${field.name} CV for ${g.phrase}</a>`,
          ),
        ],
      },
      closingCta(
        `Build your ${field.name.toLowerCase()} CV for ${goal.phrase}`,
        "Answer a few guided questions and download a tailored, ATS-friendly CV.",
        "Build my CV free",
      ),
    ],
    extraJsonLd: [facetWebPageLd(field, goal, slug)],
  };
};

// ------------------------------------------------------- MATRIX BUILDER ----
// Emits field base (unless hand-authored) + every field×goal, for each locale.
// `existingSlugs` dedupes against hand-authored pages. `cap` is a defensive
// ceiling so a data mistake can never explode the sitemap unbounded.
export function buildFacetPages(existingSlugs = new Set(), { cap = 500, locales = LOCALES } = {}) {
  const out = [];
  const skipped = [];
  for (const locale of locales) {
    for (const field of FIELDS) {
      const baseSlug = fieldSlug(field, locale);
      if (!field.handAuthoredBase && !existingSlugs.has(baseSlug)) {
        out.push(buildFieldPage(field, locale));
      }
      for (const goal of GOALS) {
        const slug = fieldGoalSlug(field, goal, locale);
        if (existingSlugs.has(slug)) continue;
        out.push(buildFieldGoalPage(field, goal, locale));
      }
    }
  }
  if (out.length > cap) {
    // Graceful degradation: never emit an unbounded flood. Truncate and report.
    skipped.push(...out.splice(cap));
  }
  return { pages: out, generated: out.length, skipped: skipped.length };
}
