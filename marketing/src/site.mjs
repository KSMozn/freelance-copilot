// Global site configuration: canonical origin, app URLs, brand, and the
// navigation model shared by every page. Keeping the nav here (not in each
// page) guarantees the menu never drifts between pages.

export const site = {
  name: "Careero",
  // Canonical origin for this marketing site. All canonical/OG/sitemap URLs
  // are built from this. The apex domain is the SEO surface.
  origin: "https://careero.app",
  // The authenticated CV builder. Every primary CTA points here.
  appUrl: "https://app.careero.app",
  loginUrl: "https://app.careero.app/login",
  linkedin: "https://www.linkedin.com/company/136044566",
  tagline: "AI CV Builder for Students",
  // Short meta-description default (per-page ones override this).
  description:
    "Careero helps students build their first professional, ATS-friendly CV with AI — describe projects and internships clearly, pick a modern template, and download as PDF or DOCX.",
  // Canonical one-paragraph product description — reused verbatim across
  // homepage, About, metadata, SoftwareApplication schema, llms.txt, FAQ and
  // footer so the brand story never drifts (playbook Phase 8).
  productDescription:
    "Careero is an AI-powered CV builder for students and fresh graduates. It helps students create professional CVs even when they have limited work experience by guiding them through education, projects, internships, skills, activities, LinkedIn, GitHub, and ready-to-download CV templates.",
  twitter: "@careero",
  locale: "en_US",
  // --- integrations (fill in, then rebuild + redeploy) -------------------
  googleSiteVerification: "",
  cloudflareAnalyticsToken: "8b93777272884655b4cfabdbca3ecd76",
  // Brand palette (mirrors app.careero.app: blue → indigo → violet).
  brand: {
    from: "#3B82F6",
    mid: "#6C5CE7",
    to: "#8B5CF6",
    ink: "#0f172a",
  },
};

// Navigation model. A group with `items` renders as a dropdown; a group with
// `href` and no items renders as a plain link. Every destination is a real,
// built page (no dead links, no duplicate slugs).
export const nav = [
  {
    label: "For Students",
    items: [
      { label: "Create My CV", href: "/create-cv-for-students" },
      { label: "AI CV Builder for Students", href: "/ai-cv-builder-for-students" },
      { label: "CV With No Experience", href: "/student-cv-with-no-experience" },
      { label: "CV for Internship", href: "/cv-for-internship" },
      { label: "ATS-Friendly CV", href: "/ats-friendly-student-cv" },
      { label: "Student CV Builder", href: "/student-cv-builder" },
    ],
  },
  {
    label: "CV by Field",
    items: [
      { label: "Computer Science Students", href: "/cv-for-computer-science-students" },
      { label: "Engineering Students", href: "/cv-for-engineering-students" },
      { label: "Business Students", href: "/cv-for-business-students" },
      { label: "For a Scholarship", href: "/cv-for-scholarship-application" },
      { label: "For a Part-Time Job", href: "/cv-for-part-time-job-students" },
    ],
  },
  {
    label: "Guides",
    items: [
      { label: "How to Write a Student CV", href: "/guides/how-to-write-a-student-cv" },
      { label: "CV With No Experience", href: "/guides/student-cv-with-no-experience" },
      { label: "Writing Projects in a CV", href: "/guides/how-to-write-projects-in-a-cv" },
      { label: "Adding Internships to a CV", href: "/guides/how-to-add-internships-to-a-cv" },
      { label: "Best CV Format for Students", href: "/guides/best-cv-format-for-students" },
      { label: "LinkedIn for Students", href: "/guides/linkedin-profile-for-students" },
      { label: "GitHub for Students", href: "/guides/github-profile-for-students" },
      { label: "CV Action Verbs", href: "/guides/cv-action-verbs" },
      { label: "Student CV Checklist", href: "/guides/student-cv-checklist" },
    ],
  },
  {
    label: "Compare",
    items: [
      { label: "Careero vs Canva", href: "/alternatives/canva-cv-builder-for-students" },
      { label: "Careero vs Resume.io", href: "/alternatives/resume-io-for-students" },
      { label: "Careero vs Zety", href: "/alternatives/zety-for-students" },
      { label: "Careero vs Generic AI tools", href: "/alternatives/generic-ai-resume-builders" },
    ],
  },
  { label: "Templates", href: "/student-cv-templates" },
  { label: "Features", href: "/features" },
];

// Footer-only "Company" column (kept out of the top nav to avoid clutter).
export const footerCompany = [
  { label: "About", href: "/about" },
  { label: "FAQ", href: "/faq" },
  { label: "Blog", href: "/blog" },
  { label: "CV Examples", href: "/student-cv-examples" },
  { label: "First CV Guide", href: "/first-cv" },
];
