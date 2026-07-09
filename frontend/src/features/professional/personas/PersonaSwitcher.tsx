import { Check, ChevronDown, Plus, UserCog } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";

import { Button } from "@/shared/ui/button";
import {
  useCurrentPersona,
  usePersonas,
  useSetDefaultPersona,
} from "@/features/professional/personas/personasApi";
import { useAuthStore } from "@/features/auth/authStore";

export function PersonaSwitcher() {
  const navigate = useNavigate();
  const setActivePersonaId = useAuthStore((s) => s.setActivePersonaId);
  const activePersonaId = useAuthStore((s) => s.activePersonaId);
  const { data: current } = useCurrentPersona();
  const { data: personas } = usePersonas();
  const setDefault = useSetDefaultPersona();
  const [open, setOpen] = useState(false);
  const wrapperRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    function onDoc(e: MouseEvent) {
      if (!wrapperRef.current?.contains(e.target as Node)) setOpen(false);
    }
    document.addEventListener("mousedown", onDoc);
    return () => document.removeEventListener("mousedown", onDoc);
  }, [open]);

  // active = explicit store value, falling back to the server-side default
  const activeId = activePersonaId ?? current?.id ?? null;
  const active = personas?.find((p) => p.id === activeId) ?? current ?? null;
  const list = (personas ?? []).filter((p) => !p.is_archived);

  return (
    <div className="relative" ref={wrapperRef}>
      <Button variant="ghost" size="sm" onClick={() => setOpen((o) => !o)} className="gap-2">
        <UserCog className="h-4 w-4" />
        <span className="hidden max-w-[140px] truncate sm:inline">{active?.name ?? "Persona"}</span>
        <ChevronDown className="h-3 w-3" />
      </Button>
      {open && (
        <div className="bg-popover absolute right-0 z-50 mt-2 w-72 rounded-md border p-1 shadow-md">
          <div className="px-3 py-2 text-xs text-muted-foreground">Acting as</div>
          {list.length === 0 && (
            <div className="px-3 py-2 text-sm text-muted-foreground">No personas yet</div>
          )}
          {list.map((p) => {
            const isActive = p.id === activeId;
            return (
              <button
                key={p.id}
                type="button"
                onClick={() => {
                  setActivePersonaId(p.id);
                  // Persist the choice server-side so reload still shows it.
                  if (!isActive) setDefault.mutate(p.id);
                  setOpen(false);
                }}
                className="flex w-full items-center justify-between rounded-sm px-3 py-2 text-left text-sm hover:bg-accent"
              >
                <span className="flex flex-col">
                  <span className="font-medium">{p.name}</span>
                  {p.target_role && (
                    <span className="text-xs text-muted-foreground">{p.target_role}</span>
                  )}
                </span>
                {isActive && <Check className="h-4 w-4 text-primary" />}
              </button>
            );
          })}
          <div className="my-1 border-t" />
          <button
            type="button"
            onClick={() => {
              setOpen(false);
              navigate("/personas/new");
            }}
            className="flex w-full items-center gap-2 rounded-sm px-3 py-2 text-left text-sm hover:bg-accent"
          >
            <Plus className="h-4 w-4" />
            New persona
          </button>
          <button
            type="button"
            onClick={() => {
              setOpen(false);
              navigate("/personas");
            }}
            className="flex w-full items-center gap-2 rounded-sm px-3 py-2 text-left text-sm hover:bg-accent"
          >
            <UserCog className="h-4 w-4" />
            Manage personas
          </button>
        </div>
      )}
    </div>
  );
}
