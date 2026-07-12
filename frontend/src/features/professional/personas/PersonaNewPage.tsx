import { ArrowLeft, Check } from "lucide-react";
import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { toast } from "sonner";

import { Button } from "@/shared/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/shared/ui/card";
import { Input } from "@/shared/ui/input";
import { Label } from "@/shared/ui/label";
import {
  useCreatePersona,
  usePersonaArchetypes,
  type PersonaArchetype,
} from "@/features/professional/personas/personasApi";

export function PersonaNewPage() {
  const navigate = useNavigate();
  const { data: archetypes, isLoading } = usePersonaArchetypes();
  const create = useCreatePersona();
  const [step, setStep] = useState<1 | 2>(1);
  const [archetype, setArchetype] = useState<PersonaArchetype | null>(null);
  const [name, setName] = useState("");
  const [targetRole, setTargetRole] = useState("");

  function pick(a: PersonaArchetype) {
    setArchetype(a);
    setName(a.name);
    setTargetRole(a.default_target_roles[0] ?? "");
    setStep(2);
  }

  function submit() {
    if (!archetype) return;
    create.mutate(
      {
        archetype_slug: archetype.slug,
        name: name.trim() || archetype.name,
        target_role: targetRole.trim() || null,
        is_default: false,
      },
      {
        onSuccess: (p) => {
          toast.success(`Persona “${p.name}” created`);
          navigate("/personas");
        },
        onError: (err: unknown) => {
          const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data
            ?.detail;
          toast.error(detail ?? "Could not create persona");
        },
      },
    );
  }

  return (
    <div className="max-w-4xl space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">New persona</h1>
          <p className="text-sm text-muted-foreground">
            Step {step} of 2 — {step === 1 ? "pick an archetype" : "name + target role"}
          </p>
        </div>
        <Button variant="ghost" asChild>
          <Link to="/personas">
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back to personas
          </Link>
        </Button>
      </div>

      {step === 1 && (
        <>
          {isLoading && <p className="text-sm text-muted-foreground">Loading archetypes…</p>}
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {(archetypes ?? []).map((a) => (
              <Card
                key={a.id}
                className="cursor-pointer transition hover:border-primary"
                onClick={() => pick(a)}
              >
                <CardHeader>
                  <CardTitle className="text-base">{a.name}</CardTitle>
                  <CardDescription className="line-clamp-3">{a.description}</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-1 text-xs text-muted-foreground">
                    <div>
                      <strong>Tone:</strong>{" "}
                      <span className="capitalize">
                        {a.default_proposal_tone.replace("_", " ")}
                      </span>
                    </div>
                    {a.default_seniority_band && (
                      <div>
                        <strong>Seniority:</strong> {a.default_seniority_band}
                      </div>
                    )}
                    {a.default_target_roles.length > 0 && (
                      <div className="pt-1">
                        <strong>Roles:</strong> {a.default_target_roles.slice(0, 2).join(", ")}
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </>
      )}

      {step === 2 && archetype && (
        <Card className="max-w-xl">
          <CardHeader>
            <CardTitle>{archetype.name}</CardTitle>
            <CardDescription>{archetype.description}</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="name">Persona name</Label>
              <Input
                id="name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder={archetype.name}
                maxLength={120}
                autoFocus
              />
              <p className="text-xs text-muted-foreground">
                A friendly label you'll see in the persona switcher. Must be unique across your
                personas.
              </p>
            </div>
            <div className="space-y-2">
              <Label htmlFor="target_role">Target role (optional)</Label>
              <Input
                id="target_role"
                value={targetRole}
                onChange={(e) => setTargetRole(e.target.value)}
                placeholder={archetype.default_target_roles[0] ?? ""}
                maxLength={255}
              />
              <p className="text-xs text-muted-foreground">
                The job titles you're targeting under this persona — feeds the match score and
                tailored outputs.
              </p>
            </div>
            <div className="flex justify-end gap-2">
              <Button variant="outline" onClick={() => setStep(1)}>
                Back
              </Button>
              <Button onClick={submit} disabled={create.isPending}>
                <Check className="mr-2 h-4 w-4" />
                {create.isPending ? "Creating…" : "Create persona"}
              </Button>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
