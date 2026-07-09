import { Pencil, Plus, Search, Star, Trash2 } from "lucide-react";
import { useState } from "react";
import { Link } from "react-router-dom";
import { toast } from "sonner";

import { Badge } from "@/shared/ui/badge";
import { Button } from "@/shared/ui/button";
import { Card, CardContent } from "@/shared/ui/card";
import { Input } from "@/shared/ui/input";
import { useDeletePortfolio, usePortfolioList } from "@/lib/portfolio";

export function PortfolioPage() {
  const [search, setSearch] = useState("");
  const [domain, setDomain] = useState("");

  const { data, isLoading } = usePortfolioList({ search, domain });
  const del = useDeletePortfolio();

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Portfolio</h1>
          <p className="text-sm text-muted-foreground">
            Projects you can reference in proposals. Used to match against analyzed jobs.
          </p>
        </div>
        <Button asChild>
          <Link to="/portfolio/new">
            <Plus className="mr-2 h-4 w-4" />
            New project
          </Link>
        </Button>
      </div>

      <div className="flex flex-wrap items-center gap-2">
        <div className="relative max-w-sm flex-1">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search title / description…"
            className="pl-9"
          />
        </div>
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
            No portfolio projects yet. Click <span className="font-medium">New project</span> or run
            <code className="ml-1 rounded bg-muted px-1.5 py-0.5">make seed</code> to insert demo
            projects.
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-3 md:grid-cols-2">
          {data.items.map((p) => (
            <Card key={p.id} className="overflow-hidden">
              <CardContent className="space-y-3 p-5">
                <div className="flex items-start justify-between gap-2">
                  <div className="min-w-0">
                    <Link
                      to={`/portfolio/${p.id}`}
                      className="block truncate text-base font-medium hover:underline"
                    >
                      {p.title}
                    </Link>
                    {p.role && (
                      <div className="text-xs text-muted-foreground">{p.role}</div>
                    )}
                  </div>
                  {p.highlight && (
                    <Star className="h-4 w-4 shrink-0 fill-amber-400 text-amber-400" />
                  )}
                </div>
                {p.short_description && (
                  <p className="text-sm text-muted-foreground">{p.short_description}</p>
                )}
                <div className="flex flex-wrap gap-1.5">
                  {p.business_domain && (
                    <Badge variant="secondary">{p.business_domain}</Badge>
                  )}
                  {p.technologies.slice(0, 4).map((t) => (
                    <Badge key={t} variant="outline">
                      {t}
                    </Badge>
                  ))}
                  {p.technologies.length > 4 && (
                    <Badge variant="outline">+{p.technologies.length - 4}</Badge>
                  )}
                </div>
                <div className="flex justify-end gap-1 pt-1">
                  <Button asChild size="sm" variant="ghost">
                    <Link to={`/portfolio/${p.id}`}>
                      <Pencil className="mr-1 h-3.5 w-3.5" />
                      Edit
                    </Link>
                  </Button>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => {
                      if (!confirm(`Delete "${p.title}"?`)) return;
                      del.mutate(p.id, {
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
