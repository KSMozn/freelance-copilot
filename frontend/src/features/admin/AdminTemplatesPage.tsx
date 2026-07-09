import { useState } from "react";
import { toast } from "sonner";

import { Card, CardContent } from "@/shared/ui/card";
import { Input } from "@/shared/ui/input";
import { useAdminCvTemplates, useUpdateAdminCvTemplate } from "@/features/admin/adminApi";

export function AdminTemplatesPage() {
  const { data, isLoading } = useAdminCvTemplates();
  const update = useUpdateAdminCvTemplate();
  // Track which slug's sort-order input is currently being edited so we
  // can debounce the save on blur rather than on every keystroke.
  const [pendingOrder, setPendingOrder] = useState<Record<string, string>>({});

  async function toggleVisible(slug: string, next: boolean) {
    try {
      await update.mutateAsync({ slug, payload: { is_visible: next } });
      toast.success(next ? "Template made visible" : "Template hidden");
    } catch {
      toast.error("Couldn't update template");
    }
  }

  async function commitSort(slug: string) {
    const raw = pendingOrder[slug];
    if (raw === undefined) return;
    const n = Number(raw);
    if (!Number.isFinite(n) || n < 0) {
      toast.error("Sort order must be a non-negative number");
      return;
    }
    try {
      await update.mutateAsync({ slug, payload: { sort_order: n } });
      setPendingOrder((prev) => {
        const next = { ...prev };
        delete next[slug];
        return next;
      });
      toast.success("Sort order saved");
    } catch {
      toast.error("Couldn't save sort order");
    }
  }

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-2xl font-semibold">CV Templates</h1>
        <p className="text-sm text-muted-foreground">
          Toggle visibility to show or hide a template in the student
          wizard. Sort order controls display order in the picker
          (lowest first) — the first visible template is also the
          fallback for students who haven't picked one.
        </p>
      </div>

      <Card>
        <CardContent className="p-0">
          {isLoading ? (
            <div className="p-6 text-sm text-muted-foreground">Loading…</div>
          ) : !data || data.items.length === 0 ? (
            <div className="p-6 text-sm text-muted-foreground">
              No templates found. Run the phase-L migration to seed them.
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b bg-muted/30 text-xs uppercase text-muted-foreground">
                    <Th>Name</Th>
                    <Th>Slug</Th>
                    <Th>Description</Th>
                    <Th>Visible</Th>
                    <Th>Sort</Th>
                  </tr>
                </thead>
                <tbody>
                  {data.items.map((t) => (
                    <tr key={t.slug} className="border-b last:border-none">
                      <Td>
                        <div className="font-medium">{t.display_name}</div>
                      </Td>
                      <Td>
                        <code className="text-xs text-muted-foreground">
                          {t.slug}
                        </code>
                      </Td>
                      <Td>
                        <div className="max-w-md text-xs text-muted-foreground">
                          {t.description}
                        </div>
                      </Td>
                      <Td>
                        <label className="inline-flex cursor-pointer items-center gap-2">
                          <input
                            type="checkbox"
                            className="h-4 w-4"
                            checked={t.is_visible}
                            disabled={update.isPending}
                            onChange={(e) =>
                              void toggleVisible(t.slug, e.target.checked)
                            }
                          />
                          <span
                            className={
                              t.is_visible
                                ? "text-xs font-medium text-primary"
                                : "text-xs text-muted-foreground"
                            }
                          >
                            {t.is_visible ? "Visible" : "Hidden"}
                          </span>
                        </label>
                      </Td>
                      <Td>
                        <Input
                          type="number"
                          min={0}
                          value={pendingOrder[t.slug] ?? String(t.sort_order)}
                          onChange={(e) =>
                            setPendingOrder((prev) => ({
                              ...prev,
                              [t.slug]: e.target.value,
                            }))
                          }
                          onBlur={() => void commitSort(t.slug)}
                          onKeyDown={(e) => {
                            if (e.key === "Enter") {
                              e.currentTarget.blur();
                            }
                          }}
                          className="h-8 w-24"
                          disabled={update.isPending}
                        />
                      </Td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

function Th({ children }: { children: React.ReactNode }) {
  return <th className="px-3 py-2 text-left font-medium">{children}</th>;
}

function Td({ children }: { children: React.ReactNode }) {
  return <td className="px-3 py-2 align-top">{children}</td>;
}
