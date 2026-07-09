// Suggestion lists for the Student wizard's autocompletes.
//
// The Combobox accepts free text — these lists are shortcuts, never a
// constraint. Whatever the student picks is what we save on the profile.
//
// Universities: the small `UNIVERSITIES` array here is a curated set of
// well-known institutions with common acronyms baked in (e.g. "KFUPM"),
// so type-ahead works on the abbreviation. It's used as an immediate
// seed while `loadUniversities()` fetches the full ~10k Hipolabs
// dataset. Callers merge the two lists once the async load resolves.
//
// Courses / Skills: hand-curated, grouped by faculty/domain in-source
// (see comments) and exported as flat sorted arrays.

// -- Universities ---------------------------------------------------------

// Featured list — well-known institutions with their common acronyms so
// students who type "kfupm" or "kaust" get an immediate hit while the
// full Hipolabs list is still loading (or forever, as a fallback).
export const UNIVERSITIES: string[] = [
  // Saudi Arabia
  "King Fahad University of Petroleum and Minerals (KFUPM) — Saudi Arabia",
  "King Abdullah University of Science and Technology (KAUST) — Saudi Arabia",
  "King Saud University (KSU) — Saudi Arabia",
  "King Abdulaziz University (KAU) — Saudi Arabia",
  "Prince Sultan University (PSU) — Saudi Arabia",
  "Princess Nourah bint Abdulrahman University (PNU) — Saudi Arabia",
  "Imam Abdulrahman Bin Faisal University (IAU) — Saudi Arabia",
  "Alfaisal University — Saudi Arabia",
  "Effat University — Saudi Arabia",
  "Umm Al-Qura University — Saudi Arabia",
  // Wider MENA
  "American University in Cairo (AUC) — Egypt",
  "Cairo University — Egypt",
  "Ain Shams University — Egypt",
  "German University in Cairo (GUC) — Egypt",
  "American University of Beirut (AUB) — Lebanon",
  "Lebanese American University (LAU) — Lebanon",
  "University of Jordan — Jordan",
  "American University of Sharjah (AUS) — United Arab Emirates",
  "Khalifa University — United Arab Emirates",
  "Bilkent University — Turkey",
  "Middle East Technical University (METU) — Turkey",
  "Istanbul Technical University (ITU) — Turkey",
  // US / Canada
  "Massachusetts Institute of Technology (MIT) — United States",
  "Stanford University — United States",
  "Harvard University — United States",
  "California Institute of Technology (Caltech) — United States",
  "Carnegie Mellon University (CMU) — United States",
  "University of California, Berkeley (UC Berkeley) — United States",
  "University of California, Los Angeles (UCLA) — United States",
  "New York University (NYU) — United States",
  "University of Pennsylvania (UPenn) — United States",
  "Georgia Institute of Technology (Georgia Tech) — United States",
  "University of Toronto — Canada",
  "McGill University — Canada",
  "University of British Columbia (UBC) — Canada",
  // UK / Europe
  "University of Oxford — United Kingdom",
  "University of Cambridge — United Kingdom",
  "Imperial College London — United Kingdom",
  "University College London (UCL) — United Kingdom",
  "London School of Economics (LSE) — United Kingdom",
  "ETH Zurich — Switzerland",
  "École Polytechnique Fédérale de Lausanne (EPFL) — Switzerland",
  "Technical University of Munich (TUM) — Germany",
  // Asia / Pacific
  "National University of Singapore (NUS) — Singapore",
  "Nanyang Technological University (NTU) — Singapore",
  "Hong Kong University of Science and Technology (HKUST) — Hong Kong",
  "Tsinghua University — China",
  "Indian Institute of Technology Bombay (IIT Bombay) — India",
  "Indian Institute of Technology Delhi (IIT Delhi) — India",
  "Indian Institute of Technology Madras (IIT Madras) — India",
  "Indian Institute of Science (IISc) — India",
  "Indian Institute of Management Ahmedabad (IIM Ahmedabad) — India",
];

