export type CareerStatus = "missing" | "started" | "needs_improvement" | "completed";

export interface LinkedInProjectSuggestion {
  name: string;
  description: string;
}

export interface LinkedInGenerated {
  headline: string;
  about: string;
  education_entry: string;
  project_entries: LinkedInProjectSuggestion[];
  skills: string[];
  checklist: string[];
}

export interface LinkedInReview {
  summary: string;
  current_headline_review: string | null;
  suggested_headline: string | null;
  current_about_review: string | null;
  suggested_about: string | null;
  missing_sections: string[];
  skills_to_add: string[];
  projects_to_improve: string[];
  checklist: string[];
}

export interface GitHubProjectReadme {
  project_title: string;
  filename: string;
  body: string;
}

export interface GitHubGenerated {
  username_suggestions: string[];
  bio: string;
  profile_readme: string;
  project_readmes: GitHubProjectReadme[];
  checklist: string[];
}

export interface GitHubReview {
  profile_summary: string;
  has_profile_readme: boolean | null;
  suggested_bio: string | null;
  suggested_profile_readme: string | null;
  project_readme_suggestions: GitHubProjectReadme[];
  repo_checklist: string[];
  cv_projects_to_add: string[];
}

export interface CareerPack {
  linkedin_url: string | null;
  github_url: string | null;
  linkedin_status: CareerStatus;
  github_status: CareerStatus;
  linkedin_generated: LinkedInGenerated | null;
  linkedin_recommendations: LinkedInReview | null;
  github_generated: GitHubGenerated | null;
  github_recommendations: GitHubReview | null;
  github_username: string | null;
}
