import { Plus, Star, Trash2 } from "lucide-react";
import { Link } from "react-router-dom";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { useDeletePersona, usePersonas, useSetDefaultPersona } from "@/lib/personas";

export function PersonasPage() {
  const { data: personas, isLoading } = usePersonas();
  const setDefault = useSetDefaultPersona();
  const deletePersona = useDeletePersona();

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Personas</h1>
          <p className="text-sm text-muted-foreground">
            Lenses over your knowledge graph. Each persona shapes how the
            system weighs your skills, picks portfolio highlights, and tunes
            generated outputs.
          </p>
        </div>
        <Button asChild>
          <Link to="/personas/new">
            <Plus className="h-4 w-4 mr-2" />
            New persona
          </Link>
        </Button>
      </div>

      {isLoading && (
        <p className="text-sm text-muted-foreground">Loading personas…</p>
      )}

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {(personas ?? []).map((p) => (
          <Card key={p.id}>
            <CardHeader>
              <div className="flex items-start justify-between">
                <div>
                  <CardTitle className="text-base">{p.name}</CardTitle>
                  <CardDescription>
                    {p.target_role || "no target role set"}
                  </CardDescription>
                </div>
                {p.is_default && (
                  <span className="flex items-center gap-1 text-xs text-primary font-medium">
                    <Star className="h-3 w-3 fill-current" />
                    Default
                  </span>
                )}
              </div>
            </CardHeader>
            <CardContent className="space-y-2">
              <div className="text-xs text-muted-foreground">
                {p.target_seniority && (
                  <span className="capitalize">{p.target_seniority}</span>
                )}
                {p.proposal_tone && (
                  <>
                    {" · "}
                    <span className="capitalize">
                      {p.proposal_tone.replace("_", " ")}
                    </span>
                  </>
                )}
              </div>
              <div className="flex gap-2 pt-2">
                {!p.is_default && (
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => setDefault.mutate(p.id)}
                    disabled={setDefault.isPending}
                  >
                    Make default
                  </Button>
                )}
                <Button
                  size="sm"
                  variant="ghost"
                  className="text-destructive ml-auto"
                  disabled={deletePersona.isPending}
                  onClick={() => {
                    if (!confirm(`Delete persona "${p.name}"?`)) return;
                    deletePersona.mutate(p.id, {
                      onError: (err: unknown) => {
                        const detail = (
                          err as { response?: { data?: { detail?: string } } }
                        )?.response?.data?.detail;
                        toast.error(detail ?? "Could not delete persona");
                      },
                    });
                  }}
                >
                  <Trash2 className="h-3 w-3" />
                </Button>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