// Full worldwide dataset — lazy-loaded from Hipolabs (~10k entries).
// Cached after first call. Returns strings in "Name — Country" format
// so display is consistent with the featured list above.
let _loadedUnis: string[] | null = null;
let _loadingUnis: Promise<string[]> | null = null;

export async function loadUniversities(): Promise<string[]> {
  if (_loadedUnis) return _loadedUnis;
  if (_loadingUnis) return _loadingUnis;
  _loadingUnis = Promise.all([
    import("@/features/student-wizard/data/universities.json"),
    import("@/features/student-wizard/data/universities-supplementary.json"),
  ]).then(([hipolabs, supp]) => {
    type Row = { name: string; country: string };
    const hipo = (hipolabs as unknown as { default: { universities: Row[] } }).default.universities;
    const extra = (supp as unknown as { default: { universities: Row[] } }).default.universities;
    // Featured list wins on collision (keeps acronyms visible).
    const seen = new Set(UNIVERSITIES.map((s) => stripAcronym(s).toLowerCase()));
    const merged: string[] = [...UNIVERSITIES];
    const push = (r: Row) => {
      const label = `${r.name} — ${r.country}`;
      const key = label.toLowerCase();
      if (seen.has(key)) return;
      seen.add(key);
      merged.push(label);
    };
    // Supplement first so curated MENA additions land ahead of any
    // near-duplicate Hipolabs entry that only differs in punctuation.
    for (const r of extra) push(r);
    for (const r of hipo) push(r);
    _loadedUnis = merged;
    return merged;
  });
  return _loadingUnis;
}

// "KFUPM (King Fahad ...) — Saudi Arabia"  ->  "King Fahad ... — Saudi Arabia"
// Used only for dedupe when merging featured + Hipolabs.
function stripAcronym(label: string): string {
  return label.replace(/\s*\([^)]+\)\s*(?=—)/u, " ");
}

// -- Degrees --------------------------------------------------------------

export const DEGREES: string[] = [
  "Bachelor of Science (BSc)",
  "Bachelor of Arts (BA)",
  "Bachelor of Engineering (BEng)",
  "Bachelor of Computer Science (BCS)",
  "Bachelor of Business Administration (BBA)",
  "Bachelor of Commerce (BCom)",
  "Bachelor of Architecture (BArch)",
  "Bachelor of Medicine, Bachelor of Surgery (MBBS)",
  "Bachelor of Laws (LLB)",
  "Bachelor of Pharmacy (BPharm)",
  "Bachelor of Nursing (BSN)",
  "Bachelor of Education (BEd)",
  "Bachelor of Fine Arts (BFA)",
  "Associate Degree",
  "Diploma",
  "Master of Science (MSc)",
  "Master of Arts (MA)",
  "Master of Engineering (MEng)",
  "Master of Business Administration (MBA)",
  "Master of Laws (LLM)",
  "Master of Public Health (MPH)",
  "Master of Fine Arts (MFA)",
  "Doctor of Philosophy (PhD)",
  "Doctor of Medicine (MD)",
  "Doctor of Dental Surgery (DDS)",
];

// -- Majors ---------------------------------------------------------------

