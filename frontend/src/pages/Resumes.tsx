import { FileText, Pencil, Plus, Search, Trash2 } from "lucide-react";
import { useState } from "react";
import { Link } from "react-router-dom";
import { toast } from "sonner";

import { Badge } from "@/shared/ui/badge";
import { Button } from "@/shared/ui/button";
import { Card, CardContent } from "@/shared/ui/card";
import { Input } from "@/shared/ui/input";
import { useDeleteResume, useResumeList } from "@/lib/resumes";

export function ResumesPage() {
  const [search, setSearch] = useState("");
  const [skill, setSkill] = useState("");
  const [domain, setDomain] = useState("");
  const { data, isLoading } = useResumeList({ search, domain, skill });
  const del = useDeleteResume();

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Resumes</h1>
          <p className="text-sm text-muted-foreground">
            Structured resume profiles used to recommend the best fit per job.
          </p>
        </div>
        <Button asChild>
          <Link to="/resumes/new">
            <Plus className="mr-2 h-4 w-4" />
            New resume
          </Link>
        </Button>
      </div>

      <div className="flex flex-wrap items-center gap-2">
        <div className="relative max-w-sm flex-1">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search title / role / summary…"
            className="pl-9"
          />
        </div>
        <Input
          value={skill}
          onChange={(e) => setSkill(e.target.value)}
          placeholder="Filter by skill"
          className="max-w-xs"
        />
        <Input
          value={domain}
          onChange={(e) => setDomain(e.target.value)}
          placeholder="Filter by domain"
          className="max-w-xs"
        />
      </div>

      {isLoading ? (
        <div className="text-sm text-muted-foreground">Loading…</div>
      ) : !data?.items.length ? (
        <Card>
          <CardContent className="p-6 text-sm text-muted-foreground">
            No resume profiles yet. Click <span className="font-medium">New resume</span> or run
            <code className="ml-1 rounded bg-muted px-1.5 py-0.5">make seed</code> for five demo
            profiles.
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-3 md:grid-cols-2">
          {data.items.map((r) => (
            <Card key={r.id}>
              <CardContent className="space-y-3 p-5">
                <div className="flex items-start justify-between gap-2">
                  <div className="min-w-0">
                    <Link
                      to={`/resumes/${r.id}`}
                      className="flex items-center gap-2 text-base font-medium hover:underline"
                    >
                      <FileText className="h-4 w-4 shrink-0 text-muted-foreground" />
                      <span className="truncate">{r.title}</span>
                    </Link>
                    {r.target_role && (
                      <div className="text-xs text-muted-foreground">{r.target_role}</div>
                    )}
                  </div>
                  {r.seniority_level && (
                    <Badge variant="secondary" className="shrink-0">
                      {r.seniority_level}
                    </Badge>
                  )}
                </div>
                {r.summary && (
                  <p className="line-clamp-2 text-sm text-muted-foreground">{r.summary}</p>
                )}
                <div className="flex flex-wrap gap-1.5">
                  {r.primary_skills.slice(0, 6).map((s) => (
                    <Badge key={s} variant="outline">
                      {s}
                    </Badge>
                  ))}
                  {r.primary_skills.length > 6 && (
                    <Badge variant="outline">+{r.primary_skills.length - 6}</Badge>
                  )}
                </div>
                <div className="flex justify-end gap-1 pt-1">
                  <Button asChild size="sm" variant="ghost">
                    <Link to={`/resumes/${r.id}`}>
                      <Pencil className="mr-1 h-3.5 w-3.5" />
                      Edit
                    </Link>
                  </Button>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => {
                      if (!confirm(`Delete "${r.title}"?`)) return;
                      del.mutate(r.id, {
                        onSuccess: () => toast.success("Deleted"),
                        onError: () => toast.error("Could not delete"),
                      });
                    }}
                  >
                    <Trash2 className="mr-1 h-3.5 w-3.5" />
                    Delete
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
