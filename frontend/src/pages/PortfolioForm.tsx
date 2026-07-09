import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { toast } from "sonner";

import { Button } from "@/shared/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/shared/ui/card";
import { Input } from "@/shared/ui/input";
import { Label } from "@/shared/ui/label";
import { Textarea } from "@/shared/ui/textarea";
import {
  useCreatePortfolio,
  usePortfolio,
  useUpdatePortfolio,
} from "@/lib/portfolio";
import type { PortfolioCreate } from "@/types/api";

const EMPTY: PortfolioCreate = {
  title: "",
  short_description: "",
  long_description: "",
  role: "",
  business_domain: "",
  github_url: "",
  live_url: "",
  technologies: [],
  skills: [],
  features: [],
  outcomes: [],
  highlight: false,
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

export function PortfolioFormPage() {
  const { id } = useParams<{ id: string }>();
  const isEdit = !!id && id !== "new";
  const navigate = useNavigate();
  const { data: loaded, isLoading } = usePortfolio(isEdit ? id : undefined);
  const create = useCreatePortfolio();
  const update = useUpdatePortfolio(id);

  const [form, setForm] = useState<PortfolioCreate>(EMPTY);
  const [tech, setTech] = useState("");
  const [skills, setSkills] = useState("");
  const [features, setFeatures] = useState("");
  const [outcomes, setOutcomes] = useState("");

  useEffect(() => {
    if (!isEdit || !loaded) return;
    setForm({
      title: loaded.title,
      short_description: loaded.short_description ?? "",
      long_description: loaded.long_description,
      role: loaded.role ?? "",
      business_domain: loaded.business_domain ?? "",
      github_url: loaded.github_url ?? "",
      live_url: loaded.live_url ?? "",
      technologies: loaded.technologies,
      skills: loaded.skills,
      features: loaded.features,
      outcomes: loaded.outcomes,
      highlight: loaded.highlight,
    });
    setTech(listToString(loaded.technologies));
    setSkills(listToString(loaded.skills));
    setFeatures(listToString(loaded.features));
    setOutcomes(listToString(loaded.outcomes));
  }, [isEdit, loaded]);

  const set = <K extends keyof PortfolioCreate>(k: K, v: PortfolioCreate[K]) =>
    setForm((f) => ({ ...f, [k]: v }));

  const onSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const payload: PortfolioCreate = {
      ...form,
      technologies: parseList(tech),
      skills: parseList(skills),
      features: parseList(features),
      outcomes: parseList(outcomes),
    };

    if (isEdit) {
      update.mutate(payload, {
        onSuccess: () => {
          toast.success("Portfolio updated");
          navigate("/portfolio");
        },
        onError: () => toast.error("Could not save"),
      });
    } else {
      create.mutate(payload, {
        onSuccess: () => {
          toast.success("Portfolio created");
          navigate("/portfolio");
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
        {isEdit ? "Edit project" : "New project"}
      </h1>

      <Card>
        <CardHeader>
          <CardTitle>Project details</CardTitle>
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
              <div className="space-y-2 md:col-span-2">
                <Label htmlFor="short">Short description</Label>
                <Input
                  id="short"
                  value={form.short_description ?? ""}
                  onChange={(e) => set("short_description", e.target.value)}
                  placeholder="One-liner used on listings and cards"
                />
              </div>
              <div className="space-y-2 md:col-span-2">
                <Label htmlFor="long">Long description</Label>
                <Textarea
                  id="long"
                  rows={6}
                  value={form.long_description}
                  required
                  onChange={(e) => set("long_description", e.target.value)}
                  placeholder="What you built, how, and the context."
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="role">Your role</Label>
                <Input
                  id="role"
                  value={form.role ?? ""}
                  onChange={(e) => set("role", e.target.value)}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="domain">Business domain</Label>
                <Input
                  id="domain"
                  value={form.business_domain ?? ""}
                  onChange={(e) => set("business_domain", e.target.value)}
                  placeholder="Enterprise SaaS, FinTech, Document Management…"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="github">GitHub URL</Label>
                <Input
                  id="github"
                  type="url"
                  value={form.github_url ?? ""}
                  onChange={(e) => set("github_url", e.target.value)}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="live">Live URL</Label>
                <Input
                  id="live"
                  type="url"
                  value={form.live_url ?? ""}
                  onChange={(e) => set("live_url", e.target.value)}
                />
              </div>
              <div className="space-y-2 md:col-span-2">
                <Label htmlFor="tech">Technologies (comma-separated)</Label>
                <Input
                  id="tech"
                  value={tech}
                  onChange={(e) => setTech(e.target.value)}
                  placeholder="PostgreSQL, FastAPI, Docker"
                />
              </div>
              <div className="space-y-2 md:col-span-2">
                <Label htmlFor="skills">Skills (comma-separated)</Label>
                <Input
                  id="skills"
                  value={skills}
                  onChange={(e) => setSkills(e.target.value)}
                  placeholder="Data modeling, Analytics, Compliance"
                />
              </div>
              <div className="space-y-2 md:col-span-2">
                <Label htmlFor="features">Features (one per line or comma-separated)</Label>
                <Textarea
                  id="features"
                  rows={3}
                  value={features}
                  onChange={(e) => setFeatures(e.target.value)}
                />
              </div>
              <div className="space-y-2 md:col-span-2">
                <Label htmlFor="outcomes">Outcomes (one per line or comma-separated)</Label>
                <Textarea
                  id="outcomes"
                  rows={3}
                  value={outcomes}
                  onChange={(e) => setOutcomes(e.target.value)}
                />
              </div>
              <label className="flex items-center gap-2 text-sm md:col-span-2">
                <input
                  type="checkbox"
                  checked={form.highlight ?? false}
                  onChange={(e) => set("highlight", e.target.checked)}
                />
                Highlight this project (appears at the top of the list)
              </label>
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <Button type="button" variant="outline" onClick={() => navigate("/portfolio")}>
                Cancel
              </Button>
              <Button type="submit" disabled={create.isPending || update.isPending}>
                {isEdit ? "Save changes" : "Create project"}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