export const MAJORS: string[] = [
  // Computing
  "Computer Science",
  "Computer Engineering",
  "Software Engineering",
  "Information Systems",
  "Information Technology",
  "Cybersecurity",
  "Data Science",
  "Artificial Intelligence",
  "Machine Learning",
  // Engineering
  "Electrical Engineering",
  "Mechanical Engineering",
  "Civil Engineering",
  "Industrial Engineering",
  "Chemical Engineering",
  "Biomedical Engineering",
  "Aerospace Engineering",
  "Petroleum Engineering",
  "Environmental Engineering",
  "Materials Engineering",
  // Sciences
  "Mathematics",
  "Statistics",
  "Physics",
  "Chemistry",
  "Biology",
  "Biochemistry",
  "Molecular Biology",
  "Environmental Science",
  "Geology",
  "Astronomy",
  // Medicine & Health
  "Medicine",
  "Dentistry",
  "Pharmacy",
  "Nursing",
  "Public Health",
  "Nutrition and Dietetics",
  "Physical Therapy",
  "Veterinary Medicine",
  "Medical Laboratory Science",
  "Radiology and Medical Imaging",
  // Business
  "Economics",
  "Finance",
  "Accounting",
  "Marketing",
  "Management",
  "Business Administration",
  "International Business",
  "Human Resources Management",
  "Supply Chain Management",
  "Entrepreneurship",
  // Law & Policy
  "Law",
  "Islamic Law (Sharia)",
  "Political Science",
  "International Relations",
  "Public Administration",
  "Public Policy",
  // Social Sciences
  "Psychology",
  "Sociology",
  "Anthropology",
  "Social Work",
  "Criminology",
  // Humanities
  "History",
  "Philosophy",
  "Islamic Studies",
  "Arabic Language and Literature",
  "English Language and Literature",
  "Linguistics",
  "Religious Studies",
  "Translation Studies",
  // Arts & Design
  "Architecture",
  "Interior Design",
  "Graphic Design",
  "Industrial Design",
  "Fashion Design",
  "Fine Arts",
  "Film and Media",
  "Music",
  "Theater Arts",
  // Education
  "Education",
  "Early Childhood Education",
  "Special Education",
  // Communications & Media
  "Communications",
  "Journalism",
  "Public Relations",
  "Media Studies",
  // Agriculture & Env
  "Agriculture",
  "Food Science",
  "Agricultural Engineering",
  // Other
  "Urban Planning",
  "Hospitality Management",
  "Tourism Management",
  "Sports Science",
  "Aviation",
];

// -- Skills ---------------------------------------------------------------

