import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { api } from "@/lib/api";
import type { Job, JobCreate } from "@/types/api";

export function JobCreatePage() {
  const navigate = useNavigate();
  const qc = useQueryClient();
  const [form, setForm] = useState<JobCreate>({
    title: "",
    description: "",
    source_url: null,
    budget_type: null,
    budget_min: null,
    budget_max: null,
    currency: "USD",
    proposal_count: null,
  });

  const mutation = useMutation({
    mutationFn: async () => {
      const payload: Record<string, unknown> = { ...form };
      // strip empty optionals
      for (const k of Object.keys(payload)) {
        if (payload[k] === "" || payload[k] === null) delete payload[k];
      }
      payload.title = form.title;
      payload.description = form.description;
      payload.currency = form.currency || "USD";
      const { data } = await api.post<Job>("/jobs", payload);
      return data;
    },
    onSuccess: (job) => {
      qc.invalidateQueries({ queryKey: ["jobs"] });
      toast.success("Job imported");
      navigate(`/jobs/${job.id}`);
    },
    onError: () => toast.error("Could not import job"),
  });

  const set = <K extends keyof JobCreate>(k: K, v: JobCreate[K]) =>
    setForm((f) => ({ ...f, [k]: v }));

  return (
    <div className="mx-auto max-w-2xl space-y-4">
      <h1 className="text-2xl font-semibold tracking-tight">Import a job</h1>
      <p className="text-sm text-muted-foreground">
        Paste the job description below. Nothing is scraped from Upwork.
      </p>

      <Card>
        <CardHeader>
          <CardTitle>Job details</CardTitle>
        </CardHeader>
        <CardContent>
          <form
            className="space-y-4"
            onSubmit={(e) => {
              e.preventDefault();
              mutation.mutate();
            }}
          >
            <div className="space-y-2">
              <Label htmlFor="title">Title</Label>
              <Input
                id="title"
                required
                value={form.title}
                onChange={(e) => set("title", e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="description">Description</Label>
              <Textarea
                id="description"
                required
                rows={10}
                value={form.description}
                onChange={(e) => set("description", e.target.value)}
                placeholder="Paste the full job description here…"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="url">Source URL (optional)</Label>
              <Input
                id="url"
                type="url"
                value={form.source_url ?? ""}
                onChange={(e) => set("source_url", e.target.value || null)}
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="budget_type">Budget type</Label>
                <select
                  id="budget_type"
                  className="h-10 w-full rounded-md border border-input bg-background px-3 text-sm"
                  value={form.budget_type ?? ""}
                  onChange={(e) =>
                    set("budget_type", (e.target.value || null) as JobCreate["budget_type"])
                  }
                >
                  <option value="">—</option>
                  <option value="fixed">Fixed</option>
                  <option value="hourly">Hourly</option>
                </select>
              </div>
              <div className="space-y-2">
                <Label htmlFor="currency">Currency</Label>
                <Input
                  id="currency"
                  maxLength={3}
                  value={form.currency}
                  onChange={(e) => set("currency", e.target.value.toUpperCase())}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="budget_min">Budget min</Label>
                <Input
                  id="budget_min"
                  type="number"
                  step="0.01"
                  value={form.budget_min ?? ""}
                  onChange={(e) => set("budget_min", e.target.value ? Number(e.target.value) : null)}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="budget_max">Budget max</Label>
                <Input
                  id="budget_max"
                  type="number"
                  step="0.01"
                  value={form.budget_max ?? ""}
                  onChange={(e) => set("budget_max", e.target.value ? Number(e.target.value) : null)}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="proposals">Proposals</Label>
                <Input
                  id="proposals"
                  type="number"
                  value={form.proposal_count ?? ""}
                  onChange={(e) =>
                    set("proposal_count", e.target.value ? Number(e.target.value) : null)
                  }
                />
              </div>
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <Button type="button" variant="outline" onClick={() => navigate("/jobs")}>
                Cancel
              </Button>
              <Button type="submit" disabled={mutation.isPending}>
                {mutation.isPending ? "Importing…" : "Import job"}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
