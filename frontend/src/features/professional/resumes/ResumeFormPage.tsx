import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { toast } from "sonner";

import { Button } from "@/shared/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/shared/ui/card";
import { Input } from "@/shared/ui/input";
import { Label } from "@/shared/ui/label";
import { Textarea } from "@/shared/ui/textarea";
import {
  useCreateResume,
  useResume,
  useUpdateResume,
} from "@/features/professional/resumes/resumesApi";
import type { ResumeCreate } from "@/features/professional/apiTypes";

const SENIORITY_OPTIONS = ["", "junior", "mid", "senior", "lead", "staff", "principal"];

const EMPTY: ResumeCreate = {
  title: "",
  target_role: "",
  summary: "",
  seniority_level: null,
  primary_skills: [],
  secondary_skills: [],
  industries: [],
  domains: [],
  achievements: [],
  project_highlights: [],
  keywords: [],
  notes: "",
};

function parseList(value: string): string[] {
  return value
    .split(/[,\n]/)
    .map((s) => s.trim())
    .filter(Boolean);
}

function listToString(items: string[] | undefined): string {
  return (items ?? []).join(", ");
}

export function ResumeFormPage() {
  const { id } = useParams<{ id: string }>();
  const isEdit = !!id && id !== "new";
  const navigate = useNavigate();
  const { data: loaded, isLoading } = useResume(isEdit ? id : undefined);
  const create = useCreateResume();
  const update = useUpdateResume(id);

  const [form, setForm] = useState<ResumeCreate>(EMPTY);
  const [primary, setPrimary] = useState("");
  const [secondary, setSecondary] = useState("");
  const [industries, setIndustries] = useState("");
  const [domains, setDomains] = useState("");
  const [achievements, setAchievements] = useState("");
  const [highlights, setHighlights] = useState("");
  const [keywords, setKeywords] = useState("");

  useEffect(() => {
    if (!isEdit || !loaded) return;
    setForm({
      title: loaded.title,
      target_role: loaded.target_role ?? "",
      summary: loaded.summary ?? "",
      seniority_level: (loaded.seniority_level as ResumeCreate["seniority_level"]) ?? null,
      primary_skills: loaded.primary_skills,
      secondary_skills: loaded.secondary_skills,
      industries: loaded.industries,
      domains: loaded.domains,
      achievements: loaded.achievements,
      project_highlights: loaded.project_highlights,
      keywords: loaded.keywords,
      notes: loaded.notes ?? "",
    });
    setPrimary(listToString(loaded.primary_skills));
    setSecondary(listToString(loaded.secondary_skills));
    setIndustries(listToString(loaded.industries));
    setDomains(listToString(loaded.domains));
    setAchievements(listToString(loaded.achievements));
    setHighlights(listToString(loaded.project_highlights));
    setKeywords(listToString(loaded.keywords));
  }, [isEdit, loaded]);

  const set = <K extends keyof ResumeCreate>(k: K, v: ResumeCreate[K]) =>
    setForm((f) => ({ ...f, [k]: v }));

  const onSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const payload: ResumeCreate = {
      ...form,
      primary_skills: parseList(primary),
      secondary_skills: parseList(secondary),
      industries: parseList(industries),
      domains: parseList(domains),
      achievements: parseList(achievements),
      project_highlights: parseList(highlights),
      keywords: parseList(keywords),
    };
    if (isEdit) {
      update.mutate(payload, {
        onSuccess: () => {
          toast.success("Resume saved");
          navigate("/resumes");
        },
        onError: () => toast.error("Could not save"),
      });
    } else {
      create.mutate(payload, {
        onSuccess: () => {
          toast.success("Resume created");
          navigate("/resumes");
        },
        onError: () => toast.error("Could not create"),
      });
    }
  };

  if (isEdit && isLoading) {
    return <div className="text-sm text-muted-foreground">Loading…</div>;
  }

  return (
    <div className="mx-auto max-w-3xl space-y-4">
      <h1 className="text-2xl font-semibold tracking-tight">
        {isEdit ? "Edit resume" : "New resume"}
      </h1>

      <Card>
        <CardHeader>
          <CardTitle>Resume profile</CardTitle>
        </CardHeader>
        <CardContent>
          <form className="space-y-4" onSubmit={onSubmit}>
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
              <div className="space-y-2 md:col-span-2">
                <Label htmlFor="title">Title</Label>
                <Input
                  id="title"
                  value={form.title}
                  required
                  onChange={(e) => set("title", e.target.value)}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="role">Target role</Label>
                <Input
                  id="role"
                  value={form.target_role ?? ""}
                  onChange={(e) => set("target_role", e.target.value)}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="seniority">Seniority</Label>
                <select
                  id="seniority"
                  className="h-10 w-full rounded-md border border-input bg-background px-3 text-sm"
                  value={form.seniority_level ?? ""}
                  onChange={(e) =>
                    set(
                      "seniority_level",
                      (e.target.value || null) as ResumeCreate["seniority_level"],
                    )
                  }
                >
                  {SENIORITY_OPTIONS.map((s) => (
                    <option key={s || "_none"} value={s}>
                      {s || "—"}
                    </option>
                  ))}
                </select>
              </div>
              <div className="space-y-2 md:col-span-2">
                <Label htmlFor="summary">Summary</Label>
                <Textarea
                  id="summary"
                  rows={4}
                  value={form.summary ?? ""}
                  onChange={(e) => set("summary", e.target.value)}
                />
              </div>
              <div className="space-y-2 md:col-span-2">
                <Label htmlFor="primary">Primary skills</Label>
                <Input
                  id="primary"
                  value={primary}
                  onChange={(e) => setPrimary(e.target.value)}
                  placeholder="Python, FastAPI, RAG"
                />
              </div>
              <div className="space-y-2 md:col-span-2">
                <Label htmlFor="secondary">Secondary skills</Label>
                <Input
                  id="secondary"
                  value={secondary}
                  onChange={(e) => setSecondary(e.target.value)}
                  placeholder="Docker, Kubernetes, AWS"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="industries">Industries</Label>
                <Input
                  id="industries"
                  value={industries}
                  onChange={(e) => setIndustries(e.target.value)}
                  placeholder="AI SaaS, Enterprise SaaS"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="domains">Domains</Label>
                <Input
                  id="domains"
                  value={domains}
                  onChange={(e) => setDomains(e.target.value)}
                  placeholder="AI SaaS, Document Management"
                />
              </div>
              <div className="space-y-2 md:col-span-2">
                <Label htmlFor="achievements">Achievements</Label>
                <Textarea
                  id="achievements"
                  rows={3}
                  value={achievements}
                  onChange={(e) => setAchievements(e.target.value)}
                  placeholder="One per line or comma-separated"
                />
              </div>
              <div className="space-y-2 md:col-span-2">
                <Label htmlFor="highlights">Project highlights</Label>
                <Textarea
                  id="highlights"
                  rows={3}
                  value={highlights}
                  onChange={(e) => setHighlights(e.target.value)}
                />
              </div>
              <div className="space-y-2 md:col-span-2">
                <Label htmlFor="keywords">Keywords</Label>
                <Input
                  id="keywords"
                  value={keywords}
                  onChange={(e) => setKeywords(e.target.value)}
                  placeholder="RAG, document Q&A, enterprise AI"
                />
              </div>
              <div className="space-y-2 md:col-span-2">
                <Label htmlFor="notes">Notes</Label>
                <Textarea
                  id="notes"
                  rows={2}
                  value={form.notes ?? ""}
                  onChange={(e) => set("notes", e.target.value)}
                  placeholder="Private notes, e.g. when to lead with this resume."
                />
              </div>
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <Button type="button" variant="outline" onClick={() => navigate("/resumes")}>
                Cancel
              </Button>
              <Button type="submit" disabled={create.isPending || update.isPending}>
                {isEdit ? "Save changes" : "Create resume"}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