// Domain-grouped in comments; exported flat + sorted A→Z so the
// Combobox's substring/starts-with search picks the closest matches.
export const SKILLS: string[] = [
  // Software — languages, frameworks, infra, tooling
  "Ansible",
  "Angular",
  "Apache Kafka",
  "AWS",
  "Bash",
  "C",
  "C#",
  "C++",
  "CI/CD",
  "CSS",
  "Dart",
  "Django",
  "Docker",
  "Elasticsearch",
  "Elixir",
  "Express",
  "FastAPI",
  "Flask",
  "Flutter",
  "Git",
  "Go",
  "Google Cloud",
  "GraphQL",
  "gRPC",
  "HTML",
  "Java",
  "JavaScript",
  "Kotlin",
  "Kubernetes",
  "Laravel",
  "Linux",
  "MATLAB",
  "Microsoft Azure",
  "MongoDB",
  "MySQL",
  "Nest.js",
  "Next.js",
  "Node.js",
  "PHP",
  "PostgreSQL",
  "Python",
  "PyTorch",
  "React",
  "React Native",
  "Redis",
  "REST APIs",
  "Ruby",
  "Ruby on Rails",
  "Rust",
  "Scala",
  "scikit-learn",
  "Solidity",
  "Spring Boot",
  "SQL",
  "Swift",
  "System Design",
  "TensorFlow",
  "Terraform",
  "TypeScript",
  "Unit Testing",
  "Vue.js",

  // Data / analytics
  "Airflow",
  "Apache Spark",
  "BigQuery",
  "dbt",
  "Excel (Advanced)",
  "Google Analytics",
  "Hadoop",
  "Looker",
  "NumPy",
  "pandas",
  "Power BI",
  "R",
  "SAS",
  "Snowflake",
  "SPSS",
  "Stata",
  "Tableau",

  // Design & creative
  "Adobe After Effects",
  "Adobe Illustrator",
  "Adobe InDesign",
  "Adobe Lightroom",
  "Adobe Photoshop",
  "Adobe Premiere Pro",
  "AutoCAD",
  "Blender",
  "Canva",
  "Figma",
  "Procreate",
  "Revit",
  "Sketch",
  "SketchUp",
  "UI Design",
  "UX Research",

  // Business / sales / operations
  "Account Management",
  "Budgeting",
  "Business Analysis",
  "Contract Drafting",
  "CRM",
  "Cross-Functional Collaboration",
  "Financial Modeling",
  "Forecasting",
  "Fundraising",
  "HubSpot",
  "Investor Relations",
  "Market Research",
  "Negotiation",
  "P&L Ownership",
  "Salesforce",
  "Stakeholder Management",
  "Vendor Management",

  // Marketing
  "Brand Strategy",
  "Content Marketing",
  "Copywriting",
  "Email Marketing",
  "Google Ads",
  "Meta Ads",
  "SEM",
  "SEO",
  "Social Media Strategy",
  "TikTok Ads",

  // Medical / lab
  "Clinical Assessment",
  "CPR/BLS",
  "EMR/EHR",
  "Lab Techniques",
  "Medical Coding",
  "Microscopy",
  "Patient Care",
  "PCR",
  "Phlebotomy",
  "Radiology Basics",

  // Legal
  "Case Analysis",
  "Compliance",
  "Contract Review",
  "IP Filing",
  "Legal Research",
  "Legal Writing",
  "Litigation Support",
  "Regulatory Analysis",

  // Teaching / education
  "Assessment Design",
  "Classroom Management",
  "Curriculum Development",
  "IEP Development",
  "Lesson Planning",
  "Online Instruction",
  "Special Education Support",
  "Tutoring",

  // Writing & communication
  "Copyediting",
  "Grant Writing",
  "Interviewing",
  "Presentation Design",
  "Public Speaking",
  "Report Writing",
  "Storytelling",
  "Technical Writing",
  "Translation (Arabic ↔ English)",

  // Soft / general
  "Adaptability",
  "Client Relations",
  "Conflict Resolution",
  "Decision-Making",
  "Facilitation",
  "Leadership",
  "Mentorship",
  "Problem Solving",
  "Project Coordination",
  "Project Management",
  "Research",
  "Team Leadership",
  "Time Management",
];

// Tech-only subset used by the Projects step's "Technologies used"
// field — students describing a project don't need "CPR/BLS" or
// "Salesforce" in their tech picker.
export const TECH_STACK: string[] = [
  "Angular",
  "Ansible",
  "Apache Kafka",
  "AWS",
  "Bash",
  "C",
  "C#",
  "C++",
  "CI/CD",
  "CSS",
  "Dart",
  "Django",
  "Docker",
  "Elasticsearch",
  "Elixir",
  "Express",
  "FastAPI",
  "Figma",
  "Flask",
  "Flutter",
  "Git",
  "Go",
  "Google Cloud",
  "GraphQL",
  "gRPC",
  "HTML",
  "Java",
  "JavaScript",
  "Kotlin",
  "Kubernetes",
  "Laravel",
  "Linux",
  "MATLAB",
  "Microsoft Azure",
  "MongoDB",
  "MySQL",
  "Nest.js",
  "Next.js",
  "Node.js",
  "NumPy",
  "pandas",
  "PHP",
  "PostgreSQL",
  "Python",
  "PyTorch",
  "R",
  "React",
  "React Native",
  "Redis",
  "REST APIs",
  "Ruby",
  "Ruby on Rails",
  "Rust",
  "Scala",
  "scikit-learn",
  "Solidity",
  "Spring Boot",
  "SQL",
  "Swift",
  "TensorFlow",
  "Terraform",
  "TypeScript",
  "Vue.js",
];

// -- Courses --------------------------------------------------------------

