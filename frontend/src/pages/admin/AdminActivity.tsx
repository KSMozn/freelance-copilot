import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Select } from "@/components/ui/select";
import { useAdminActivity } from "@/lib/admin";
import { cn } from "@/lib/utils";

const KIND_OPTIONS = [
  { value: "", label: "All kinds" },
  { value: "coach.draft_summary", label: "coach.draft_summary" },
  { value: "coach.proofread", label: "coach.proofread" },
  { value: "coach.photo", label: "coach.photo" },
  { value: "coach.text", label: "coach.text" },
  { value: "coach.internship", label: "coach.internship" },
  { value: "cv.pdf", label: "cv.pdf" },
  { value: "cv.preview", label: "cv.preview" },
  { value: "admin.action", label: "admin.action" },
  { value: "admin.impersonate", label: "admin.impersonate" },
  { value: "error", label: "error" },
];

const STATUS_OPTIONS = [
  { value: "", label: "Any status" },
  { value: "ok", label: "ok" },
  { value: "error", label: "error" },
];

export function AdminActivityPage() {
  const [kind, setKind] = useState<string>("");
  const [status, setStatus] = useState<string>("");
  const [page, setPage] = useState(1);
  const size = 50;
  const { data, isLoading } = useAdminActivity({
    kind: kind || undefined,
    status: status || undefined,
    page,
    size,
  });
  const totalPages = data ? Math.max(1, Math.ceil(data.total / size)) : 1;

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-2xl font-semibold">Activity</h1>
        <p className="text-sm text-muted-foreground">
          Every meaningful call and admin action, newest first.
          {data && ` ${data.total.toLocaleString()} matching.`}
        </p>
      </div>

      <div className="flex flex-wrap gap-2">
        <div className="w-52">
          <Select
            value={kind}
            onChange={(e) => {
              setKind(e.target.value);
              setPage(1);
            }}
            options={KIND_OPTIONS}
            placeholder="All kinds"
          />
        </div>
        <div className="w-40">
          <Select
            value={status}
            onChange={(e) => {
              setStatus(e.target.value);
              setPage(1);
            }}
            options={STATUS_OPTIONS}
            placeholder="Any status"
          />
        </div>
      </div>

      <Card>
        <CardContent className="p-0">
          {isLoading ? (
            <div className="p-6 text-sm text-muted-foreground">Loading…</div>
          ) : !data || data.items.length === 0 ? (
            <div className="p-6 text-sm text-muted-foreground">
              No matching events.
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-xs">
                <thead>
                  <tr className="border-b bg-muted/30 uppercase text-muted-foreground">
                    <Th>When</Th>
                    <Th>Kind</Th>
                    <Th>Status</Th>
                    <Th>User</Th>
                    <Th>Duration</Th>
                    <Th>Details</Th>
                  </tr>
                </thead>
                <tbody>
                  {data.items.map((r) => (
                    <tr key={r.id} className="border-b align-top hover:bg-muted/30">
                      <Td className="whitespace-nowrap">
                        {new Date(r.created_at).toLocaleString()}
                      </Td>
                      <Td>
                        <span className="font-mono">{r.kind}</span>
                      </Td>
                      <Td>
                        <span
                          className={cn(
                            "rounded px-1.5 py-0.5 text-[10px] font-semibold uppercase",
                            r.status === "error"
                              ? "bg-destructive/10 text-destructive"
                              : "bg-primary/10 text-primary",
                          )}
                        >
                          {r.status}
                        </span>
                      </Td>
                      <Td>{r.user_email ?? "—"}</Td>
                      <Td>
                        {r.duration_ms !== null
                          ? `${r.duration_ms}ms`
                          : "—"}
                      </Td>
                      <Td className="max-w-md">
                        {r.error_message && (
                          <div className="whitespace-pre-wrap text-destructive">
                            {r.error_message}
                          </div>
                        )}
                        {Object.keys(r.meta).length > 0 && (
                          <div className="whitespace-pre-wrap text-muted-foreground">
                            {JSON.stringify(r.meta)}
                          </div>
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

      {data && data.total > size && (
        <div className="flex items-center justify-between">
          <div className="text-xs text-muted-foreground">
            Page {page} of {totalPages}
          </div>
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page === 1}
            >
              Previous
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              disabled={page === totalPages}
            >
              Next
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}

function Th({ children }: { children: React.ReactNode }) {
  return <th className="px-3 py-2 text-left font-medium">{children}</th>;
}

function Td({ children, className }: { children: React.ReactNode; className?: string }) {
  return <td className={cn("px-3 py-2", className)}>{children}</td>;
}
