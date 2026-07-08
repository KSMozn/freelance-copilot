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
  tagline: "AI CV Builder for Students",
  description:
    "Careero helps students build their first professional, ATS-friendly CV with AI — describe projects and internships clearly, pick a modern template, and download as PDF or DOCX.",
  twitter: "@careero",
  locale: "en_US",
  // Brand palette (mirrors app.careero.app: blue → indigo → violet).
  brand: {
    from: "#3B82F6",
    mid: "#6C5CE7",
    to: "#8B5CF6",
    ink: "#0f172a",
  },
};

// Navigation model. Each dropdown item resolves to a real destination — an
// internal SEO page (path starting with "/") or the app (absolute URL). No
// dead links: feature/resource items without a dedicated marketing page point
// to the closest relevant guide or to the app.
export const nav = [
  {
    label: "For Students",
    items: [
      { label: "Student CV Builder", href: "/student-cv-builder" },
      { label: "First CV Guide", href: "/first-cv" },
      { label: "CV for Internship", href: "/cv-for-internship" },
      { label: "Student CV Templates", href: "/student-cv-templates" },
      { label: "ATS-Friendly CV", href: "/ats-friendly-student-cv" },
    ],
  },
  {
    label: "Features",
    items: [
      { label: "AI CV Writing", href: "/ai-cv-builder" },
      {
        label: "Project Description Helper",
        href: "/blog/how-to-describe-student-projects",
      },
      { label: "Internship Summary Helper", href: "/cv-for-internship" },
      { label: "PDF Download", href: "/student-cv-builder#formats" },
      { label: "DOCX Download", href: "/student-cv-builder#formats" },
      {
        label: "LinkedIn Profile Helper",
        href: "/blog/how-to-write-cv-with-no-experience",
      },
    ],
  },
  {
    label: "Resources",
    items: [
      { label: "CV Examples", href: "/student-cv-templates" },
      { label: "Career Tips", href: "/blog" },
      {
        label: "LinkedIn Tips",
        href: "/blog/how-to-write-cv-with-no-experience",
      },
      {
        label: "GitHub Profile Tips",
        href: "/blog/how-to-describe-student-projects",
      },
    ],
  },
];