// Grouped in-source by faculty; exported flat + sorted A→Z. Substring
// search in the Combobox handles discovery — a student typing "cont"
// surfaces "Contract Law", "Control Systems", "Content Marketing".
export const COURSES: string[] = [
  // Medicine & Health Sciences
  "Anatomy",
  "Biochemistry (Medical)",
  "Cell Biology",
  "Clinical Skills",
  "Community Medicine",
  "Emergency Medicine",
  "Epidemiology",
  "General Medicine",
  "Gynecology",
  "Histology",
  "Immunology",
  "Internal Medicine",
  "Medical Ethics",
  "Medical Genetics",
  "Medical Microbiology",
  "Nursing Fundamentals",
  "Nutrition",
  "Obstetrics",
  "Pathology",
  "Pediatrics",
  "Pharmacology",
  "Physiology",
  "Public Health",
  "Radiology",
  "Surgery Basics",

  // Law
  "Administrative Law",
  "Civil Procedure",
  "Commercial Law",
  "Constitutional Law",
  "Contract Law",
  "Corporate Law",
  "Criminal Law",
  "Environmental Law",
  "Evidence Law",
  "Family Law",
  "Human Rights Law",
  "Intellectual Property Law",
  "International Law",
  "Islamic Jurisprudence (Fiqh)",
  "Legal Writing",
  "Tort Law",

  // Business / Economics / Finance / Accounting
  "Auditing",
  "Behavioral Economics",
  "Business Ethics",
  "Business Statistics",
  "Consumer Behavior",
  "Corporate Finance",
  "Cost Accounting",
  "Development Economics",
  "Entrepreneurship",
  "Financial Accounting",
  "Financial Modeling",
  "Human Resource Management",
  "International Business",
  "International Trade",
  "Investment Analysis",
  "Labor Economics",
  "Macroeconomics",
  "Managerial Accounting",
  "Managerial Economics",
  "Marketing Principles",
  "Microeconomics",
  "Money and Banking",
  "Operations Management",
  "Operations Research",
  "Organizational Behavior",
  "Principles of Management",
  "Public Economics",
  "Strategic Management",
  "Supply Chain Management",
  "Taxation",

  // Engineering (Civil, Mech, Elec, Chem, Ind, Biomed)
  "Chemical Reactor Design",
  "Circuit Analysis",
  "Computer-Aided Design",
  "Concrete Structures",
  "Construction Materials",
  "Control Systems",
  "Digital Logic Design",
  "Electric Machines",
  "Electromagnetic Theory",
  "Engineering Drawing",
  "Engineering Ethics",
  "Engineering Mechanics",
  "Environmental Engineering",
  "Fluid Mechanics",
  "Geotechnical Engineering",
  "Heat Transfer",
  "Highway Engineering",
  "Hydraulics",
  "Industrial Engineering",
  "Machine Design",
  "Manufacturing Processes",
  "Materials Science",
  "Mechanical Vibrations",
  "Power Systems",
  "Process Control",
  "Reinforced Concrete Design",
  "Robotics",
  "Signals and Systems",
  "Solid Mechanics",
  "Statics and Dynamics",
  "Steel Structures",
  "Structural Analysis",
  "Surveying",
  "Thermodynamics",
  "Transportation Engineering",

  // Computer Science / IT
  "Artificial Intelligence",
  "Blockchain Fundamentals",
  "Cloud Computing",
  "Compilers",
  "Computer Architecture",
  "Computer Graphics",
  "Computer Networks",
  "Computer Vision",
  "Cybersecurity Fundamentals",
  "Data Structures and Algorithms",
  "Database Systems",
  "DevOps",
  "Digital Signal Processing",
  "Distributed Systems",
  "Human-Computer Interaction",
  "Information Retrieval",
  "Introduction to Programming",
  "Machine Learning",
  "Mobile App Development",
  "Natural Language Processing",
  "Object-Oriented Programming",
  "Operating Systems",
  "Parallel Computing",
  "Software Engineering",
  "Theory of Computation",
  "Web Development",

  // Math & Statistics
  "Abstract Algebra",
  "Calculus I",
  "Calculus II",
  "Calculus III",
  "Differential Equations",
  "Discrete Mathematics",
  "Linear Algebra",
  "Mathematical Analysis",
  "Multivariable Calculus",
  "Numerical Methods",
  "Number Theory",
  "Optimization Theory",
  "Probability and Statistics",
  "Real Analysis",
  "Stochastic Processes",
  "Topology",

  // Natural Sciences
  "Analytical Chemistry",
  "Astronomy",
  "Atmospheric Science",
  "Biology I",
  "Biology II",
  "Botany",
  "Ecology",
  "Environmental Science",
  "Evolutionary Biology",
  "General Chemistry I",
  "General Chemistry II",
  "Genetics",
  "Geology",
  "Inorganic Chemistry",
  "Marine Biology",
  "Meteorology",
  "Microbiology",
  "Molecular Biology",
  "Organic Chemistry",
  "Physical Chemistry",
  "Physics I",
  "Physics II",
  "Quantum Mechanics",
  "Solid State Physics",
  "Zoology",

  // Social Sciences
  "Abnormal Psychology",
  "Anthropology",
  "Cognitive Psychology",
  "Comparative Politics",
  "Cultural Studies",
  "Demography",
  "Developmental Psychology",
  "Gender Studies",
  "International Relations",
  "Introduction to Psychology",
  "Political Economy",
  "Political Science",
  "Political Theory",
  "Public Administration",
  "Public Policy",
  "Qualitative Research Methods",
  "Quantitative Research Methods",
  "Social Psychology",
  "Sociology",
  "Urban Studies",

  // Humanities
  "Ancient History",
  "Arabic Language and Literature",
  "Classical Studies",
  "Comparative Religion",
  "Ethics",
  "Islamic Studies",
  "Linguistics",
  "Logic",
  "Middle Eastern History",
  "Modern History",
  "Philosophy of Science",
  "Rhetoric",
  "World History",
  "World Literature",
  "Writing and Composition",

  // Arts & Design
  "Animation",
  "Art History",
  "Digital Media Design",
  "Drawing",
  "Fashion Design",
  "Film Studies",
  "Graphic Design",
  "Illustration",
  "Interior Design",
  "Music History",
  "Music Theory",
  "Painting",
  "Photography",
  "Sculpture",
  "Theater Arts",

  // Architecture & Planning
  "Architectural Design Studio",
  "Architectural History",
  "Building Systems",
  "Construction Technology",
  "Landscape Architecture",
  "Site Planning",
  "Structural Systems for Architects",
  "Sustainable Design",
  "Urban Design",
  "Urban Planning",

  // Education
  "Assessment and Evaluation",
  "Child Development",
  "Classroom Management (Education)",
  "Curriculum Design",
  "Educational Psychology",
  "Educational Technology",
  "Instructional Design",
  "Learning Theories",
  "Special Education",
  "Teaching Methods",

  // Communications / Media
  "Advertising",
  "Broadcasting",
  "Digital Media",
  "Journalism",
  "Media Ethics",
  "Media Law",
  "Media Studies",
  "Public Relations",
  "Screenwriting",
  "Social Media Strategy (Course)",

  // Agriculture / Food Science / Env
  "Agricultural Economics",
  "Agronomy",
  "Animal Science",
  "Crop Science",
  "Food Chemistry",
  "Food Safety",
  "Food Science",
  "Horticulture",
  "Plant Pathology",
  "Soil Science",
  "Sustainable Agriculture",
  "Veterinary Anatomy",

  // Technical writing (spans faculties)
  "Technical Writing",
].sort((a, b) => a.localeCompare(b));

