// All public pages. Each object is a page: unique title/description/H1, a set
// of content blocks (rendered to real HTML), and optional FAQ (which also
// generates FAQPage structured data). Slug "" is the homepage.

import { site } from "./site.mjs";

const APP = site.appUrl;
const PUB = "2026-07-01T09:00:00+00:00";
const MOD = "2026-07-08T09:00:00+00:00";

// Shared closing CTA band reused across pages.
const closingCta = (h2, text, buttonText) => ({
  type: "cta",
  h2,
  text,
  buttonText,
  href: APP,
});

export const pages = [
  // ---------------------------------------------------------------- HOME ----
  {
    slug: "",
    title: "Careero — AI CV Builder for Students",
    description:
      "Careero helps students and fresh graduates create professional CVs with AI. Build your first CV, improve projects and internships, choose a template, and download in PDF or DOCX.",
    h1: "Build your first student CV with confidence",
    type: "website",
    blocks: [
      {
        type: "hero",
        kicker: "AI CV Builder for Students",
        h1: "Build your first student CV with confidence",
        lead:
          "Careero helps students and fresh graduates build professional CVs even when they have limited work experience. Add education, projects, internships, skills, activities, LinkedIn and GitHub — and download your CV in PDF or DOCX.",
        primaryCta: { text: "Create My CV", href: APP },
        secondaryCta: { text: "See Student CV Templates", href: "/student-cv-templates" },
        note: "Free to start · No credit card · PDF &amp; DOCX download",
        bullets: [
          "Guided, step-by-step CV wizard built for students",
          "AI help for projects, internships and summaries",
          "ATS-friendly formatting that passes screening software",
        ],
      },
      {
        type: "cards",
        h2: "Everything a student needs to land the interview",
        intro:
          "Careero is an AI-powered CV builder for students and fresh graduates. It helps you create a professional CV even with limited work experience by guiding you through education, projects, internships, skills, activities, LinkedIn, GitHub, and ready-to-download CV templates.",
        items: [
          {
            icon: "🎓",
            title: "Made for students",
            text: "Sections for coursework, academic projects, volunteering and societies — the things that actually make up a student CV.",
            href: "/student-cv-builder",
          },
          {
            icon: "🤖",
            title: "AI writing help",
            text: "Describe a project or internship in a sentence and Careero rewrites it into strong, quantified bullet points.",
            href: "/ai-cv-builder-for-students",
          },
          {
            icon: "✅",
            title: "ATS-friendly",
            text: "Clean structure and standard headings so applicant tracking systems can read every line of your CV.",
            href: "/ats-friendly-student-cv",
          },
          {
            icon: "🧩",
            title: "Project helper",
            text: "Turn a class or side project into achievement-focused bullets that show real skills.",
            href: "/guides/how-to-write-projects-in-a-cv",
          },
          {
            icon: "💼",
            title: "Internship-ready",
            text: "Tailor your CV for internship applications with a focused summary and relevant highlights.",
            href: "/cv-for-internship",
          },
          {
            icon: "⬇️",
            title: "PDF & DOCX",
            text: "Download a pixel-perfect PDF for applications or an editable DOCX whenever you need it.",
            href: "/student-cv-builder#formats",
          },
        ],
      },
      {
        type: "steps",
        h2: "From blank page to finished CV in three steps",
        items: [
          {
            title: "1. Add your details",
            text: "Answer simple guided questions about your education, projects and experience. No formatting to fight with.",
          },
          {
            title: "2. Let AI polish it",
            text: "Careero rewrites rough notes into clear, quantified bullet points and drafts a strong personal summary.",
          },
          {
            title: "3. Pick a template & download",
            text: "Choose a modern, ATS-friendly template and export as PDF or DOCX, ready to send.",
          },
        ],
      },
      {
        type: "prose",
        h2: "Why students choose Careero",
        paragraphs: [
          "Writing a first CV is hard because you feel you have &ldquo;nothing to put on it.&rdquo; Careero flips that around: it helps you recognise the value in your coursework, projects, part-time jobs and volunteering, then describes them the way recruiters expect to read them.",
          "Because everything is built around the student experience, you are never staring at an empty document meant for someone with a decade of jobs. You get structure, prompts and AI suggestions tuned for early-career applicants.",
        ],
      },
      {
        type: "faq",
        h2: "Frequently asked questions",
        items: [
          {
            q: "Is Careero free to use?",
            a: "Yes — you can build your CV for free and start right away. Create your account at <a href=\"" + APP + "\" rel=\"noopener\">app.careero.app</a>.",
          },
          {
            q: "Do I need any experience to create a CV?",
            a: "No. Careero is designed for students writing their first CV. It helps you turn coursework, academic projects, volunteering and part-time work into strong CV content.",
          },
          {
            q: "Can I download my CV as PDF and DOCX?",
            a: "Yes. Every CV can be exported as a print-ready PDF or an editable DOCX file.",
          },
          {
            q: "Is the CV ATS-friendly?",
            a: "Yes. Careero uses clean layouts and standard section headings so applicant tracking systems can parse your CV correctly.",
          },
        ],
      },
      closingCta(
        "Ready to build your student CV?",
        "Join students using Careero to create their first professional, ATS-friendly CV.",
        "Create your CV now",
      ),
    ],
  },

  // -------------------------------------------------- STUDENT CV BUILDER ----
  {
    slug: "student-cv-builder",
    title: "Student CV Builder — Free AI CV Maker for Students | Careero",
    description:
      "Build a professional student CV with Careero's free AI CV builder. Guided sections for education, projects and internships, ATS-friendly templates, and PDF or DOCX download.",
    h1: "The student CV builder that does the hard part for you",
    type: "website",
    blocks: [
      {
        type: "hero",
        kicker: "Student CV Builder",
        h1: "The student CV builder that does the hard part for you",
        lead:
          "A guided, AI-powered CV builder made specifically for students and recent graduates. Add your details, let Careero write strong bullet points, and download an ATS-friendly CV in minutes.",
        primaryCta: { text: "Start your student CV", href: APP },
        secondaryCta: { text: "Browse templates", href: "/student-cv-templates" },
        note: "Free to start · PDF &amp; DOCX export",
      },
      {
        type: "cards",
        h2: "Built around the student journey",
        items: [
          {
            icon: "📚",
            title: "Education first",
            text: "Lead with your degree, modules, grades and academic achievements — the strongest part of a student CV.",
          },
          {
            icon: "🧪",
            title: "Projects that shine",
            text: "Add coursework and side projects with AI-written bullets that highlight the skills you used.",
          },
          {
            icon: "🤝",
            title: "Experience of any kind",
            text: "Part-time jobs, volunteering, societies and internships all become relevant, well-described experience.",
          },
          {
            icon: "🎨",
            title: "Modern templates",
            text: "Clean, recruiter-friendly designs that stay readable for both humans and screening software.",
          },
        ],
      },
      {
        type: "steps",
        h2: "How the builder works",
        items: [
          {
            title: "Answer guided questions",
            text: "No blank document — Careero asks for exactly what belongs on a student CV, one section at a time.",
          },
          {
            title: "Improve with AI",
            text: "Turn plain notes into quantified, achievement-focused bullet points and a confident personal summary.",
          },
          {
            title: "Export and apply",
            text: "Pick a template and download a polished PDF or an editable DOCX, ready for applications.",
          },
        ],
      },
      {
        type: "prose",
        id: "formats",
        h2: "Download as PDF or DOCX",
        paragraphs: [
          "When your CV is ready, export it as a <strong>print-ready PDF</strong> for online applications and job boards, or as an <strong>editable DOCX</strong> if an employer or careers service asks for a Word document.",
          "Both formats keep your layout intact and stay ATS-friendly, so your CV looks the same wherever it lands.",
        ],
      },
      {
        type: "faq",
        items: [
          {
            q: "How long does it take to build a CV?",
            a: "Most students finish a first draft in 15–20 minutes because the builder is guided and the AI writes the bullet points for you.",
          },
          {
            q: "Can I edit my CV after downloading?",
            a: "Yes. You can return and update your CV anytime, and the DOCX export is fully editable in Word or Google Docs.",
          },
          {
            q: "What if I have no work experience?",
            a: "That is exactly who Careero is built for. Read our guide on <a href=\"/guides/student-cv-with-no-experience\">writing a CV with no experience</a>.",
          },
        ],
      },
      closingCta(
        "Start building your student CV",
        "It's free to begin — add your details and let Careero do the writing.",
        "Start your student CV",
      ),
    ],
  },

  // --------------------------------------------------- WRITE CV STUDENTS ----
  {
    slug: "create-cv-for-students",
    title: "How to Write a CV for Students (2026 Guide) | Careero",
    description:
      "Learn how to write a student CV that gets interviews: what to include, how to structure it, and how to describe projects and experience. Then build yours free with Careero.",
    h1: "How to write a CV for students",
    type: "website",
    blocks: [
      {
        type: "hero",
        kicker: "Student CV Guide",
        h1: "How to write a CV for students",
        lead:
          "A practical, no-jargon guide to writing a student CV that recruiters actually read — what to include, how to order it, and how to make limited experience look strong.",
        primaryCta: { text: "Build my CV now", href: APP },
        secondaryCta: { text: "Read the first-CV guide", href: "/first-cv" },
      },
      {
        type: "prose",
        h2: "What to include on a student CV",
        paragraphs: [
          "A strong student CV usually fits on one page and leads with education, because that is your most relevant and recent achievement. Around it, you add the experiences that show skills — even if they did not come from a formal job.",
        ],
        bullets: [
          "<strong>Contact details</strong> — name, email, phone, city, and links to LinkedIn or GitHub.",
          "<strong>Personal summary</strong> — two or three lines on who you are and what you're looking for.",
          "<strong>Education</strong> — your degree, expected grade, relevant modules and academic highlights.",
          "<strong>Projects</strong> — coursework and personal projects described by outcome and skills.",
          "<strong>Experience</strong> — part-time work, internships, volunteering and society roles.",
          "<strong>Skills</strong> — tools, technologies and languages relevant to the role.",
        ],
      },
      {
        type: "prose",
        h2: "How to structure and order your CV",
        paragraphs: [
          "Order sections by relevance, not by date alone. For most students that means: summary, education, projects, experience, then skills. If you're applying for something technical, projects can move above education-detail so your practical skills are seen first.",
          "Keep formatting simple and consistent. One clean font, clear headings, and plenty of white space beat a heavily designed layout that confuses both readers and screening software.",
        ],
        subsections: [
          {
            h3: "Write achievement-focused bullet points",
            paragraphs: [
              "Start each bullet with an action verb and, where you can, include a number or result. &ldquo;Built a weather app in Python used by 30 classmates&rdquo; says far more than &ldquo;did a Python project.&rdquo;",
            ],
          },
          {
            h3: "Tailor it to each application",
            paragraphs: [
              "Mirror the language of the job description. If a role asks for teamwork and data analysis, make sure those words appear naturally in your projects and experience.",
            ],
          },
        ],
      },
      {
        type: "faq",
        items: [
          {
            q: "How long should a student CV be?",
            a: "One page. Recruiters spend seconds on a first scan, so keep it focused and remove anything that isn't relevant.",
          },
          {
            q: "Should I include my high school?",
            a: "Include it briefly if you're early in university or it has notable results, then drop the detail as your degree and projects fill the page.",
          },
          {
            q: "Do I need a personal summary?",
            a: "Yes — a short, specific summary helps a recruiter place you instantly. Careero can draft one for you based on your details.",
          },
        ],
      },
      closingCta(
        "Turn this guide into a finished CV",
        "Careero applies all of these best practices automatically as you build.",
        "Build my CV now",
      ),
    ],
  },

  // ------------------------------------------------------------ FIRST CV ----
  {
    slug: "first-cv",
    title: "How to Write Your First CV (Step-by-Step) | Careero",
    description:
      "Writing your first CV? This step-by-step guide shows students exactly what to put on a first CV and how to describe skills with no work experience. Start free with Careero.",
    h1: "How to write your first CV",
    type: "website",
    blocks: [
      {
        type: "hero",
        kicker: "First CV Guide",
        h1: "How to write your first CV",
        lead:
          "Your first CV feels intimidating because it's a blank page and you're not sure you have &ldquo;enough&rdquo; to fill it. You do — and this guide (plus Careero's AI) will help you prove it.",
        primaryCta: { text: "Build my first CV", href: APP },
        secondaryCta: { text: "CV with no experience", href: "/guides/student-cv-with-no-experience" },
      },
      {
        type: "steps",
        h2: "Your first CV, step by step",
        items: [
          {
            title: "Start with contact details",
            text: "Name, professional email, phone, city and a LinkedIn or GitHub link. Skip your full address and date of birth.",
          },
          {
            title: "Write a short summary",
            text: "Two or three lines: who you are, what you study, and the kind of role you want. Careero can draft this from your answers.",
          },
          {
            title: "Lead with education",
            text: "Your degree, expected grade and relevant modules. Add academic projects and achievements here.",
          },
          {
            title: "Add projects and experience",
            text: "Coursework, personal projects, part-time jobs and volunteering — described by what you did and learned.",
          },
          {
            title: "Finish with skills",
            text: "List the tools, software and languages relevant to your target role. Keep it honest and specific.",
          },
        ],
      },
      {
        type: "prose",
        h2: "What counts as experience on a first CV",
        paragraphs: [
          "Almost everything counts when it's described well. A group coursework project shows teamwork and problem-solving. A part-time retail job shows reliability and communication. Running a society shows organisation and leadership.",
          "The trick is to describe each one by its <strong>outcome and the skills it demonstrates</strong>, not just the title. Careero's AI does this rewriting for you so your first CV reads like someone who knows their value.",
        ],
      },
      {
        type: "faq",
        items: [
          {
            q: "What do I put on a first CV with no jobs?",
            a: "Education, academic and personal projects, volunteering, societies, and any part-time or casual work. Our <a href=\"/guides/student-cv-with-no-experience\">no-experience guide</a> covers this in detail.",
          },
          {
            q: "How do I make my first CV look professional?",
            a: "Use a clean, consistent template and standard headings. Careero's ATS-friendly templates handle the formatting so you can focus on content.",
          },
          {
            q: "Can Careero write my first CV for me?",
            a: "Careero drafts your summary and rewrites your notes into strong bullet points — you stay in control and edit anything you like.",
          },
        ],
      },
      closingCta(
        "Write your first CV today",
        "No blank page. Answer a few questions and Careero builds it with you.",
        "Build my first CV",
      ),
    ],
  },

  // ------------------------------------------------------ CV INTERNSHIP -----
  {
    slug: "cv-for-internship",
    title: "CV for Internship — Templates & Examples for Students | Careero",
    description:
      "Write a standout internship CV. Learn what employers look for, how to tailor your CV to an internship, and build one free with Careero's AI CV builder. PDF & DOCX download.",
    h1: "Write a CV for your internship application",
    type: "website",
    blocks: [
      {
        type: "hero",
        kicker: "CV for Internship",
        h1: "Write a CV for your internship application",
        lead:
          "Internship recruiters know you're early in your career — they're looking for potential, relevant coursework and a genuine interest in the field. Careero helps you show all three.",
        primaryCta: { text: "Start my internship CV", href: APP },
        secondaryCta: { text: "See templates", href: "/student-cv-templates" },
      },
      {
        type: "prose",
        h2: "What internship recruiters look for",
        paragraphs: [
          "For internships, employers weigh relevant modules, projects and enthusiasm more heavily than years of experience. A focused CV that clearly connects your studies to the role stands out immediately.",
        ],
        bullets: [
          "A summary that names the internship field and your motivation.",
          "Relevant coursework and projects placed high on the page.",
          "Transferable skills from any job, society or volunteering.",
          "Clean, ATS-friendly formatting so nothing gets filtered out.",
        ],
      },
      {
        type: "steps",
        h2: "Tailor your CV to the internship",
        items: [
          {
            title: "Read the posting closely",
            text: "Note the skills and keywords the employer repeats — those are what the CV should echo.",
          },
          {
            title: "Lead with a targeted summary",
            text: "Say which field the internship is in and why you want it. Careero drafts this for you.",
          },
          {
            title: "Surface relevant projects",
            text: "Move the most relevant coursework and projects to the top and describe them by result.",
          },
        ],
      },
      {
        type: "faq",
        items: [
          {
            q: "How is an internship CV different from a normal CV?",
            a: "It leans more on education, relevant projects and motivation, and less on work history. It's also tailored tightly to the specific internship.",
          },
          {
            q: "Should I write a summary for an internship CV?",
            a: "Yes. A short, targeted summary that names the field and your interest helps recruiters place you fast. Careero's internship summary helper drafts one for you.",
          },
          {
            q: "Can I reuse one CV for every internship?",
            a: "Tailor it each time. Careero makes this quick — update the summary and reorder projects to match each posting.",
          },
        ],
      },
      closingCta(
        "Land the internship interview",
        "Build a focused, ATS-friendly internship CV in minutes with Careero.",
        "Start my internship CV",
      ),
    ],
  },

  // -------------------------------------------------- ATS-FRIENDLY CV -------
  {
    slug: "ats-friendly-student-cv",
    title: "ATS-Friendly Student CV — Pass the Screening Software | Careero",
    description:
      "Make sure your student CV passes applicant tracking systems (ATS). Learn what ATS software checks and build an ATS-friendly CV free with Careero. PDF & DOCX download.",
    h1: "Build an ATS-friendly student CV",
    type: "website",
    blocks: [
      {
        type: "hero",
        kicker: "ATS-Friendly CV",
        h1: "Build an ATS-friendly student CV",
        lead:
          "Most applications pass through an applicant tracking system before a human sees them. Careero's templates are built to be parsed cleanly, so your CV actually reaches the recruiter.",
        primaryCta: { text: "Create an ATS-friendly CV", href: APP },
        secondaryCta: { text: "Browse templates", href: "/student-cv-templates" },
      },
      {
        type: "prose",
        h2: "What is an ATS, and why it matters",
        paragraphs: [
          "An <strong>applicant tracking system (ATS)</strong> is software employers use to collect and scan CVs. It reads your CV as text, pulls out sections and keywords, and ranks or filters candidates before a recruiter reviews anyone.",
          "If your CV uses unusual layouts, text inside images, or non-standard headings, an ATS can misread or skip it — which means a strong candidate can be filtered out for formatting reasons alone.",
        ],
      },
      {
        type: "cards",
        h2: "What makes a CV ATS-friendly",
        items: [
          {
            icon: "🔤",
            title: "Standard headings",
            text: "Clear sections like Education, Experience and Skills that an ATS recognises instantly.",
          },
          {
            icon: "📄",
            title: "Simple layout",
            text: "Single-column, no text boxes or images holding key information — everything stays machine-readable.",
          },
          {
            icon: "🔑",
            title: "Relevant keywords",
            text: "Skills and terms from the job description, included naturally so the ATS matches your CV to the role.",
          },
          {
            icon: "🧾",
            title: "Clean file export",
            text: "A properly structured PDF or DOCX that parses correctly — both of Careero's exports are ATS-safe.",
          },
        ],
      },
      {
        type: "faq",
        items: [
          {
            q: "Are Careero's CVs ATS-friendly?",
            a: "Yes. Every template uses a clean, single-column structure with standard headings so applicant tracking systems can read your CV correctly.",
          },
          {
            q: "Is PDF or DOCX better for ATS?",
            a: "Both work when the file is well structured. Careero produces ATS-safe PDF and DOCX exports, so you can use whichever an employer requests.",
          },
          {
            q: "How do I add keywords without stuffing?",
            a: "Weave the skills from the job description into your real projects and experience. Careero's AI helps phrase them naturally.",
          },
        ],
      },
      closingCta(
        "Make your CV pass the screening",
        "Start with an ATS-friendly template and let Careero handle the formatting.",
        "Create an ATS-friendly CV",
      ),
    ],
  },

  // -------------------------------------------------- CV TEMPLATES ----------
  {
    slug: "student-cv-templates",
    title: "Student CV Templates — Modern & ATS-Friendly | Careero",
    description:
      "Choose from modern, ATS-friendly student CV templates. Professional designs built for first CVs, internships and graduate roles. Fill one in free with Careero and download as PDF or DOCX.",
    h1: "Modern, ATS-friendly student CV templates",
    type: "website",
    blocks: [
      {
        type: "hero",
        kicker: "Student CV Templates",
        h1: "Modern, ATS-friendly student CV templates",
        lead:
          "Professionally designed templates built for students — clean enough to pass screening software, polished enough to impress a recruiter. Pick one and Careero fills it in with you.",
        primaryCta: { text: "Choose a template & start", href: APP },
        secondaryCta: { text: "What makes a CV ATS-safe?", href: "/ats-friendly-student-cv" },
      },
      {
        type: "cards",
        h2: "Five templates for every kind of student application",
        intro:
          "Every template is ATS-friendly and exports to <strong>PDF and DOCX</strong>. Switch between them anytime — your content stays, only the design changes.",
        items: [
          {
            icon: "🟦",
            title: "Classic",
            text: "A timeless single-column layout that suits any field and always parses cleanly in an ATS.",
          },
          {
            icon: "🟪",
            title: "Modern",
            text: "A contemporary design with a subtle accent colour — professional without looking like a template.",
          },
          {
            icon: "⬜",
            title: "Minimal",
            text: "Maximum white space and clarity for when your content should do all the talking.",
          },
          {
            icon: "🎓",
            title: "Academic",
            text: "Structured for research, publications and coursework — ideal for postgraduate and scholarship applications.",
          },
          {
            icon: "🎨",
            title: "Creative",
            text: "A touch more personality for design, media and marketing students — still clean and recruiter-safe.",
          },
        ],
      },
      {
        type: "prose",
        h2: "Designed to look good and read well",
        paragraphs: [
          "Every Careero template balances two audiences: the <strong>software</strong> that scans your CV first and the <strong>recruiter</strong> who reads it second. That means clean structure, standard headings and consistent spacing — never design that gets in the way of the content.",
          "You can switch templates at any time without redoing your work. Your details stay the same; only the design changes, and every option exports to PDF and DOCX.",
        ],
      },
      {
        type: "faq",
        items: [
          {
            q: "Are the templates really free?",
            a: "You can start building with any template for free at <a href=\"" + APP + "\" rel=\"noopener\">app.careero.app</a>.",
          },
          {
            q: "Can I switch templates later?",
            a: "Yes. Change template anytime — your content is preserved and only the design updates.",
          },
          {
            q: "Which template is best for me?",
            a: "Classic or Minimal suit most students; Technical is great for CS, engineering and data roles. All are ATS-friendly.",
          },
        ],
      },
      closingCta(
        "Pick your template and start",
        "Choose a design and let Careero fill it with strong, ready-to-send content.",
        "Choose a template & start",
      ),
    ],
  },

  // -------------------------------------------------- AI CV BUILDER ---------
  {
    slug: "ai-cv-builder-for-students",
    title: "AI CV Builder for Students — Write Your CV with AI | Careero",
    description:
      "Careero's AI CV builder writes strong, ATS-friendly CV content for students. Describe a project or internship and AI turns it into quantified bullet points. Start free and download as PDF or DOCX.",
    h1: "An AI CV builder that writes with you",
    type: "website",
    blocks: [
      {
        type: "hero",
        kicker: "AI CV Writing",
        h1: "An AI CV builder that writes with you",
        lead:
          "Careero's AI turns rough notes into recruiter-ready CV content. Describe what you did in plain words and get clear, quantified, ATS-friendly bullet points — plus a personal summary drafted for you.",
        primaryCta: { text: "Try Careero for free", href: APP },
        secondaryCta: { text: "See how it works", href: "#how" },
      },
      {
        type: "cards",
        h2: "What the AI helps you write",
        items: [
          {
            icon: "✍️",
            title: "Personal summary",
            text: "A confident two-to-three line intro tailored to your field and the roles you want.",
          },
          {
            icon: "🧩",
            title: "Project descriptions",
            text: "Turn a class or side project into achievement bullets that show real, transferable skills.",
            href: "/guides/how-to-write-projects-in-a-cv",
          },
          {
            icon: "💼",
            title: "Internship summaries",
            text: "Describe an internship or placement in strong, results-focused language.",
            href: "/cv-for-internship",
          },
          {
            icon: "🔁",
            title: "Rewrites & polish",
            text: "Paste a weak bullet and get a stronger, quantified version that keeps your meaning.",
          },
        ],
      },
      {
        type: "steps",
        id: "how",
        h2: "How AI writing works in Careero",
        items: [
          {
            title: "Describe it in plain words",
            text: "Write a sentence about a project, job or internship — no CV-speak required.",
          },
          {
            title: "AI rewrites it",
            text: "Careero produces clear, action-led, quantified bullet points in seconds.",
          },
          {
            title: "You approve and edit",
            text: "Keep, tweak or regenerate any suggestion. You're always in control of the final wording.",
          },
        ],
      },
      {
        type: "prose",
        h2: "Helpful, not robotic",
        paragraphs: [
          "AI is a drafting partner, not an autopilot. Careero suggests strong phrasing and structure, but you review every line so your CV stays honest and sounds like you.",
          "The result is a CV you could have written on your best day — clear, specific and free of the vague filler that makes early-career CVs blend together.",
        ],
      },
      {
        type: "faq",
        items: [
          {
            q: "Does the AI write my whole CV automatically?",
            a: "It drafts summaries and rewrites your notes into strong bullet points, but you review and approve everything. You stay in control of the content.",
          },
          {
            q: "Will my CV sound generic?",
            a: "No — the AI works from your specific projects and experience, so the output is personal to you. You can regenerate or edit any line.",
          },
          {
            q: "Is it free to try?",
            a: "Yes. Start free at <a href=\"" + APP + "\" rel=\"noopener\">app.careero.app</a> and download as PDF or DOCX.",
          },
        ],
      },
      closingCta(
        "Let AI write your next CV",
        "Describe your experience and Careero turns it into a strong, ATS-friendly CV.",
        "Try Careero for free",
      ),
    ],
  },

  // -------------------------------------------------- BLOG INDEX ------------
  {
    slug: "blog",
    title: "Careero Blog — CV & Career Tips for Students",
    description:
      "Practical CV and career advice for students: how to write your first CV, describe projects, and build a CV with no experience. Learn, then build free with Careero.",
    h1: "Career tips and CV guides for students",
    type: "website",
    blocks: [
      {
        type: "hero",
        kicker: "Careero Blog",
        h1: "Career tips and CV guides for students",
        lead:
          "Straightforward, student-focused advice on writing CVs, describing your projects, and getting noticed for internships and graduate roles.",
        primaryCta: { text: "Build your CV now", href: APP },
      },
      {
        type: "cards",
        h2: "Latest guides",
        items: [
          {
            icon: "📝",
            title: "How to write your first CV",
            text: "A step-by-step walkthrough for students creating a CV for the very first time.",
            href: "/blog/how-to-write-first-cv",
          },
          {
            icon: "🧩",
            title: "How to describe student projects",
            text: "Turn coursework and side projects into achievement-focused CV bullet points.",
            href: "/guides/how-to-write-projects-in-a-cv",
          },
          {
            icon: "🚀",
            title: "How to write a CV with no experience",
            text: "What to include — and how to describe it — when you don't have formal work history yet.",
            href: "/guides/student-cv-with-no-experience",
          },
          {
            icon: "✉️",
            title: "How to write a cover letter as a student",
            text: "A simple 4-paragraph structure that works even with little experience.",
            href: "/blog/cover-letter-for-students",
          },
          {
            icon: "⚠️",
            title: "10 common student CV mistakes",
            text: "The fixable reasons student CVs get rejected — and how to fix each one.",
            href: "/blog/common-cv-mistakes-students",
          },
          {
            icon: "🔑",
            title: "CV keywords: getting past the ATS",
            text: "Use the right keywords naturally so screening software ranks your CV.",
            href: "/blog/cv-keywords-and-ats",
          },
          {
            icon: "🎤",
            title: "How to prepare for an internship interview",
            text: "Research, common questions, the STAR method and what to ask.",
            href: "/blog/internship-interview-prep",
          },
        ],
      },
      closingCta(
        "Put the advice into practice",
        "Careero builds these best practices into every CV automatically.",
        "Build your CV now",
      ),
    ],
  },

  // -------------------------------------------------- BLOG: FIRST CV --------
  {
    slug: "blog/how-to-write-first-cv",
    title: "How to Write Your First CV: A Student's Step-by-Step Guide | Careero",
    description:
      "A complete, beginner-friendly guide to writing your first CV as a student — what to include, how to structure each section, and common mistakes to avoid. Build yours free with Careero.",
    h1: "How to write your first CV: a student's step-by-step guide",
    type: "article",
    datePublished: PUB,
    dateModified: MOD,
    blocks: [
      {
        type: "hero",
        kicker: "Guide · 6 min read",
        h1: "How to write your first CV: a student's step-by-step guide",
        lead:
          "The hardest CV you'll ever write is your first one — not because it's long, but because you're starting from nothing. Here's exactly how to go from blank page to a CV you're proud to send.",
        primaryCta: { text: "Build my first CV", href: APP },
      },
      {
        type: "prose",
        h2: "1. Get the basics down first",
        paragraphs: [
          "Start with the easy part: your name, a professional-sounding email, a phone number, your city, and links to LinkedIn or GitHub if you have them. Leave off your full home address, date of birth and photo — they're unnecessary and can introduce bias.",
        ],
      },
      {
        type: "prose",
        h2: "2. Write a short, specific summary",
        paragraphs: [
          "Two or three lines that answer: who are you, what do you study, and what are you looking for? &ldquo;Second-year Computer Science student seeking a summer software internship, with hands-on Python and web-development project experience&rdquo; is far stronger than &ldquo;hard-working student looking for opportunities.&rdquo;",
          "If you're stuck, Careero can draft this summary from the details you enter and let you refine it.",
        ],
      },
      {
        type: "prose",
        h2: "3. Lead with education",
        paragraphs: [
          "As a student, your education is your headline. List your degree, university, expected graduation and predicted or current grade. Add relevant modules and any academic achievements — a high project mark, a scholarship, a prize.",
        ],
      },
      {
        type: "prose",
        h2: "4. Turn projects and experience into achievements",
        paragraphs: [
          "This is where most first CVs go wrong: they list duties instead of achievements. Rewrite each item to start with an action verb and, where possible, a result. Describe coursework, personal projects, part-time jobs, volunteering and societies by what you did and what changed because of it.",
        ],
        bullets: [
          "Before: &ldquo;Worked in a team on a database project.&rdquo;",
          "After: &ldquo;Built a library database with 3 classmates in SQL, cutting lookup time in our demo by 40%.&rdquo;",
        ],
      },
      {
        type: "prose",
        h2: "5. Finish with skills — and proofread",
        paragraphs: [
          "List the tools, software and languages relevant to your target role, and be honest about your level. Then proofread ruthlessly: spelling and consistency mistakes are the fastest way to lose a recruiter's trust.",
        ],
      },
      {
        type: "faq",
        items: [
          {
            q: "How long should my first CV be?",
            a: "One page. As a student you rarely need more, and a focused one-pager reads far better than a padded two-pager.",
          },
          {
            q: "What's the biggest first-CV mistake?",
            a: "Listing duties instead of achievements. Always describe the result or skill, not just the task.",
          },
          {
            q: "Can Careero help me write it?",
            a: "Yes — it drafts your summary and rewrites notes into strong bullet points. <a href=\"" + APP + "\" rel=\"noopener\">Start free</a>.",
          },
        ],
      },
      closingCta(
        "Ready to write yours?",
        "Careero guides you through every step above and writes the tricky parts with you.",
        "Build my first CV",
      ),
    ],
  },

  // ------------------------------------------ BLOG: DESCRIBE PROJECTS --------
  {
    slug: "guides/how-to-write-projects-in-a-cv",
    title: "How to Write Projects in a Student CV (With Examples) | Careero",
    description:
      "Learn how to describe academic and personal projects on your CV so they show real skills. Includes before-and-after examples and a simple formula. Build your CV free with Careero.",
    h1: "How to write projects in a student CV",
    type: "article",
    datePublished: PUB,
    dateModified: MOD,
    blocks: [
      {
        type: "hero",
        kicker: "Guide · 5 min read",
        h1: "How to write projects in a student CV",
        lead:
          "Projects are the most valuable thing on a student CV — they prove you can actually do the work. But only if you describe them well. Here's a simple formula and real examples.",
        primaryCta: { text: "Improve my projects", href: APP },
      },
      {
        type: "prose",
        h2: "The problem with most project descriptions",
        paragraphs: [
          "Most students write projects like a syllabus entry: &ldquo;Group project using Java.&rdquo; That tells a recruiter nothing about what you did, how well you did it, or what you learned. A great project bullet answers all three in one line.",
        ],
      },
      {
        type: "prose",
        h2: "A simple formula: action + what + result",
        paragraphs: [
          "Use this structure: <strong>[action verb] + [what you built] + [result or skill shown]</strong>. Add a number wherever you honestly can — team size, users, performance, grade.",
        ],
        subsections: [
          {
            h3: "Before and after",
            bullets: [
              "Before: &ldquo;Made a website for a module.&rdquo;",
              "After: &ldquo;Designed and built a responsive charity website in React, achieving the top mark in a cohort of 60.&rdquo;",
              "Before: &ldquo;Data analysis project in Python.&rdquo;",
              "After: &ldquo;Analysed 10k rows of transport data in Python and pandas to identify three peak-congestion routes, presented to the class.&rdquo;",
            ],
          },
        ],
      },
      {
        type: "prose",
        h2: "Which projects to include",
        paragraphs: [
          "Choose projects that show skills relevant to the role you want, and that you can talk about confidently in an interview. Two or three well-described projects beat a long list of shallow ones. Coursework, hackathons, personal builds and open-source contributions all count.",
        ],
      },
      {
        type: "faq",
        items: [
          {
            q: "How many projects should I list?",
            a: "Two to four strong, relevant projects is ideal. Depth and clear results beat a long, shallow list.",
          },
          {
            q: "Should I include the tech stack?",
            a: "Yes — naming the languages and tools helps both recruiters and ATS software match you to technical roles.",
          },
          {
            q: "Can Careero rewrite my project descriptions?",
            a: "Yes. Describe the project in plain words and Careero's AI turns it into strong, quantified bullets. <a href=\"" + APP + "\" rel=\"noopener\">Try it free</a>.",
          },
        ],
      },
      closingCta(
        "Make your projects stand out",
        "Careero's project helper rewrites your coursework and side projects into achievement bullets.",
        "Improve my projects",
      ),
    ],
  },

  // ------------------------------------------ BLOG: NO EXPERIENCE ------------
  {
    slug: "guides/student-cv-with-no-experience",
    title: "How to Create a Student CV With No Work Experience | Careero",
    description:
      "No work experience? You can still write a strong CV. Learn what to include, how to describe transferable skills, and how to fill the page with substance. Build yours free with Careero.",
    h1: "How to create a student CV with no work experience",
    type: "article",
    datePublished: PUB,
    dateModified: MOD,
    blocks: [
      {
        type: "hero",
        kicker: "Guide · 5 min read",
        h1: "How to create a student CV with no work experience",
        lead:
          "&ldquo;I have no experience&rdquo; almost always means &ldquo;I have no job title yet.&rdquo; You have more to work with than you think — here's how to find it and put it on the page.",
        primaryCta: { text: "Start my CV free", href: APP },
      },
      {
        type: "prose",
        h2: "Redefine what “experience” means",
        paragraphs: [
          "Experience isn't only paid, full-time jobs. It's any situation where you built something, solved a problem or worked with people. For a student, that includes coursework, academic and personal projects, volunteering, societies and clubs, part-time or casual work, and even significant self-taught skills.",
        ],
      },
      {
        type: "prose",
        h2: "Lead with education and projects",
        paragraphs: [
          "With no formal work history, your degree and projects carry the CV. Detail relevant modules, strong grades and academic achievements, then give real space to two or three projects described by their results and the skills they show.",
        ],
      },
      {
        type: "prose",
        h2: "Show transferable skills with evidence",
        paragraphs: [
          "Recruiters hiring students look for transferable skills: teamwork, communication, problem-solving, reliability and initiative. Don't just claim them — <strong>prove</strong> them with a specific example.",
        ],
        bullets: [
          "Teamwork: &ldquo;Coordinated a 5-person group project to an on-time submission and a distinction grade.&rdquo;",
          "Communication: &ldquo;Presented research findings to a class of 40 and answered live questions.&rdquo;",
          "Initiative: &ldquo;Taught myself Figma to design the UI for a personal app in two weeks.&rdquo;",
        ],
      },
      {
        type: "prose",
        h2: "Fill the page with substance, not filler",
        paragraphs: [
          "A short, honest, well-described CV beats a padded one. Use a clean template, keep it to one page, and let each line earn its place. Careero helps by turning your real experiences into strong, specific bullet points — no invented history required.",
        ],
      },
      {
        type: "faq",
        items: [
          {
            q: "Can I get an interview with no experience?",
            a: "Absolutely. Employers hiring students expect limited work history and focus on potential, projects and transferable skills — so present those clearly.",
          },
          {
            q: "What do I put in the experience section?",
            a: "Volunteering, societies, part-time or casual work, and significant projects. Describe each by the skills it demonstrates.",
          },
          {
            q: "How does Careero help with no experience?",
            a: "It's built for first CVs — it surfaces the right sections and rewrites your notes into strong content. <a href=\"" + APP + "\" rel=\"noopener\">Start free</a>.",
          },
        ],
      },
      closingCta(
        "You have more than enough for a great CV",
        "Let Careero help you find it and write it — no experience required to start.",
        "Start my CV free",
      ),
    ],
  },

  // -------------------------------------------------- CV EXAMPLES -----------
  {
    slug: "student-cv-examples",
    title: "Student CV Examples — Real Samples & What Makes Them Work | Careero",
    description:
      "See what a great student CV looks like. Real, annotated student CV examples for first CVs, internships and graduate roles — then build your own free with Careero.",
    h1: "Student CV examples that actually get interviews",
    type: "website",
    blocks: [
      {
        type: "hero",
        kicker: "CV Examples",
        h1: "Student CV examples that actually get interviews",
        lead:
          "The fastest way to write a great CV is to see one first. These examples show how strong student CVs are structured — and how to describe projects and experience the way recruiters want to read them.",
        primaryCta: { text: "Build my CV from an example", href: APP },
        secondaryCta: { text: "Browse templates", href: "/student-cv-templates" },
      },
      {
        type: "cards",
        h2: "Examples for every kind of student",
        intro:
          "An example is a starting point, not a script — use the structure, then fill it with <strong>your</strong> projects, modules and experience.",
        items: [
          {
            icon: "🎓",
            title: "First-CV example",
            text: "For students with little formal work history — education-led, with projects and volunteering doing the heavy lifting.",
            href: "/first-cv",
          },
          {
            icon: "💼",
            title: "Internship CV example",
            text: "Tailored to a specific internship, with a targeted summary and the most relevant coursework up top.",
            href: "/cv-for-internship",
          },
          {
            icon: "💻",
            title: "Technical / CS example",
            text: "Projects and skills first, with a tech stack and links to GitHub — ideal for software and data roles.",
            href: "/guides/github-profile-for-students",
          },
          {
            icon: "🎯",
            title: "Graduate-role example",
            text: "A polished one-pager that balances degree, projects and any placement or part-time experience.",
          },
        ],
      },
      {
        type: "prose",
        h2: "What every strong student CV example has in common",
        paragraphs: [
          "Look past the visual design and the best examples share the same fundamentals: a clear one-page layout, a specific summary, education front and centre, and — most importantly — <strong>achievement-focused bullet points</strong> instead of lists of duties.",
        ],
        bullets: [
          "A specific, role-aware summary (not &ldquo;hard-working student&rdquo;).",
          "Projects described by result and skill, with numbers where possible.",
          "Consistent formatting and standard, ATS-friendly headings.",
          "Everything relevant, nothing padded — one focused page.",
        ],
      },
      {
        type: "faq",
        items: [
          {
            q: "Can I copy a CV example directly?",
            a: "Use the structure and phrasing style, but always fill it with your own real experience. Careero starts you from a proven layout and helps you write your own content.",
          },
          {
            q: "What's the difference between an example and a template?",
            a: "A <a href=\"/student-cv-templates\">template</a> is the blank design; an example is a filled-in sample showing how to word each section. Careero gives you both.",
          },
          {
            q: "Do these examples work for internships?",
            a: "Yes — see the dedicated <a href=\"/cv-for-internship\">internship CV</a> guidance for how to tailor an example to a specific role.",
          },
        ],
      },
      closingCta(
        "Turn an example into your CV",
        "Start from a proven structure and let Careero help you write every section.",
        "Build my CV from an example",
      ),
    ],
  },

  // -------------------------------------------------- DOWNLOAD PDF/DOCX -----
  {
    slug: "download-cv-pdf",
    title: "Download Your CV as PDF or Word (DOCX) — Free | Careero",
    description:
      "Build your student CV and download it as a print-ready PDF or an editable Word DOCX file. Free, ATS-friendly, and formatted consistently across both formats with Careero.",
    h1: "Download your CV as PDF or Word (DOCX)",
    type: "website",
    blocks: [
      {
        type: "hero",
        kicker: "PDF & DOCX Download",
        h1: "Download your CV as PDF or Word (DOCX)",
        lead:
          "Finish your CV in Careero and export it exactly how each application needs it — a pixel-perfect PDF for online forms and job boards, or a fully editable Word DOCX when someone asks for one.",
        primaryCta: { text: "Create & download my CV", href: APP },
        secondaryCta: { text: "See templates", href: "/student-cv-templates" },
      },
      {
        type: "prose",
        h2: "Download as PDF",
        paragraphs: [
          "PDF is the safest format for most applications: it looks identical on every device and can't be accidentally reformatted. Careero produces a clean, ATS-friendly PDF with selectable text (never a flat image), so applicant tracking systems can still read every line.",
        ],
      },
      {
        type: "prose",
        id: "docx",
        h2: "Download as Word (DOCX)",
        paragraphs: [
          "Some universities, careers services and recruiters ask for an editable Word document. Careero exports a <strong>DOCX</strong> that opens cleanly in Microsoft Word or Google Docs, keeping your layout and headings intact so you can make quick edits without breaking the design.",
        ],
      },
      {
        type: "cards",
        h2: "Which format should you use?",
        items: [
          {
            icon: "📄",
            title: "Use PDF when…",
            text: "Applying online, uploading to a job board, or emailing directly — anywhere the layout must stay fixed.",
          },
          {
            icon: "📝",
            title: "Use DOCX when…",
            text: "An employer or careers service specifically asks for Word, or you want to hand-edit outside Careero.",
          },
          {
            icon: "✅",
            title: "Either way…",
            text: "Both exports stay ATS-friendly and keep identical formatting, so your CV looks the same wherever it lands.",
          },
        ],
      },
      {
        type: "faq",
        items: [
          {
            q: "Is downloading my CV free?",
            a: "You can build and export your CV at <a href=\"" + APP + "\" rel=\"noopener\">app.careero.app</a>. Start free and download as PDF or DOCX.",
          },
          {
            q: "Is the PDF ATS-friendly?",
            a: "Yes. Careero's PDF keeps selectable, structured text — not a flat image — so applicant tracking systems can parse it. Learn more about <a href=\"/ats-friendly-student-cv\">ATS-friendly CVs</a>.",
          },
          {
            q: "Can I edit the DOCX after downloading?",
            a: "Yes — the DOCX opens and edits normally in Word or Google Docs while keeping your Careero layout.",
          },
        ],
      },
      closingCta(
        "Build once, download in any format",
        "Create your CV with Careero and export a PDF or Word file in a click.",
        "Create & download my CV",
      ),
    ],
  },

  // -------------------------------------------------- LINKEDIN --------------
  {
    slug: "guides/linkedin-profile-for-students",
    title: "LinkedIn Profile for Students — Tips to Get Noticed | Careero",
    description:
      "Build a LinkedIn profile that gets students noticed by recruiters: headline, About section, projects and skills. Practical tips that pair perfectly with your Careero CV.",
    h1: "Build a LinkedIn profile that gets you noticed",
    type: "website",
    blocks: [
      {
        type: "hero",
        kicker: "LinkedIn for Students",
        h1: "Build a LinkedIn profile that gets you noticed",
        lead:
          "Recruiters check LinkedIn before (and after) they read your CV. A clear, consistent profile makes you easy to find and easy to trust — here's how to build one as a student.",
        primaryCta: { text: "Build my CV first", href: APP },
        secondaryCta: { text: "Write a CV with no experience", href: "/guides/student-cv-with-no-experience" },
      },
      {
        type: "steps",
        h2: "The essentials, in order",
        items: [
          {
            title: "A clear photo and headline",
            text: "A friendly, well-lit headshot and a headline that says what you study and what you're looking for — e.g. &ldquo;Computer Science student · seeking summer software internships.&rdquo;",
          },
          {
            title: "A short, specific About section",
            text: "Three or four lines on your field, key skills and goals. Mirror the language of the roles you want.",
          },
          {
            title: "Projects, education and experience",
            text: "List the same projects and experience as your CV, described the same way. Consistency builds credibility.",
          },
          {
            title: "Skills and a few connections",
            text: "Add the skills relevant to your target roles and connect with classmates, lecturers and societies to grow your network.",
          },
        ],
      },
      {
        type: "prose",
        h2: "Keep LinkedIn and your CV in sync",
        paragraphs: [
          "Your LinkedIn profile and CV should tell the same story. Recruiters get suspicious when dates, titles or projects don't match. The easiest approach is to write strong CV content first, then mirror it on LinkedIn.",
          "Careero helps you produce that content once — clear summaries and quantified project bullets — which you can reuse directly in your LinkedIn About and Experience sections.",
        ],
      },
      {
        type: "faq",
        items: [
          {
            q: "Do students really need LinkedIn?",
            a: "Yes — it's where many recruiters search for early-career talent and verify your CV. Even a simple, consistent profile helps.",
          },
          {
            q: "What should my LinkedIn headline say?",
            a: "State what you study and what you're seeking, e.g. &ldquo;Marketing student · seeking 2026 summer internships.&rdquo; Keep it specific.",
          },
          {
            q: "How do I match LinkedIn to my CV?",
            a: "Write your CV content in Careero first, then reuse the same summaries and bullet points on LinkedIn so both are consistent.",
          },
        ],
      },
      closingCta(
        "Get your CV and LinkedIn working together",
        "Write strong, reusable content once with Careero — then mirror it on LinkedIn.",
        "Build my CV first",
      ),
    ],
  },

  // -------------------------------------------------- GITHUB ----------------
  {
    slug: "guides/github-profile-for-students",
    title: "GitHub Profile Tips for Students (Put It on Your CV) | Careero",
    description:
      "Turn your GitHub into a portfolio that strengthens your CV. Tips on your README, pinned projects and commit history for students applying to tech roles. Build your CV free with Careero.",
    h1: "Make your GitHub profile work for your CV",
    type: "website",
    blocks: [
      {
        type: "hero",
        kicker: "GitHub for Students",
        h1: "Make your GitHub profile work for your CV",
        lead:
          "For tech roles, your GitHub is living proof of what you can build. A tidy profile with a few well-presented projects can matter as much as the CV itself — here's how to get it right.",
        primaryCta: { text: "Build my technical CV", href: APP },
        secondaryCta: { text: "Describe your projects", href: "/guides/how-to-write-projects-in-a-cv" },
      },
      {
        type: "cards",
        h2: "What recruiters look for on your GitHub",
        items: [
          {
            icon: "📌",
            title: "Pinned projects",
            text: "Pin your best 3–6 repositories so the strongest work is the first thing a visitor sees.",
          },
          {
            icon: "📖",
            title: "Clear READMEs",
            text: "Each project needs a README explaining what it does, the tech used, and how to run it. This is where you show communication skills.",
          },
          {
            icon: "🟩",
            title: "Real, steady activity",
            text: "A consistent commit history signals genuine, ongoing practice — more than one giant last-minute commit.",
          },
          {
            icon: "🔗",
            title: "A profile README",
            text: "A short profile README introducing who you are, what you study and what you're building ties it all together.",
          },
        ],
      },
      {
        type: "prose",
        h2: "Link GitHub from your CV — the right way",
        paragraphs: [
          "Add your GitHub URL to your CV's contact details, and link individual repositories from the relevant project bullets. But only link a profile you're happy for a recruiter to explore — tidy up or unpin half-finished work first.",
          "When you describe those projects on your CV, use the same achievement-focused style you'd use anywhere: what you built, the tech, and the result. Careero helps you write those bullets so your CV and GitHub reinforce each other.",
        ],
      },
      {
        type: "faq",
        items: [
          {
            q: "How many projects should be on my GitHub?",
            a: "Quality over quantity — three to six polished, well-documented projects beat dozens of empty repositories.",
          },
          {
            q: "Should I put my GitHub link on my CV?",
            a: "Yes, for technical roles. Add it to your contact details and link specific repos from your project bullets.",
          },
          {
            q: "How do I describe GitHub projects on my CV?",
            a: "Use achievement-focused bullets: what you built, the tech, and the outcome. See our guide on <a href=\"/guides/how-to-write-projects-in-a-cv\">describing student projects</a>.",
          },
        ],
      },
      closingCta(
        "Turn your GitHub into CV-ready proof",
        "Careero helps you describe your projects so your CV and GitHub tell one strong story.",
        "Build my technical CV",
      ),
    ],
  },

  // ------------------------------------------ BLOG: COVER LETTER ------------
  {
    slug: "blog/cover-letter-for-students",
    title: "How to Write a Cover Letter as a Student (Template + Tips) | Careero",
    description:
      "Write a cover letter that gets read: a simple structure for students, what to say in each paragraph, and mistakes to avoid — even with no work experience. Build your CV free with Careero.",
    h1: "How to write a cover letter as a student",
    type: "article",
    datePublished: PUB,
    dateModified: MOD,
    blocks: [
      {
        type: "hero",
        kicker: "Guide · 5 min read",
        h1: "How to write a cover letter as a student",
        lead:
          "A good cover letter doesn't repeat your CV — it connects you to one specific role. Here's a simple structure that works for students, even when you're light on experience.",
        primaryCta: { text: "Build my CV first", href: APP },
      },
      {
        type: "prose",
        h2: "The 4-paragraph structure",
        paragraphs: [
          "Keep it to one page and four short paragraphs. The goal is to show you understand the role, you're genuinely interested, and you have something relevant to offer.",
        ],
        bullets: [
          "<strong>Opening</strong> — the role you're applying for and a one-line hook on why you're excited about it.",
          "<strong>Why you</strong> — one or two relevant projects, modules or experiences, described by result.",
          "<strong>Why them</strong> — a specific reason you want to work for this organisation, not a generic one.",
          "<strong>Close</strong> — a confident sign-off and a thank you.",
        ],
      },
      {
        type: "prose",
        h2: "Writing it with little experience",
        paragraphs: [
          "As a student, lean on coursework, projects, volunteering and part-time roles. The key is to connect each example to what the job actually needs — if the role values teamwork, describe a group project and its outcome.",
          "Mirror the language of the job posting, and never send the same letter twice. A tailored letter beats a polished-but-generic one every time.",
        ],
      },
      {
        type: "faq",
        items: [
          {
            q: "How long should a student cover letter be?",
            a: "Half a page to one page — four short paragraphs. Recruiters skim, so make every line count.",
          },
          {
            q: "Do I need a cover letter if it's optional?",
            a: "If you can write a tailored one, yes — it's a chance to show interest and fit that a CV alone can't.",
          },
          {
            q: "Should my cover letter repeat my CV?",
            a: "No. Use it to connect a few relevant highlights to this specific role, not to list everything again.",
          },
        ],
      },
      closingCta(
        "Get your CV ready to match",
        "A great cover letter needs a great CV behind it. Build yours free with Careero.",
        "Build my CV first",
      ),
    ],
  },

  // ------------------------------------------ BLOG: CV MISTAKES -------------
  {
    slug: "blog/common-cv-mistakes-students",
    title: "10 Common Student CV Mistakes (and How to Fix Them) | Careero",
    description:
      "The most common student CV mistakes — from listing duties instead of achievements to typos and bad formatting — and exactly how to fix each one. Build a better CV free with Careero.",
    h1: "10 common student CV mistakes (and how to fix them)",
    type: "article",
    datePublished: PUB,
    dateModified: MOD,
    blocks: [
      {
        type: "hero",
        kicker: "Guide · 6 min read",
        h1: "10 common student CV mistakes (and how to fix them)",
        lead:
          "Most student CVs are rejected for the same handful of fixable reasons. Avoid these ten and you're already ahead of most applicants.",
        primaryCta: { text: "Fix my CV now", href: APP },
      },
      {
        type: "prose",
        h2: "The mistakes recruiters see most",
        bullets: [
          "<strong>Listing duties, not achievements.</strong> Fix: start with an action verb and add a result or number.",
          "<strong>A generic summary.</strong> Fix: name your field and what you're looking for.",
          "<strong>Too long.</strong> Fix: keep it to one focused page.",
          "<strong>Typos and inconsistency.</strong> Fix: proofread, and keep dates and tenses consistent.",
          "<strong>Fancy layouts that break the ATS.</strong> Fix: use a clean, single-column, <a href=\"/ats-friendly-student-cv\">ATS-friendly</a> template.",
          "<strong>Burying education.</strong> Fix: as a student, lead with it.",
          "<strong>Vague project descriptions.</strong> Fix: say what you built, the tools, and the outcome.",
          "<strong>Irrelevant detail.</strong> Fix: cut anything that doesn't support the role.",
          "<strong>No keywords from the job post.</strong> Fix: weave in the skills the employer asks for.",
          "<strong>Unprofessional contact details.</strong> Fix: use a clean email and add LinkedIn/GitHub.",
        ],
      },
      {
        type: "faq",
        items: [
          {
            q: "What's the single biggest CV mistake?",
            a: "Describing duties instead of achievements. Always show the result or skill, not just the task.",
          },
          {
            q: "How do I know if my CV is ATS-friendly?",
            a: "Use a simple single-column layout with standard headings. See our <a href=\"/ats-friendly-student-cv\">ATS-friendly CV guide</a>.",
          },
          {
            q: "Can Careero help me avoid these?",
            a: "Yes — it enforces clean structure and rewrites duties into achievement bullets automatically. <a href=\"" + APP + "\" rel=\"noopener\">Start free</a>.",
          },
        ],
      },
      closingCta(
        "Build a CV without the common mistakes",
        "Careero bakes these fixes in, so you avoid them by default.",
        "Fix my CV now",
      ),
    ],
  },

  // ------------------------------------------ BLOG: ATS KEYWORDS ------------
  {
    slug: "blog/cv-keywords-and-ats",
    title: "CV Keywords: How to Get Past the ATS (Student Guide) | Careero",
    description:
      "Learn how to use the right CV keywords to pass applicant tracking systems without keyword stuffing. A practical guide for students. Build an ATS-friendly CV free with Careero.",
    h1: "CV keywords: how to get past the ATS",
    type: "article",
    datePublished: PUB,
    dateModified: MOD,
    blocks: [
      {
        type: "hero",
        kicker: "Guide · 5 min read",
        h1: "CV keywords: how to get past the ATS",
        lead:
          "Before a human reads your CV, software scans it for relevant terms. Here's how to include the right keywords naturally — so you rank well without sounding like a robot.",
        primaryCta: { text: "Build an ATS-friendly CV", href: APP },
      },
      {
        type: "prose",
        h2: "Where keywords come from",
        paragraphs: [
          "The best keyword list is the job description itself. Read it closely and note the skills, tools and phrases the employer repeats — those are exactly what the applicant tracking system is told to look for.",
          "Then make sure those terms appear naturally in your CV: in your skills section, and — more powerfully — inside real project and experience bullets that prove you actually used them.",
        ],
      },
      {
        type: "prose",
        h2: "How to include keywords without stuffing",
        paragraphs: [
          "Keyword stuffing (repeating terms unnaturally) reads badly to humans and can be flagged. Instead, weave each keyword into a genuine achievement.",
        ],
        bullets: [
          "Weak: a long list of 30 skills with no context.",
          "Strong: &ldquo;Built a REST API in <strong>Python</strong> and <strong>FastAPI</strong>, tested with <strong>pytest</strong> — used by a 4-person project team.&rdquo;",
        ],
      },
      {
        type: "faq",
        items: [
          {
            q: "How many keywords should I use?",
            a: "Cover the core skills the job posting emphasises — quality and relevance matter more than quantity.",
          },
          {
            q: "Does the ATS read PDFs?",
            a: "Yes, if the PDF has real selectable text. Careero's PDF export keeps structured text so it parses correctly.",
          },
          {
            q: "How does Careero help with keywords?",
            a: "Its AI phrases your skills into natural, keyword-rich achievement bullets. <a href=\"/ats-friendly-student-cv\">See the ATS guide</a> or <a href=\"" + APP + "\" rel=\"noopener\">start free</a>.",
          },
        ],
      },
      closingCta(
        "Rank higher with the right keywords",
        "Careero helps you include the terms recruiters and ATS software look for — naturally.",
        "Build an ATS-friendly CV",
      ),
    ],
  },

  // ------------------------------------------ BLOG: INTERVIEW PREP ----------
  {
    slug: "blog/internship-interview-prep",
    title: "How to Prepare for an Internship Interview (Student Guide) | Careero",
    description:
      "A practical checklist for students preparing for an internship interview: research, common questions, the STAR method, and questions to ask. Build your CV free with Careero.",
    h1: "How to prepare for an internship interview",
    type: "article",
    datePublished: PUB,
    dateModified: MOD,
    blocks: [
      {
        type: "hero",
        kicker: "Guide · 6 min read",
        h1: "How to prepare for an internship interview",
        lead:
          "Internship interviews are about potential and attitude as much as knowledge. A little preparation goes a long way — here's a simple plan.",
        primaryCta: { text: "Get my CV interview-ready", href: APP },
      },
      {
        type: "steps",
        h2: "Your prep checklist",
        items: [
          {
            title: "Research the organisation",
            text: "Know what they do, a recent project or product, and why you want to work there specifically.",
          },
          {
            title: "Re-read your own CV",
            text: "Be ready to talk through every project and experience on it — interviewers ask about what you wrote.",
          },
          {
            title: "Prepare STAR examples",
            text: "For behavioural questions, structure answers as Situation, Task, Action, Result. Prepare two or three flexible stories.",
          },
          {
            title: "Prepare questions to ask",
            text: "Have two thoughtful questions ready — about the team, the work, or how success is measured.",
          },
        ],
      },
      {
        type: "prose",
        h2: "Common internship interview questions",
        bullets: [
          "&ldquo;Tell me about yourself&rdquo; — a 60-second summary of your studies, interests and why this role.",
          "&ldquo;Tell me about a project you're proud of&rdquo; — use a STAR example with a clear result.",
          "&ldquo;Why do you want this internship?&rdquo; — connect your goals to what they offer.",
          "&ldquo;Tell me about a time you worked in a team&rdquo; — pick a real group project or role.",
        ],
      },
      {
        type: "faq",
        items: [
          {
            q: "What is the STAR method?",
            a: "A way to structure answers: describe the Situation, the Task, the Action you took, and the Result. It keeps stories clear and focused.",
          },
          {
            q: "What should I ask at the end?",
            a: "Ask about the team, the day-to-day work, or how they measure success — it shows genuine interest.",
          },
          {
            q: "How does my CV help in the interview?",
            a: "Interviewers ask about what's on it, so a clear, honest CV sets up the conversation. Build yours with <a href=\"/cv-for-internship\">Careero's internship CV</a> guidance.",
          },
        ],
      },
      closingCta(
        "Walk in with a CV you can talk about",
        "Careero helps you write clear, honest highlights you'll be ready to discuss.",
        "Get my CV interview-ready",
      ),
    ],
  },

  // ============================================ PLAYBOOK LANDING PAGES ======

  // -------------------------------------------- NO EXPERIENCE (landing) -----
  {
    slug: "student-cv-with-no-experience",
    title: "Student CV With No Experience — Build One Free | Careero",
    description:
      "No work experience? Build a strong student CV with Careero using your projects, coursework, activities, skills, LinkedIn and GitHub. Free, ATS-friendly, PDF & DOCX download.",
    h1: "Build a student CV with no work experience",
    type: "website",
    blocks: [
      {
        type: "hero",
        kicker: "Student CV With No Experience",
        h1: "Build a student CV with no work experience",
        lead:
          "You don't need a job history to have a strong CV. Careero helps you build one from what you already have — projects, coursework, activities, skills, and your LinkedIn and GitHub.",
        primaryCta: { text: "Create My CV", href: APP },
        secondaryCta: { text: "Read the full guide", href: "/guides/student-cv-with-no-experience" },
        note: "Free to start · PDF & DOCX download",
      },
      {
        type: "cards",
        h2: "What to put on a CV when you have no experience",
        intro:
          "Careero guides you through each of these and turns them into strong, recruiter-ready content.",
        items: [
          { icon: "🧩", title: "Projects", text: "Coursework and personal projects are the strongest proof of what you can do. Careero rewrites them into achievement bullets.", href: "/guides/how-to-write-projects-in-a-cv" },
          { icon: "💼", title: "Internships (if any)", text: "Even short placements count. Describe them by results and the skills you used.", href: "/cv-for-internship" },
          { icon: "📚", title: "Coursework", text: "Relevant modules, strong grades and academic achievements lead a student CV.", href: "/guides/how-to-write-a-student-cv" },
          { icon: "🤝", title: "Activities", text: "Volunteering, societies and clubs show teamwork, initiative and leadership.", href: null },
          { icon: "🛠️", title: "Technical skills", text: "List the tools, languages and software relevant to the roles you want.", href: null },
          { icon: "🔗", title: "GitHub & LinkedIn", text: "Link your GitHub and LinkedIn so recruiters can see more of your work.", href: "/guides/linkedin-profile-for-students" },
        ],
      },
      {
        type: "prose",
        h2: "How Careero helps you fill the page — honestly",
        paragraphs: [
          "Careero never invents experience. It helps you <strong>recognise and describe</strong> what you already have: a class project becomes evidence of problem-solving; a part-time job becomes proof of reliability; a society role becomes leadership.",
          "The result is a clean, one-page, ATS-friendly CV built entirely from real things you've done — ready to download as PDF or DOCX.",
        ],
      },
      {
        type: "faq",
        items: [
          { q: "Can I really build a CV with zero work experience?", a: "Yes. Careero is designed for exactly this — it builds your CV from projects, coursework, activities, skills and your online profiles." },
          { q: "What's the most important section?", a: "Education and projects. Describe two or three projects by their results and the skills they show." },
          { q: "Is it free?", a: "Yes — start free at <a href=\"" + APP + "\" rel=\"noopener\">app.careero.app</a> and download as PDF or DOCX." },
        ],
      },
      closingCta(
        "You have more than enough for a great CV",
        "Let Careero help you find it and write it — no experience required to start.",
        "Create My CV",
      ),
    ],
  },

  // -------------------------------------------------- FEATURES --------------
  {
    slug: "features",
    title: "Features — What Careero Does for Student CVs | Careero",
    description:
      "Careero's features for student CVs: AI-guided writing, project and internship help, skills guidance, five templates, PDF and DOCX export, plus LinkedIn and GitHub guidance.",
    h1: "Everything Careero does for your student CV",
    type: "website",
    blocks: [
      {
        type: "hero",
        kicker: "Features",
        h1: "Everything Careero does for your student CV",
        lead:
          "Careero is an AI-powered CV builder for students and fresh graduates. Here's everything it helps you do — from a blank page to a polished, downloadable CV.",
        primaryCta: { text: "Create My CV", href: APP },
        secondaryCta: { text: "See templates", href: "/student-cv-templates" },
      },
      {
        type: "cards",
        h2: "Core features",
        items: [
          { icon: "🤖", title: "AI-guided student CV creation", text: "A guided wizard writes strong, quantified content with you — no blank page.", href: "/ai-cv-builder-for-students" },
          { icon: "🧩", title: "Project section improvement", text: "Turn coursework and side projects into achievement-focused bullets.", href: "/guides/how-to-write-projects-in-a-cv" },
          { icon: "💼", title: "Internship section support", text: "Describe internships and placements in results-focused language.", href: "/guides/how-to-add-internships-to-a-cv" },
          { icon: "🛠️", title: "Skills guidance", text: "Add the right technical and soft skills for the roles you want.", href: null },
          { icon: "🎨", title: "Multiple CV templates", text: "Five ATS-friendly designs: Classic, Modern, Minimal, Academic, Creative.", href: "/student-cv-templates" },
          { icon: "📄", title: "PDF export", text: "Download a pixel-perfect, ATS-safe PDF for applications.", href: "/download-cv-pdf" },
          { icon: "📝", title: "DOCX export", text: "Download an editable Word document when an employer asks for one.", href: "/download-cv-pdf#docx" },
          { icon: "🔗", title: "LinkedIn profile guidance", text: "Tips to build a LinkedIn profile that matches your CV.", href: "/guides/linkedin-profile-for-students" },
          { icon: "💻", title: "GitHub profile guidance", text: "Make your GitHub CV-ready for technical roles.", href: "/guides/github-profile-for-students" },
        ],
      },
      closingCta(
        "Try every feature free",
        "Careero is free to start — build your CV and download it in a few minutes.",
        "Create My CV",
      ),
    ],
  },

  // -------------------------------------------------- ABOUT -----------------
  {
    slug: "about",
    title: "About Careero — AI CV Builder for Students",
    description:
      "Careero is an AI-powered CV builder for students and fresh graduates, built to help them present their potential clearly, professionally and confidently.",
    h1: "About Careero",
    type: "website",
    blocks: [
      {
        type: "hero",
        kicker: "About",
        h1: "About Careero",
        lead:
          "Careero is built to help students present their potential clearly, professionally, and confidently.",
        primaryCta: { text: "Create My CV", href: APP },
      },
      {
        type: "prose",
        h2: "Why Careero exists",
        paragraphs: [
          "Careero is an AI-powered CV builder for students and fresh graduates. It helps students create professional CVs even when they have limited work experience by guiding them through education, projects, internships, skills, activities, LinkedIn, GitHub, and ready-to-download CV templates.",
          "Most CV tools assume you already have years of work history. Students don't — and that's not a weakness, it's just a different starting point. Careero is designed around the real student experience: coursework, academic and personal projects, internships, volunteering and early achievements, described the way recruiters expect to read them.",
          "Our goal is simple: help every student walk into their first application with a CV they're proud of.",
        ],
      },
      closingCta(
        "Build a CV you're proud of",
        "Start free and see how Careero turns your experience into a professional CV.",
        "Create My CV",
      ),
    ],
  },

  // -------------------------------------------------- FAQ -------------------
  {
    slug: "faq",
    title: "Careero FAQ — Student CV Builder Questions Answered",
    description:
      "Answers to common questions about Careero: who it's for, building a CV with no experience, PDF and DOCX download, templates, and help with projects, internships, LinkedIn and GitHub.",
    h1: "Frequently asked questions",
    type: "website",
    blocks: [
      {
        type: "hero",
        kicker: "FAQ",
        h1: "Frequently asked questions",
        lead:
          "Everything students ask about Careero, the AI CV builder for students and fresh graduates.",
        primaryCta: { text: "Create My CV", href: APP },
      },
      {
        type: "faq",
        h2: "Careero FAQ",
        items: [
          { q: "What is Careero?", a: "Careero is an AI-powered CV builder for students and fresh graduates. It helps you create a professional CV even with limited work experience by guiding you through education, projects, internships, skills, activities, LinkedIn, GitHub, and ready-to-download CV templates." },
          { q: "Is Careero for students?", a: "Yes. Careero is built specifically for students, fresh graduates and internship applicants — not senior professionals with years of work history." },
          { q: "Can I create a CV with no work experience?", a: "Yes. Careero helps you build a strong CV from projects, coursework, activities, skills and your online profiles. See our <a href=\"/student-cv-with-no-experience\">no-experience page</a>." },
          { q: "Can I download my CV as PDF?", a: "Yes. Every CV can be exported as a clean, ATS-friendly PDF." },
          { q: "Can I download my CV as DOCX?", a: "Yes. You can also export an editable Word (DOCX) document whenever you need one." },
          { q: "What CV templates are available?", a: "Five ATS-friendly templates: Classic, Modern, Minimal, Academic and Creative. See <a href=\"/student-cv-templates\">student CV templates</a>." },
          { q: "Does Careero help with projects?", a: "Yes. Careero turns coursework and personal projects into achievement-focused bullet points. See <a href=\"/guides/how-to-write-projects-in-a-cv\">writing projects in a CV</a>." },
          { q: "Does Careero help with internships?", a: "Yes. It helps you describe internships and placements in strong, results-focused language. See <a href=\"/cv-for-internship\">CV for internship</a>." },
          { q: "Does Careero help with LinkedIn?", a: "Yes — we provide guidance on building a LinkedIn profile that matches your CV. See <a href=\"/guides/linkedin-profile-for-students\">LinkedIn for students</a>." },
          { q: "Does Careero help with GitHub?", a: "Yes — we help you make your GitHub profile CV-ready for technical roles. See <a href=\"/guides/github-profile-for-students\">GitHub for students</a>." },
        ],
      },
      closingCta(
        "Still have questions? Just start building",
        "Careero is free to try — the fastest way to see how it works is to build your CV.",
        "Create My CV",
      ),
    ],
  },

  // ============================================ GUIDES (new) ================

  // -------------------------------------------- GUIDE: WRITE STUDENT CV -----
  {
    slug: "guides/how-to-write-a-student-cv",
    title: "How to Write a Student CV: A Simple Guide for University Students | Careero",
    description:
      "A simple, step-by-step guide to writing a student CV: what to include, how to order sections, and how to describe projects and experience. Build yours free with Careero.",
    h1: "How to write a student CV: a simple guide for university students",
    type: "article",
    datePublished: PUB,
    dateModified: MOD,
    blocks: [
      {
        type: "hero",
        kicker: "Guide · 6 min read",
        h1: "How to write a student CV: a simple guide for university students",
        lead:
          "A clear, no-jargon walkthrough of writing a student CV that recruiters actually read — what to include, how to order it, and how to make limited experience look strong.",
        primaryCta: { text: "Create My CV", href: APP },
      },
      {
        type: "prose",
        h2: "The sections of a student CV",
        paragraphs: [
          "A strong student CV fits on one page and leads with education. Around it, you add the experiences that show skills — even if they didn't come from a formal job.",
        ],
        bullets: [
          "<strong>Contact details</strong> — name, professional email, phone, city, LinkedIn and GitHub.",
          "<strong>Personal summary</strong> — two or three lines on who you are and what you want.",
          "<strong>Education</strong> — degree, expected grade, relevant modules and achievements.",
          "<strong>Projects</strong> — coursework and personal projects, described by outcome.",
          "<strong>Experience</strong> — part-time work, internships, volunteering and societies.",
          "<strong>Skills</strong> — tools, technologies and languages relevant to the role.",
        ],
      },
      {
        type: "steps",
        h2: "Write it step by step",
        items: [
          { title: "Lead with education", text: "As a student, your degree is your headline. Add modules, grades and academic achievements." },
          { title: "Turn tasks into achievements", text: "Start each bullet with an action verb and add a result or number where you can." },
          { title: "Tailor to each application", text: "Mirror the language of the job description so the CV matches the role." },
          { title: "Keep it to one clean page", text: "Use a simple, ATS-friendly template and proofread carefully." },
        ],
      },
      {
        type: "prose",
        h2: "Common mistakes to avoid",
        bullets: [
          "Listing duties instead of achievements.",
          "A generic summary that could belong to anyone.",
          "Fancy layouts that confuse applicant tracking systems.",
          "Typos and inconsistent formatting.",
        ],
      },
      {
        type: "faq",
        items: [
          { q: "How long should a student CV be?", a: "One page. Keep it focused and remove anything that isn't relevant." },
          { q: "What if I have no experience?", a: "Lead with education and projects. See our <a href=\"/guides/student-cv-with-no-experience\">no-experience guide</a>." },
          { q: "Can Careero write it for me?", a: "Careero drafts your summary and rewrites your notes into strong bullets — you stay in control. <a href=\"" + APP + "\" rel=\"noopener\">Start free</a>." },
        ],
      },
      closingCta(
        "Turn this guide into a finished CV",
        "Careero applies all of these best practices automatically as you build.",
        "Create My CV",
      ),
    ],
  },

  // -------------------------------------------- GUIDE: INTERNSHIPS ----------
  {
    slug: "guides/how-to-add-internships-to-a-cv",
    title: "How to Add Internships to a Student CV (With Examples) | Careero",
    description:
      "Learn how to add internships to your student CV: what to include, how to describe your work by results, and where to place them. Build your CV free with Careero.",
    h1: "How to add internships to a student CV",
    type: "article",
    datePublished: PUB,
    dateModified: MOD,
    blocks: [
      {
        type: "hero",
        kicker: "Guide · 5 min read",
        h1: "How to add internships to a student CV",
        lead:
          "An internship is one of the strongest things on a student CV — if you describe it well. Here's how to present it by impact, not just job title.",
        primaryCta: { text: "Create My CV", href: APP },
      },
      {
        type: "prose",
        h2: "What to include for each internship",
        bullets: [
          "<strong>Role and organisation</strong> — your title and where you interned.",
          "<strong>Dates</strong> — month and year, even for short placements.",
          "<strong>2–4 achievement bullets</strong> — what you did and the result, not a task list.",
          "<strong>Tools and skills</strong> — the technologies or methods you used.",
        ],
      },
      {
        type: "prose",
        h2: "Describe internships by result",
        paragraphs: [
          "Use the formula <strong>action + what + result</strong>. A number makes it stronger.",
        ],
        subsections: [
          {
            h3: "Before and after",
            bullets: [
              "Before: &ldquo;Helped the marketing team.&rdquo;",
              "After: &ldquo;Scheduled 30+ social posts and drafted 5 newsletter emails, contributing to a 12% rise in open rate over 8 weeks.&rdquo;",
            ],
          },
        ],
      },
      {
        type: "prose",
        h2: "Where to place internships",
        paragraphs: [
          "If the internship is directly relevant to the role you're applying for, place it near the top under an Experience section. If it's less relevant, keep it but let stronger projects lead. Careero helps you order and describe everything automatically.",
        ],
      },
      {
        type: "faq",
        items: [
          { q: "Should I include a very short internship?", a: "Yes, if it's relevant — even a two-week placement shows initiative and real-world exposure." },
          { q: "How many bullets per internship?", a: "Two to four strong, result-focused bullets is ideal." },
          { q: "No internships yet?", a: "That's fine — lead with projects and coursework. See <a href=\"/guides/student-cv-with-no-experience\">CV with no experience</a>." },
        ],
      },
      closingCta(
        "Make your internship stand out",
        "Careero rewrites your internship into strong, quantified bullet points.",
        "Create My CV",
      ),
    ],
  },

  // -------------------------------------------- GUIDE: BEST FORMAT ----------
  {
    slug: "guides/best-cv-format-for-students",
    title: "Best CV Format for Students and Fresh Graduates | Careero",
    description:
      "The best CV format for students and fresh graduates: which layout to use, section order, length, and why ATS-friendly formatting matters. Build yours free with Careero.",
    h1: "The best CV format for students and fresh graduates",
    type: "article",
    datePublished: PUB,
    dateModified: MOD,
    blocks: [
      {
        type: "hero",
        kicker: "Guide · 5 min read",
        h1: "The best CV format for students and fresh graduates",
        lead:
          "The right format makes limited experience look strong and keeps your CV readable by both recruiters and screening software. Here's what works for students.",
        primaryCta: { text: "Create My CV", href: APP },
      },
      {
        type: "prose",
        h2: "Use a reverse-chronological, single-column layout",
        paragraphs: [
          "For students, a clean <strong>reverse-chronological</strong> layout in a <strong>single column</strong> is best. It's what recruiters expect and what applicant tracking systems parse most reliably. Avoid multi-column designs, text boxes and graphics that hold key information.",
        ],
      },
      {
        type: "prose",
        h2: "The recommended section order",
        bullets: [
          "Contact details",
          "Short personal summary",
          "Education (your headline as a student)",
          "Projects",
          "Experience — internships, part-time work, volunteering",
          "Skills",
        ],
      },
      {
        type: "prose",
        h2: "Length, fonts and file type",
        paragraphs: [
          "Keep it to <strong>one page</strong>. Use one clean, standard font and consistent spacing. Export a structured PDF for most applications, or a DOCX when an employer asks for Word — both of Careero's exports stay <a href=\"/ats-friendly-student-cv\">ATS-friendly</a>.",
        ],
      },
      {
        type: "faq",
        items: [
          { q: "Should a student CV be one or two pages?", a: "One page. A focused one-pager reads far better than a padded two-pager." },
          { q: "Is a creative CV format okay?", a: "For most students, a clean format is safest. Careero's Creative template adds personality while staying recruiter- and ATS-safe." },
          { q: "PDF or DOCX?", a: "PDF for most applications; DOCX when Word is requested. Careero exports both." },
        ],
      },
      closingCta(
        "Get the format right automatically",
        "Careero's templates handle formatting so you can focus on content.",
        "Create My CV",
      ),
    ],
  },

  // ============================================ COMPARISONS =================

  // -------------------------------------------- vs CANVA -------------------
  {
    slug: "alternatives/canva-cv-builder-for-students",
    title: "Careero vs Canva for Student CVs — Which Is Better? | Careero",
    description:
      "Canva is great for flexible design; Careero is a guided AI CV builder for students. Compare the two for building a first professional student CV, and choose what fits you.",
    h1: "Careero vs Canva for student CVs",
    type: "website",
    blocks: [
      {
        type: "hero",
        kicker: "Compare",
        h1: "Careero vs Canva for student CVs",
        lead:
          "Both can produce a good-looking CV. The difference is guidance: Canva gives you a blank canvas, while Careero walks students through what to write and how to phrase it.",
        primaryCta: { text: "Create My CV", href: APP },
      },
      {
        type: "prose",
        h2: "What Canva is good at",
        paragraphs: [
          "Canva is a flexible, general-purpose design tool with a huge range of templates. If you enjoy design and want full control over layout, colours and typography, it's excellent — and it's used for far more than CVs.",
        ],
      },
      {
        type: "cards",
        h2: "Best for",
        items: [
          { icon: "🎨", title: "Canva is best for", text: "People who want maximum design flexibility and are comfortable writing and structuring their CV content themselves." },
          { icon: "🎓", title: "Careero is best for", text: "Students and fresh graduates who want guidance on what to write — especially projects, internships and skills — with ATS-friendly output." },
        ],
      },
      {
        type: "prose",
        h2: "Why Careero is different for students",
        paragraphs: [
          "With Canva, the hard part isn't the design — it's knowing <strong>what to say</strong> when you don't have much experience. Careero focuses there: it guides you section by section, uses AI to turn rough notes into strong bullet points, keeps the layout ATS-friendly, and exports to PDF and DOCX.",
          "If you want a beautiful blank canvas, Canva is great. If you want help building a professional first CV as a student, that's what Careero is for.",
        ],
      },
      closingCta(
        "Want guidance, not a blank canvas?",
        "Careero helps students write the CV, not just design it.",
        "Create My CV",
      ),
    ],
  },

  // -------------------------------------------- vs RESUME.IO ---------------
  {
    slug: "alternatives/resume-io-for-students",
    title: "Careero vs Resume.io for Students — A Fair Comparison | Careero",
    description:
      "Resume.io is a polished general CV builder; Careero focuses specifically on students, projects, internships and early-career profiles. Compare them and pick the right fit.",
    h1: "Careero vs Resume.io for students",
    type: "website",
    blocks: [
      {
        type: "hero",
        kicker: "Compare",
        h1: "Careero vs Resume.io for students",
        lead:
          "Resume.io is a capable, general-purpose CV builder. Careero is purpose-built for students — the difference shows up in how each one handles limited experience.",
        primaryCta: { text: "Create My CV", href: APP },
      },
      {
        type: "prose",
        h2: "What Resume.io is good at",
        paragraphs: [
          "Resume.io is a polished, widely-used resume builder with clean templates and a smooth editor. It works well for people across many career stages who already know what they want to say.",
        ],
      },
      {
        type: "cards",
        h2: "Best for",
        items: [
          { icon: "🧰", title: "Resume.io is best for", text: "General job seekers who want a professional, all-purpose resume builder and are comfortable writing their own content." },
          { icon: "🎓", title: "Careero is best for", text: "Students, fresh graduates and interns who want guidance tailored to early-career CVs — projects, coursework, internships and skills." },
        ],
      },
      {
        type: "prose",
        h2: "Why Careero is different for students",
        paragraphs: [
          "General builders assume you have work history to list. Careero assumes you might not — and helps you present education, projects, activities, LinkedIn and GitHub instead. Its AI is tuned for early-career phrasing, and every template stays ATS-friendly with PDF and DOCX export.",
          "If you're mid-career, a general builder is a fine choice. If you're a student writing your first professional CV, Careero is built for exactly that.",
        ],
      },
      closingCta(
        "Building your first CV as a student?",
        "Careero guides the whole early-career CV journey.",
        "Create My CV",
      ),
    ],
  },

  // -------------------------------------------- vs GENERIC AI --------------
  {
    slug: "alternatives/generic-ai-resume-builders",
    title: "Careero vs Generic AI Resume Builders (for Students) | Careero",
    description:
      "Generic AI tools can write resume text; Careero guides the full student CV journey — structure, projects, internships, templates and ATS-friendly PDF and DOCX export.",
    h1: "Careero vs generic AI resume builders",
    type: "website",
    blocks: [
      {
        type: "hero",
        kicker: "Compare",
        h1: "Careero vs generic AI resume builders",
        lead:
          "A generic AI tool can generate resume text. But a student CV needs more than text — it needs the right structure, the right sections, and output that actually reaches recruiters.",
        primaryCta: { text: "Create My CV", href: APP },
      },
      {
        type: "prose",
        h2: "What generic AI tools are good at",
        paragraphs: [
          "General AI writing tools are great at producing text on demand. If you already know your CV's structure and just want help wording a bullet point, they can help with that one step.",
        ],
      },
      {
        type: "cards",
        h2: "Best for",
        items: [
          { icon: "✍️", title: "Generic AI tools are best for", text: "One-off text generation when you already know exactly what your CV should contain and how it should be laid out." },
          { icon: "🎓", title: "Careero is best for", text: "Students who want the whole journey guided — what sections to include, how to describe projects and internships, which template to use, and how to export." },
        ],
      },
      {
        type: "prose",
        h2: "Why Careero is different for students",
        paragraphs: [
          "Raw AI text isn't a CV. Careero combines AI writing with a guided, student-specific structure: it prompts you for the right information, keeps everything ATS-friendly, applies a professional template, and gives you a finished PDF or DOCX — not just a paragraph to paste somewhere.",
          "Use a generic tool if you only need a sentence rewritten. Use Careero if you want to build the whole CV.",
        ],
      },
      closingCta(
        "Want the whole CV, not just the text?",
        "Careero guides students from a blank page to a finished, downloadable CV.",
        "Create My CV",
      ),
    ],
  },

  // --------------------------------------------- CV FOR CS STUDENTS ----
  {
    slug: "cv-for-computer-science-students",
    title: "Computer Science Student CV: Guide & Examples (2026) | Careero",
    description:
      "How to write a computer science student CV that lands internships and graduate roles — projects, tech skills, GitHub and ATS tips. Build yours free with Careero.",
    h1: "How to write a computer science student CV",
    type: "website",
    blocks: [
      {
        type: "hero",
        kicker: "CV by Field · Computer Science",
        h1: "The computer science student CV that gets you interviews",
        lead:
          "Recruiters for tech roles scan for projects, a public GitHub and the right stack — not a long work history. Here's how to build a computer science CV that shows what you can actually do, even as a student.",
        primaryCta: { text: "Build my CS CV", href: APP },
        secondaryCta: { text: "See CV examples", href: "/student-cv-examples" },
        note: "Free to start · ATS-friendly · PDF &amp; DOCX",
      },
      {
        type: "cards",
        h2: "What matters most on a computer science CV",
        items: [
          {
            icon: "🧩",
            title: "Projects over jobs",
            text: "Coursework and side projects are your strongest evidence. Describe each by problem, stack and outcome.",
            href: "/guides/how-to-write-projects-in-a-cv",
          },
          {
            icon: "🐙",
            title: "A linked GitHub",
            text: "A tidy GitHub with pinned repos and READMEs turns claims into proof. Link it near your contact details.",
            href: "/guides/github-profile-for-students",
          },
          {
            icon: "🛠️",
            title: "A focused skills section",
            text: "List languages, frameworks and tools you can actually discuss — grouped, not a 40-item word cloud.",
          },
          {
            icon: "✅",
            title: "ATS-safe formatting",
            text: "Tech employers lean heavily on screening software. Keep headings standard and layout clean.",
            href: "/ats-friendly-student-cv",
          },
        ],
      },
      {
        type: "prose",
        h2: "How to describe a coding project",
        paragraphs: [
          "The best computer science bullets read like mini case studies: what you built, the stack you used, and the measurable result. Lead with an action verb and include a number wherever you honestly can.",
        ],
        subsections: [
          {
            h3: "Weak vs strong",
            paragraphs: [
              "&ldquo;Made a website for a project&rdquo; tells a recruiter nothing. &ldquo;Built a full-stack expense tracker in React and Node.js used by 30 classmates; added auth and charts&rdquo; shows scope, stack and impact in one line.",
            ],
          },
          {
            h3: "No internship yet? No problem",
            paragraphs: [
              "Hackathons, open-source contributions, university society tech teams and personal apps all count as experience. See our guide on <a href=\"/student-cv-with-no-experience\">writing a CV with no experience</a>.",
            ],
          },
        ],
      },
      {
        type: "faq",
        items: [
          {
            q: "How many projects should a CS student CV have?",
            a: "Two to four strong projects beat a long list. Choose the ones with the clearest outcome and the stack most relevant to the role.",
          },
          {
            q: "Should I list every programming language I've touched?",
            a: "No. List the ones you can talk about confidently in an interview, and group them (languages, frameworks, tools) so screening software and humans can scan them quickly.",
          },
          {
            q: "Do I need a GitHub link on my CV?",
            a: "For technical roles, yes — a clean GitHub is strong proof. See our <a href=\"/guides/github-profile-for-students\">GitHub for students guide</a>.",
          },
        ],
      },
      {
        type: "prose",
        h2: "Tailor your computer science CV to a goal",
        bullets: [
          "<a href=\"/cv-for-computer-science-students/internship\">CV for an internship</a>",
          "<a href=\"/cv-for-computer-science-students/scholarship\">CV for a scholarship</a>",
          "<a href=\"/cv-for-computer-science-students/part-time-job\">CV for a part-time job</a>",
          "<a href=\"/cv-for-computer-science-students/first-job\">CV for your first job</a>",
          "<a href=\"/cv-for-computer-science-students/graduate-scheme\">CV for a graduate scheme</a>",
        ],
      },
      {
        type: "prose",
        h2: "More CV guides",
        bullets: [
          "<a href=\"/cv-for-engineering-students\">CV for engineering students</a>",
          "<a href=\"/cv-for-internship\">CV for an internship</a>",
          "<a href=\"/ai-cv-builder-for-students\">AI CV builder for students</a>",
        ],
      },
      closingCta(
        "Build your computer science CV",
        "Add your projects and let Careero write recruiter-ready, ATS-friendly bullets.",
        "Build my CS CV",
      ),
    ],
  },

  // -------------------------------------- CV FOR ENGINEERING STUDENTS ----
  {
    slug: "cv-for-engineering-students",
    title: "Engineering Student CV: Guide & Examples (2026) | Careero",
    description:
      "Write an engineering student CV that wins internships and graduate schemes — technical projects, lab work, tools and ATS tips. Build yours free with Careero.",
    h1: "How to write an engineering student CV",
    type: "website",
    blocks: [
      {
        type: "hero",
        kicker: "CV by Field · Engineering",
        h1: "An engineering CV built around what you've made and measured",
        lead:
          "Engineering recruiters look for hands-on projects, technical tools and evidence you can solve real problems. Here's how to present your degree, labs and projects so a student CV reads like an engineer's.",
        primaryCta: { text: "Build my engineering CV", href: APP },
        secondaryCta: { text: "See CV examples", href: "/student-cv-examples" },
        note: "Free to start · ATS-friendly · PDF &amp; DOCX",
      },
      {
        type: "cards",
        h2: "What engineering recruiters want to see",
        items: [
          {
            icon: "📐",
            title: "Technical projects",
            text: "Design projects, final-year projects and competitions — described by objective, method and result.",
            href: "/guides/how-to-write-projects-in-a-cv",
          },
          {
            icon: "🧰",
            title: "Tools & software",
            text: "CAD, MATLAB, SolidWorks, simulation and lab equipment you've genuinely used belong in a clear skills block.",
          },
          {
            icon: "🏭",
            title: "Placements & labs",
            text: "Industrial placements, lab modules and workshops all count as practical experience worth describing.",
            href: "/cv-for-internship",
          },
          {
            icon: "✅",
            title: "Clean, ATS-safe layout",
            text: "Large engineering employers screen at scale. Keep formatting simple so nothing gets dropped.",
            href: "/ats-friendly-student-cv",
          },
        ],
      },
      {
        type: "prose",
        h2: "Turn a design project into strong bullets",
        paragraphs: [
          "Quantify wherever you can: loads, tolerances, cost savings, efficiency gains, team size. Numbers signal an engineer's mindset. &ldquo;Designed and tested a load-bearing bracket that cut mass 18% while meeting the safety factor&rdquo; is far stronger than &ldquo;did a design project.&rdquo;",
        ],
      },
      {
        type: "faq",
        items: [
          {
            q: "Should I include my final-year project?",
            a: "Yes — it's often the most substantial engineering work you've done. Describe the objective, your method, the tools, and the outcome.",
          },
          {
            q: "How do I show experience without a placement?",
            a: "Lab modules, design competitions, society projects and part-time work all demonstrate skills. See our guide on <a href=\"/student-cv-with-no-experience\">CVs with no experience</a>.",
          },
          {
            q: "How long should an engineering student CV be?",
            a: "One page while you're a student. Prioritise your degree, strongest projects and relevant tools.",
          },
        ],
      },
      {
        type: "prose",
        h2: "Tailor your engineering CV to a goal",
        bullets: [
          "<a href=\"/cv-for-engineering-students/internship\">CV for an internship</a>",
          "<a href=\"/cv-for-engineering-students/scholarship\">CV for a scholarship</a>",
          "<a href=\"/cv-for-engineering-students/part-time-job\">CV for a part-time job</a>",
          "<a href=\"/cv-for-engineering-students/first-job\">CV for your first job</a>",
          "<a href=\"/cv-for-engineering-students/graduate-scheme\">CV for a graduate scheme</a>",
        ],
      },
      {
        type: "prose",
        h2: "More CV guides",
        bullets: [
          "<a href=\"/cv-for-computer-science-students\">CV for computer science students</a>",
          "<a href=\"/guides/best-cv-format-for-students\">Best CV format for students</a>",
          "<a href=\"/cv-for-internship\">CV for an internship</a>",
        ],
      },
      closingCta(
        "Build your engineering CV",
        "Add your projects and tools and let Careero write quantified, ATS-friendly bullets.",
        "Build my engineering CV",
      ),
    ],
  },

  // ---------------------------------------- CV FOR BUSINESS STUDENTS ----
  {
    slug: "cv-for-business-students",
    title: "Business Student CV: Guide & Examples (2026) | Careero",
    description:
      "Write a business, finance or management student CV that stands out — internships, societies, leadership and results. Build yours free with Careero.",
    h1: "How to write a business student CV",
    type: "website",
    blocks: [
      {
        type: "hero",
        kicker: "CV by Field · Business & Finance",
        h1: "A business CV that leads with results, not just responsibilities",
        lead:
          "For business, finance and management roles, recruiters want commercial awareness, leadership and measurable impact. Here's how to turn societies, part-time work and coursework into a CV that competes for competitive schemes.",
        primaryCta: { text: "Build my business CV", href: APP },
        secondaryCta: { text: "See CV examples", href: "/student-cv-examples" },
        note: "Free to start · ATS-friendly · PDF &amp; DOCX",
      },
      {
        type: "cards",
        h2: "What sets a strong business CV apart",
        items: [
          {
            icon: "📈",
            title: "Quantified results",
            text: "Revenue raised, budgets managed, members recruited, hours saved — numbers make a business CV credible.",
          },
          {
            icon: "👥",
            title: "Leadership & teamwork",
            text: "Society committees, group projects and part-time supervision show the soft skills employers screen for.",
          },
          {
            icon: "🧠",
            title: "Commercial awareness",
            text: "Tie coursework and projects to real business outcomes to show you think beyond the classroom.",
          },
          {
            icon: "✅",
            title: "Polished & ATS-safe",
            text: "Consultancies and banks use heavy screening. Keep it clean, consistent and error-free.",
            href: "/ats-friendly-student-cv",
          },
        ],
      },
      {
        type: "prose",
        h2: "Make everyday experience sound commercial",
        paragraphs: [
          "A part-time retail job becomes &ldquo;Handled 100+ customer transactions per shift and resolved complaints, improving repeat custom.&rdquo; A society treasurer role becomes &ldquo;Managed a £4k budget and cut event costs 15%.&rdquo; The activity matters less than the result you describe.",
        ],
      },
      {
        type: "faq",
        items: [
          {
            q: "I only have part-time and society experience — is that enough?",
            a: "Yes. Described well, part-time work and society roles show exactly the leadership, numeracy and teamwork employers want. Our <a href=\"/student-cv-with-no-experience\">no-experience guide</a> shows how.",
          },
          {
            q: "Should I include my A-level or high-school grades?",
            a: "Include them briefly early in your degree, especially for finance schemes that ask for them, then reduce the detail as your degree and experience grow.",
          },
          {
            q: "How do I stand out for competitive schemes?",
            a: "Quantify everything, tailor the CV to each firm, and keep it to one clean page. Careero helps you do all three.",
          },
        ],
      },
      {
        type: "prose",
        h2: "Tailor your business CV to a goal",
        bullets: [
          "<a href=\"/cv-for-business-students/internship\">CV for an internship</a>",
          "<a href=\"/cv-for-business-students/scholarship\">CV for a scholarship</a>",
          "<a href=\"/cv-for-business-students/part-time-job\">CV for a part-time job</a>",
          "<a href=\"/cv-for-business-students/first-job\">CV for your first job</a>",
          "<a href=\"/cv-for-business-students/graduate-scheme\">CV for a graduate scheme</a>",
        ],
      },
      {
        type: "prose",
        h2: "More CV guides",
        bullets: [
          "<a href=\"/cv-for-internship\">CV for an internship</a>",
          "<a href=\"/cv-for-part-time-job-students\">CV for a part-time job</a>",
          "<a href=\"/guides/how-to-write-a-student-cv\">How to write a student CV</a>",
        ],
      },
      closingCta(
        "Build your business CV",
        "Turn societies, part-time work and coursework into results-focused, ATS-friendly bullets.",
        "Build my business CV",
      ),
    ],
  },

  // ------------------------------------ CV FOR SCHOLARSHIP APPLICATION ----
  {
    slug: "cv-for-scholarship-application",
    title: "CV for a Scholarship Application: Guide & Tips (2026) | Careero",
    description:
      "How to write a CV for a scholarship application — lead with academics, achievements, leadership and impact. Build a polished scholarship CV free with Careero.",
    h1: "How to write a CV for a scholarship application",
    type: "website",
    blocks: [
      {
        type: "hero",
        kicker: "CV by Goal · Scholarships",
        h1: "A scholarship CV that puts your achievements first",
        lead:
          "A scholarship CV isn't a job CV. Committees reward academic excellence, leadership, community impact and potential. Here's how to structure and write one that makes a strong case for funding.",
        primaryCta: { text: "Build my scholarship CV", href: APP },
        secondaryCta: { text: "How to write a student CV", href: "/guides/how-to-write-a-student-cv" },
        note: "Free to start · PDF &amp; DOCX",
      },
      {
        type: "prose",
        h2: "What a scholarship CV should include",
        paragraphs: [
          "Lead with academics — they are the core of the decision. Then show the well-rounded profile committees look for: leadership, service, and evidence you'll make good use of the opportunity.",
        ],
        bullets: [
          "<strong>Academic record</strong> — degree, grades, awards, scholarships and honours.",
          "<strong>Achievements</strong> — competitions, publications, presentations and prizes.",
          "<strong>Leadership</strong> — society roles, mentoring, captaincy and organising.",
          "<strong>Community & volunteering</strong> — service that shows values and initiative.",
          "<strong>Goals</strong> — a short statement of what the scholarship will help you achieve.",
        ],
      },
      {
        type: "prose",
        h2: "How it differs from a job CV",
        paragraphs: [
          "Where a job CV foregrounds work experience and role-specific skills, a scholarship CV foregrounds merit, character and potential. It's usually acceptable for it to run slightly longer if you have genuine achievements to list — but keep every line relevant and evidenced.",
        ],
      },
      {
        type: "faq",
        items: [
          {
            q: "How long should a scholarship CV be?",
            a: "One page is ideal; up to two is acceptable if you have substantial academic achievements, publications or leadership to evidence.",
          },
          {
            q: "Should I include a personal statement on the CV?",
            a: "A short profile or goals line helps, but keep any long personal statement as a separate document if the scholarship asks for one.",
          },
          {
            q: "What if my grades aren't perfect?",
            a: "Lead with your strengths — relevant achievements, leadership and impact — and let a strong, well-organised CV tell a fuller story than grades alone.",
          },
        ],
      },
      {
        type: "prose",
        h2: "More CV guides",
        bullets: [
          "<a href=\"/guides/how-to-write-a-student-cv\">How to write a student CV</a>",
          "<a href=\"/student-cv-with-no-experience\">CV with no experience</a>",
          "<a href=\"/student-cv-templates\">Student CV templates</a>",
        ],
      },
      closingCta(
        "Build your scholarship CV",
        "Careero helps you present your academics, achievements and leadership with clarity.",
        "Build my scholarship CV",
      ),
    ],
  },

  // ------------------------------------ CV FOR PART-TIME JOB STUDENTS ----
  {
    slug: "cv-for-part-time-job-students",
    title: "CV for a Part-Time Job (Student Guide, 2026) | Careero",
    description:
      "Write a student CV for a part-time job even with no experience — highlight availability, reliability and transferable skills. Build yours free with Careero.",
    h1: "How to write a CV for a part-time job",
    type: "website",
    blocks: [
      {
        type: "hero",
        kicker: "CV by Goal · Part-Time Work",
        h1: "A part-time job CV that gets you hired with little or no experience",
        lead:
          "Applying for retail, hospitality, tutoring or campus work? Employers care about reliability, attitude and availability far more than a long CV. Here's how to write a short, convincing one — even for your first job.",
        primaryCta: { text: "Build my CV free", href: APP },
        secondaryCta: { text: "CV with no experience", href: "/student-cv-with-no-experience" },
        note: "Free to start · Ready in minutes",
      },
      {
        type: "cards",
        h2: "What part-time employers actually look for",
        items: [
          {
            icon: "⏰",
            title: "Availability",
            text: "State when you can work — evenings, weekends, term-time or holidays. It's often the deciding factor.",
          },
          {
            icon: "🤝",
            title: "Reliability & attitude",
            text: "Punctuality, teamwork and a willingness to learn matter more than a polished career history.",
          },
          {
            icon: "🔁",
            title: "Transferable skills",
            text: "School, volunteering, clubs and coursework all show communication, responsibility and time management.",
          },
          {
            icon: "📄",
            title: "Short & clean",
            text: "Half a page to one page is plenty. Keep it easy to skim for a busy shift manager.",
          },
        ],
      },
      {
        type: "prose",
        h2: "No work experience yet? Start here",
        paragraphs: [
          "Everyone's first CV has no jobs on it — that's normal. Lead with a friendly one-line summary, your availability, your education, and a short list of transferable skills backed by examples from school, clubs or volunteering.",
          "For a full walkthrough, read our guide on <a href=\"/student-cv-with-no-experience\">writing a CV with no experience</a>.",
        ],
      },
      {
        type: "faq",
        items: [
          {
            q: "How long should a part-time job CV be?",
            a: "Half a page to one page. Managers scan quickly, so keep it short, clear and focused on availability and attitude.",
          },
          {
            q: "What do I put if I've never had a job?",
            a: "Your education, a short summary, availability, and transferable skills from school, volunteering and activities — with a quick example for each.",
          },
          {
            q: "Should I write a cover letter too?",
            a: "A few lines help for competitive roles. See our <a href=\"/blog/cover-letter-for-students\">student cover letter guide</a>.",
          },
        ],
      },
      {
        type: "prose",
        h2: "More CV guides",
        bullets: [
          "<a href=\"/student-cv-with-no-experience\">CV with no experience</a>",
          "<a href=\"/first-cv\">Your first CV</a>",
          "<a href=\"/cv-for-business-students\">CV for business students</a>",
        ],
      },
      closingCta(
        "Build your part-time job CV",
        "Answer a few guided questions and download a clean, ready-to-send CV in minutes.",
        "Build my CV free",
      ),
    ],
  },

  // ---------------------------------------- ALTERNATIVE · CAREERO vs ZETY ----
  {
    slug: "alternatives/zety-for-students",
    title: "Careero vs Zety: Best CV Builder for Students (2026) | Careero",
    description:
      "Comparing Zety and Careero for students? See how a student-first, AI CV builder with free PDF and DOCX download compares for first-time CV writers.",
    h1: "Careero vs Zety for students",
    type: "website",
    blocks: [
      {
        type: "hero",
        kicker: "Compare · Careero vs Zety",
        h1: "Careero vs Zety: which is better for a student CV?",
        lead:
          "Zety is a capable general-purpose resume builder. But if you're a student writing a first CV with limited experience, a student-first tool can be a faster, friendlier fit. Here's an honest comparison.",
        primaryCta: { text: "Try Careero free", href: APP },
        secondaryCta: { text: "See other comparisons", href: "/alternatives/resume-io-for-students" },
      },
      {
        type: "cards",
        h2: "Where Careero focuses",
        items: [
          {
            icon: "🎓",
            title: "Student-first by design",
            text: "Sections for coursework, projects, societies and volunteering — not a layout built for a 10-year career.",
            href: "/student-cv-builder",
          },
          {
            icon: "🤖",
            title: "AI for early-career writing",
            text: "Turns a one-line description of a project or internship into strong, quantified bullets.",
            href: "/ai-cv-builder-for-students",
          },
          {
            icon: "⬇️",
            title: "PDF & DOCX download",
            text: "Export a print-ready PDF or an editable DOCX and start free — no wall before you can see your CV.",
          },
        ],
      },
      {
        type: "prose",
        h2: "How to choose",
        paragraphs: [
          "Choose a general builder like Zety if you have years of work history and want a large template library across industries. Choose Careero if you're a student or fresh graduate who wants guidance tailored to a first CV, AI help for projects and internships, and a quick, ATS-friendly result.",
          "Both produce professional CVs — the difference is how much of the student-specific thinking is done for you.",
        ],
      },
      {
        type: "faq",
        items: [
          {
            q: "Is Careero free?",
            a: "Yes — you can build your CV for free and download it. Start at <a href=\"" + APP + "\" rel=\"noopener\">app.careero.app</a>.",
          },
          {
            q: "Is Careero better than Zety?",
            a: "For students writing a first CV, Careero is purpose-built and often faster. For a long professional history across many industries, a general builder may offer more templates. Pick the fit for your stage.",
          },
          {
            q: "Are Careero CVs ATS-friendly?",
            a: "Yes. Careero uses clean layouts and standard headings so applicant tracking systems can parse your CV. See our <a href=\"/ats-friendly-student-cv\">ATS guide</a>.",
          },
        ],
      },
      closingCta(
        "See the difference for yourself",
        "Build a student CV with Careero free — no credit card, PDF and DOCX included.",
        "Try Careero free",
      ),
    ],
  },
];
