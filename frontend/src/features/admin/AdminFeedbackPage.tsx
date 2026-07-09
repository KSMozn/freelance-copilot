import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { toast } from "sonner";

import { Button } from "@/shared/ui/button";
import { Card, CardContent } from "@/shared/ui/card";
import { Select } from "@/shared/ui/select";
import {
  useAdminFeedback,
  useAdminResolveFeedback,
  useAdminUnresolveFeedback,
} from "@/lib/admin";
import { cn } from "@/shared/lib/utils";
import type { AdminFeedbackItem } from "@/types/admin";

const KIND_OPTIONS = [
  { value: "", label: "All kinds" },
  { value: "general", label: "General" },
  { value: "post_download", label: "Post-download survey" },
];

const RESOLVED_OPTIONS = [
  { value: "unresolved", label: "Open" },
  { value: "resolved", label: "Resolved" },
  { value: "all", label: "All" },
];

export function AdminFeedbackPage() {
  const [kind, setKind] = useState<string>("");
  const [resolvedFilter, setResolvedFilter] = useState<string>("unresolved");
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const resolvedParam =
    resolvedFilter === "resolved"
      ? true
      : resolvedFilter === "unresolved"
        ? false
        : undefined;

  const { data, isLoading } = useAdminFeedback({
    kind: kind || undefined,
    resolved: resolvedParam,
  });
  const resolve = useAdminResolveFeedback();
  const unresolve = useAdminUnresolveFeedback();

  const selected = useMemo(
    () => data?.items.find((i) => i.id === selectedId) ?? null,
    [data, selectedId],
  );

  async function handleResolve(id: string) {
    try {
      await resolve.mutateAsync(id);
      toast.success("Marked resolved");
    } catch {
      toast.error("Could not resolve");
    }
  }

  async function handleUnresolve(id: string) {
    try {
      await unresolve.mutateAsync(id);
      toast.success("Reopened");
    } catch {
      toast.error("Could not reopen");
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex items-baseline justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Feedback</h1>
          <p className="text-sm text-muted-foreground">
            Every free-text feedback + post-download survey rating, newest first.
            {data && ` ${data.total.toLocaleString()} shown.`}
          </p>
        </div>
        {data && data.unresolved_count > 0 && (
          <div className="rounded-md bg-primary/10 px-3 py-1.5 text-xs font-medium text-primary">
            {data.unresolved_count} open
          </div>
        )}
      </div>

      <div className="flex flex-wrap gap-2">
        <div className="w-52">
          <Select
            value={kind}
            onChange={(e) => setKind(e.target.value)}
            options={KIND_OPTIONS}
            placeholder="All kinds"
          />
        </div>
        <div className="w-40">
          <Select
            value={resolvedFilter}
            onChange={(e) => setResolvedFilter(e.target.value)}
            options={RESOLVED_OPTIONS}
          />
        </div>
      </div>

      <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_360px]">
        <Card>
          <CardContent className="p-0">
            {isLoading ? (
              <div className="p-6 text-sm text-muted-foreground">Loading…</div>
            ) : !data || data.items.length === 0 ? (
              <div className="p-6 text-sm text-muted-foreground">
                No matching feedback.
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-xs">
                  <thead>
                    <tr className="border-b bg-muted/30 uppercase text-muted-foreground">
                      <Th>When</Th>
                      <Th>User</Th>
                      <Th>Kind</Th>
                      <Th>Rating</Th>
                      <Th>Message</Th>
                      <Th>Status</Th>
                      <Th />
                    </tr>
                  </thead>
                  <tbody>
                    {data.items.map((r) => (
                      <tr
                        key={r.id}
                        className={cn(
                          "cursor-pointer border-b align-top hover:bg-muted/40",
                          selectedId === r.id && "bg-muted/60",
                        )}
                        onClick={() => setSelectedId(r.id)}
                      >
                        <Td className="whitespace-nowrap">
                          {new Date(r.created_at).toLocaleString()}
                        </Td>
                        <Td className="whitespace-nowrap">
                          {r.user_email ? (
                            <Link
                              to={`/users/${r.user_id}`}
                              className="text-primary hover:underline"
                              onClick={(e) => e.stopPropagation()}
                            >
                              {r.user_email}
                            </Link>
                          ) : (
                            <span className="text-muted-foreground">
                              deleted user
                            </span>
                          )}
                        </Td>
                        <Td className="whitespace-nowrap">
                          <span className="font-mono">{r.kind}</span>
                        </Td>
                        <Td>{r.rating !== null ? `${r.rating}/5` : "—"}</Td>
                        <Td className="max-w-md">
                          <div className="line-clamp-2 text-muted-foreground">
                            {r.message ?? (
                              <span className="italic">(no comment)</span>
                            )}
                          </div>
                        </Td>
                        <Td className="whitespace-nowrap">
                          <StatusBadge item={r} />
                        </Td>
                        <Td className="whitespace-nowrap">
                          {r.resolved_at ? (
                            <button
                              type="button"
                              onClick={(e) => {
                                e.stopPropagation();
                                void handleUnresolve(r.id);
                              }}
                              className="text-[11px] text-muted-foreground hover:text-foreground"
                            >
                              Reopen
                            </button>
                          ) : (
                            <button
                              type="button"
                              onClick={(e) => {
                                e.stopPropagation();
                                void handleResolve(r.id);
                              }}
                              className="text-[11px] text-primary hover:underline"
                            >
                              Resolve
                            </button>
                          )}
                        </Td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </CardContent>
        </Card>

        <DetailPanel
          item={selected}
          onResolve={handleResolve}
          onUnresolve={handleUnresolve}
        />
      </div>
    </div>
  );
}

function StatusBadge({ item }: { item: AdminFeedbackItem }) {
  if (item.resolved_at) {
    return (
      <span className="rounded bg-emerald-500/10 px-1.5 py-0.5 text-[10px] font-semibold uppercase text-emerald-600 dark:text-emerald-400">
        Resolved
      </span>
    );
  }
  return (
    <span className="rounded bg-amber-500/10 px-1.5 py-0.5 text-[10px] font-semibold uppercase text-amber-600 dark:text-amber-400">
      Open
    </span>
  );
}

function DetailPanel({
  item,
  onResolve,
  onUnresolve,
}: {
  item: AdminFeedbackItem | null;
  onResolve: (id: string) => Promise<void>;
  onUnresolve: (id: string) => Promise<void>;
}) {
  if (!item) {
    return (
      <Card className="hidden lg:block">
        <CardContent className="p-4 text-xs text-muted-foreground">
          Select a row to see the full message + user context.
        </CardContent>
      </Card>
    );
  }
  return (
    <Card>
      <CardContent className="space-y-3 p-4 text-xs">
        <div className="flex items-start justify-between gap-2">
          <div>
            <div className="font-semibold uppercase text-muted-foreground">
              {item.kind === "general" ? "Feedback" : "Post-download survey"}
            </div>
            <div className="mt-0.5 text-[11px] text-muted-foreground">
              {new Date(item.created_at).toLocaleString()}
            </div>
          </div>
          <StatusBadge item={item} />
        </div>

        <div>
          <div className="uppercase text-muted-foreground">From</div>
          {item.user_email ? (
            <Link
              to={`/users/${item.user_id}`}
              className="text-sm text-primary hover:underline"
            >
              {item.user_full_name ?? item.user_email}
            </Link>
          ) : (
            <div className="text-sm italic text-muted-foreground">
              deleted user
            </div>
          )}
          {item.user_email && item.user_full_name && (
            <div className="text-[11px] text-muted-foreground">
              {item.user_email}
            </div>
          )}
        </div>

        {item.rating !== null && (
          <div>
            <div className="uppercase text-muted-foreground">Rating</div>
            <div className="text-sm">
              {"★".repeat(item.rating)}
              <span className="text-muted-foreground">
                {"★".repeat(5 - item.rating)}
              </span>{" "}
              <span className="text-[11px] text-muted-foreground">
                ({item.rating}/5)
              </span>
            </div>
          </div>
        )}

        {item.template_slug && (
          <div>
            <div className="uppercase text-muted-foreground">Template</div>
            <div className="text-sm font-mono">{item.template_slug}</div>
          </div>
        )}

        <div>
          <div className="uppercase text-muted-foreground">Message</div>
          {item.message ? (
            <div className="whitespace-pre-wrap rounded-md border bg-muted/30 p-2 text-sm">
              {item.message}
            </div>
          ) : (
            <div className="italic text-muted-foreground">(no comment)</div>
          )}
        </div>

        {item.resolved_at && (
          <div className="rounded-md border bg-muted/30 p-2 text-[11px] text-muted-foreground">
            Resolved {new Date(item.resolved_at).toLocaleString()}
            {item.resolved_by_email && ` by ${item.resolved_by_email}`}
          </div>
        )}

        <div className="flex gap-2 pt-1">
          {item.resolved_at ? (
            <Button
              size="sm"
              variant="outline"
              onClick={() => void onUnresolve(item.id)}
            >
              Reopen
            </Button>
          ) : (
            <Button size="sm" onClick={() => void onResolve(item.id)}>
              Mark resolved
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

function Th({ children }: { children?: React.ReactNode }) {
  return <th className="px-3 py-2 text-left font-medium">{children}</th>;
}

function Td({
  children,
  className,
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return <td className={cn("px-3 py-2", className)}>{children}</td>;
}