// -- Languages ------------------------------------------------------------

export const LANGUAGES: string[] = [
  "Arabic",
  "English",
  "French",
  "Spanish",
  "German",
  "Italian",
  "Portuguese",
  "Russian",
  "Chinese (Mandarin)",
  "Japanese",
  "Korean",
  "Hindi",
  "Urdu",
  "Turkish",
  "Dutch",
  "Swedish",
  "Norwegian",
  "Polish",
  "Greek",
  "Hebrew",
  "Persian (Farsi)",
];

export const LANGUAGE_PROFICIENCIES: string[] = ["Basic", "Intermediate", "Fluent", "Native"];

export const SKILL_PROFICIENCIES: { value: string; label: string }[] = [
  { value: "1", label: "1 — Beginner" },
  { value: "2", label: "2 — Novice" },
  { value: "3", label: "3 — Intermediate" },
  { value: "4", label: "4 — Advanced" },
  { value: "5", label: "5 — Expert" },
];

// -- Certificates ---------------------------------------------------------

export const CERTIFICATES: string[] = [
  "AWS Certified Cloud Practitioner",
  "AWS Certified Solutions Architect – Associate",
  "AWS Certified Developer – Associate",
  "Google Cloud Associate Cloud Engineer",
  "Google Cloud Professional Data Engineer",
  "Microsoft Certified: Azure Fundamentals",
  "Microsoft Certified: Azure Administrator Associate",
  "CompTIA A+",
  "CompTIA Network+",
  "CompTIA Security+",
  "Certified Ethical Hacker (CEH)",
  "Cisco Certified Network Associate (CCNA)",
  "Oracle Certified Associate (OCA)",
  "Project Management Professional (PMP)",
  "Certified ScrumMaster (CSM)",
  "Google Data Analytics Professional Certificate",
  "Google IT Support Professional Certificate",
  "Meta Front-End Developer Professional Certificate",
  "DeepLearning.AI Machine Learning Specialization",
  "IBM Data Science Professional Certificate",
];

