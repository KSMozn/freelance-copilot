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
      "Create your first professional student CV with Careero. Build an ATS-friendly CV, improve your projects and internships, choose from modern templates, and download as PDF or DOCX.",
    h1: "Build your first student CV with confidence",
    type: "website",
    blocks: [
      {
        type: "hero",
        kicker: "AI CV Builder for Students",
        h1: "Build your first student CV with confidence",
        lead:
          "Careero turns your courses, projects and internships into a clean, ATS-friendly CV — with AI that helps you describe your experience in strong, recruiter-ready language. No blank page, no guesswork.",
        primaryCta: { text: "Create your CV now", href: APP },
        secondaryCta: { text: "See templates", href: "/student-cv-templates" },
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
          "Careero is designed for people writing their <strong>first</strong> CV — students, fresh graduates and interns — not senior professionals with 15 years of history.",
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
            href: "/ai-cv-builder",
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
            href: "/blog/how-to-describe-student-projects",
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
            a: "That is exactly who Careero is built for. Read our guide on <a href=\"/blog/how-to-write-cv-with-no-experience\">writing a CV with no experience</a>.",
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
    slug: "write-cv-for-students",
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
        secondaryCta: { text: "CV with no experience", href: "/blog/how-to-write-cv-with-no-experience" },
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
            a: "Education, academic and personal projects, volunteering, societies, and any part-time or casual work. Our <a href=\"/blog/how-to-write-cv-with-no-experience\">no-experience guide</a> covers this in detail.",
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
        h2: "Templates for every kind of student application",
        items: [
          {
            icon: "🟦",
            title: "Classic",
            text: "A timeless single-column layout that suits any field and always parses cleanly in an ATS.",
          },
          {
            icon: "🟪",
            title: "Modern",
            text: "A contemporary design with subtle accent colour — professional without looking like a template.",
          },
          {
            icon: "🟩",
            title: "Technical",
            text: "Projects and skills up front — ideal for computer science, engineering and data roles.",
          },
          {
            icon: "🟨",
            title: "Minimal",
            text: "Maximum white space and clarity for when your content should do all the talking.",
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
    slug: "ai-cv-builder",
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
            href: "/blog/how-to-describe-student-projects",
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
            href: "/blog/how-to-describe-student-projects",
          },
          {
            icon: "🚀",
            title: "How to write a CV with no experience",
            text: "What to include — and how to describe it — when you don't have formal work history yet.",
            href: "/blog/how-to-write-cv-with-no-experience",
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
    slug: "blog/how-to-describe-student-projects",
    title: "How to Describe Student Projects on a CV (With Examples) | Careero",
    description:
      "Learn how to describe academic and personal projects on your CV so they show real skills. Includes before-and-after examples and a simple formula. Build your CV free with Careero.",
    h1: "How to describe student projects on your CV",
    type: "article",
    datePublished: PUB,
    dateModified: MOD,
    blocks: [
      {
        type: "hero",
        kicker: "Guide · 5 min read",
        h1: "How to describe student projects on your CV",
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
    slug: "blog/how-to-write-cv-with-no-experience",
    title: "How to Write a CV With No Experience (Student Guide) | Careero",
    description:
      "No work experience? You can still write a strong CV. Learn what to include, how to describe transferable skills, and how to fill the page with substance. Build yours free with Careero.",
    h1: "How to write a CV with no experience",
    type: "article",
    datePublished: PUB,
    dateModified: MOD,
    blocks: [
      {
        type: "hero",
        kicker: "Guide · 5 min read",
        h1: "How to write a CV with no experience",
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
            href: "/github-profile-for-students",
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
    slug: "linkedin-profile-for-students",
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
        secondaryCta: { text: "Write a CV with no experience", href: "/blog/how-to-write-cv-with-no-experience" },
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
    slug: "github-profile-for-students",
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
        secondaryCta: { text: "Describe your projects", href: "/blog/how-to-describe-student-projects" },
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
            a: "Use achievement-focused bullets: what you built, the tech, and the outcome. See our guide on <a href=\"/blog/how-to-describe-student-projects\">describing student projects</a>.",
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
];