export const CERTIFICATE_ISSUERS: string[] = [
  "Amazon Web Services",
  "Google Cloud",
  "Microsoft",
  "CompTIA",
  "EC-Council",
  "Cisco",
  "Oracle",
  "PMI",
  "Scrum Alliance",
  "Coursera",
  "edX",
  "Udacity",
  "DataCamp",
  "DeepLearning.AI",
  "IBM",
  "Meta",
];

// -- Internships ----------------------------------------------------------

export const INTERNSHIP_FIELD_OPTIONS: {
  value:
    | "software_engineering"
    | "data_analysis"
    | "marketing"
    | "hr"
    | "finance"
    | "design"
    | "customer_support"
    | "other";
  label: string;
}[] = [
  { value: "software_engineering", label: "Software Engineering" },
  { value: "data_analysis", label: "Data Analysis" },
  { value: "marketing", label: "Marketing" },
  { value: "hr", label: "HR" },
  { value: "finance", label: "Finance" },
  { value: "design", label: "Design" },
  { value: "customer_support", label: "Customer Support" },
  { value: "other", label: "Other" },
];

// One-click task templates the student can pin into their
// Responsibilities textarea after picking an internship field. Each
// starts with an action verb so the resulting bullet is ATS-friendly.
//
// Each field has a pool of ~12 tasks; the UI shows 6 at a time and
// backfills from the pool as chips get picked. When the pool is
// exhausted the row goes empty (no synthetic suggestions).
export const INTERNSHIP_FIELD_TASK_PRESETS: Record<string, string[]> = {
  software_engineering: [
    "Assisted in building frontend or backend features.",
    "Fixed bugs and tested application flows.",
    "Used GitHub, APIs, databases, or frameworks.",
    "Collaborated with developers during code reviews.",
    "Wrote unit tests and validated changes before merging.",
    "Documented technical decisions in a shared wiki.",
    "Attended stand-ups and sprint planning meetings.",
    "Debugged production issues with the on-call engineer.",
    "Built internal tools that automated a recurring task.",
    "Read and reviewed pull requests from other interns.",
    "Learned the deployment pipeline and shipped a change end-to-end.",
    "Improved page load performance for a specific flow.",
  ],
  data_analysis: [
    "Cleaned and analyzed datasets.",
    "Created reports or dashboards.",
    "Used Excel, SQL, Python, Power BI, or Tableau.",
    "Presented findings to the team.",
    "Wrote SQL queries to answer business questions.",
    "Built pivot tables and charts summarising monthly metrics.",
    "Automated a recurring report using Python or spreadsheets.",
    "Identified anomalies and flagged them for review.",
    "Documented data definitions and assumptions.",
    "Joined data sources from multiple systems.",
    "A/B-tested a hypothesis and shared the results.",
    "Validated data quality against source systems.",
  ],
  marketing: [
    "Supported social media campaigns.",
    "Created content ideas.",
    "Analyzed engagement metrics.",
    "Helped prepare campaign reports.",
    "Drafted copy for email or newsletter sends.",
    "Scheduled posts across LinkedIn, Instagram, or X.",
    "Researched competitors and summarised positioning.",
    "Ran a keyword-research pass for SEO.",
    "Prepared briefs for designers and video editors.",
    "Coordinated with influencers or partners.",
    "Tracked campaign KPIs against targets.",
    "Reported on ROI for a specific channel.",
  ],
  hr: [
    "Supported recruitment activities.",
    "Screened CVs.",
    "Coordinated interviews.",
    "Helped with employee documentation.",
    "Scheduled candidate interviews across time zones.",
    "Drafted job descriptions with the hiring manager.",
    "Maintained the applicant tracking system (ATS).",
    "Supported new-joiner onboarding sessions.",
    "Coordinated employee engagement events.",
    "Prepared training materials for team workshops.",
    "Updated policy documents and HR handbooks.",
    "Analysed hiring funnel metrics.",
  ],
  finance: [
    "Assisted with financial reports.",
    "Reviewed transactions or invoices.",
    "Used Excel or accounting tools.",
    "Supported budgeting or reconciliation tasks.",
    "Reconciled bank statements against ledger entries.",
    "Prepared monthly closing schedules.",
    "Built financial models for scenario analysis.",
    "Tracked accounts payable and receivable aging.",
    "Assisted external auditors during audit season.",
    "Analysed variance between budget and actuals.",
    "Documented internal controls and processes.",
    "Prepared cash-flow forecasts for management review.",
  ],
  design: [
    "Created visuals, banners, or UI elements.",
    "Used tools like Figma, Canva, Photoshop, or Illustrator.",
    "Supported brand or product design tasks.",
    "Collaborated with product or marketing teams.",
    "Iterated on wireframes based on user feedback.",
    "Built and maintained a component style guide.",
    "Prototyped interactions in Figma for user testing.",
    "Designed social-media creatives for campaigns.",
    "Prepared assets and specs for developer handoff.",
    "Ran usability tests with 3-5 participants.",
    "Illustrated icons or spot graphics for the product.",
    "Audited existing screens for accessibility issues.",
  ],
  customer_support: [
    "Responded to customer inquiries.",
    "Logged issues and escalated cases.",
    "Used CRM or ticketing tools.",
    "Helped improve customer satisfaction.",
    "Wrote help-center articles for recurring questions.",
    "Categorised tickets and tagged them for reporting.",
    "Collaborated with engineering on bug reproductions.",
    "Analysed CSAT survey responses for patterns.",
    "Supported live chat during high-volume periods.",
    "Trained new agents on ticket workflows.",
    "Reduced average response time on a specific queue.",
    "Documented internal knowledge-base updates.",
  ],
  other: [],
};

// Action-verb chips shown next to the Responsibilities textarea. Click
// appends a bullet-shaped template ("Tested — ") that the student can
// finish in their own words.
export const INTERNSHIP_ACTION_CHIPS: string[] = [
  "Tested",
  "Analyzed",
  "Built",
  "Supported",
  "Presented",
  "Documented",
  "Designed",
  "Coordinated",
];

export const INTERNSHIP_WORK_MODES: { value: "on_site" | "remote" | "hybrid"; label: string }[] = [
  { value: "on_site", label: "On-site" },
  { value: "remote", label: "Remote" },
  { value: "hybrid", label: "Hybrid" },
];
