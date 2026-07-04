import { useState } from "react";
import { Link } from "react-router-dom";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { useAdminUsers } from "@/lib/admin";
import { cn } from "@/lib/utils";

export function AdminUsersPage() {
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const size = 25;
  const { data, isLoading } = useAdminUsers({ search, page, size });

  const totalPages = data ? Math.max(1, Math.ceil(data.total / size)) : 1;

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-2xl font-semibold">Users</h1>
        <p className="text-sm text-muted-foreground">
          {data ? `${data.total.toLocaleString()} total` : "—"}
        </p>
      </div>

      <div className="flex gap-2">
        <Input
          placeholder="Search by email or name…"
          value={search}
          onChange={(e) => {
            setSearch(e.target.value);
            setPage(1);
          }}
          className="max-w-sm"
        />
      </div>

      <Card>
        <CardContent className="p-0">
          {isLoading ? (
            <div className="p-6 text-sm text-muted-foreground">Loading…</div>
          ) : !data || data.items.length === 0 ? (
            <div className="p-6 text-sm text-muted-foreground">No users found.</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b bg-muted/30 text-xs uppercase text-muted-foreground">
                    <Th>Email</Th>
                    <Th>Name</Th>
                    <Th>Persona</Th>
                    <Th>Status</Th>
                    <Th>Wizard</Th>
                    <Th>LinkedIn</Th>
                    <Th>GitHub</Th>
                    <Th>Last login</Th>
                    <Th>Joined</Th>
                  </tr>
                </thead>
                <tbody>
                  {data.items.map((u) => (
                    <tr key={u.id} className="border-b hover:bg-muted/30">
                      <Td>
                        <Link
                          to={`/admin/users/${u.id}`}
                          className="text-primary hover:underline"
                        >
                          {u.email}
                        </Link>
                        {u.is_superuser && (
                          <span className="ml-1 rounded bg-primary/10 px-1 text-[10px] font-semibold uppercase text-primary">
                            Super
                          </span>
                        )}
                      </Td>
                      <Td>{u.full_name ?? "—"}</Td>
                      <Td className="capitalize">{u.persona_kind}</Td>
                      <Td>
                        <StatusBadge active={u.is_active} verified={u.email_verified} />
                      </Td>
                      <Td>
                        {u.persona_kind === "student" ? (
                          <span className="text-xs text-muted-foreground">
                            {u.wizard_completed}/11
                            {u.wizard_step ? ` · ${u.wizard_step}` : ""}
                          </span>
                        ) : (
                          "—"
                        )}
                      </Td>
                      <Td><PresenceBadge value={u.has_linkedin} /></Td>
                      <Td><PresenceBadge value={u.has_github} /></Td>
                      <Td className="whitespace-nowrap">
                        {u.last_login_at ? fmtRelative(u.last_login_at) : "—"}
                      </Td>
                      <Td className="whitespace-nowrap">{fmtDate(u.created_at)}</Td>
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

function PresenceBadge({ value }: { value: boolean | null }) {
  if (value === null) return <span className="text-xs text-muted-foreground">—</span>;
  if (value)
    return (
      <span className="rounded bg-primary/10 px-1.5 py-0.5 text-[10px] font-semibold uppercase text-primary">
        Yes
      </span>
    );
  return (
    <span className="rounded bg-muted px-1.5 py-0.5 text-[10px] font-semibold uppercase text-muted-foreground">
      No
    </span>
  );
}

function StatusBadge({ active, verified }: { active: boolean; verified: boolean }) {
  if (!active)
    return (
      <span className="rounded bg-destructive/10 px-1.5 py-0.5 text-[10px] font-semibold uppercase text-destructive">
        Disabled
      </span>
    );
  return (
    <span className="rounded bg-primary/10 px-1.5 py-0.5 text-[10px] font-semibold uppercase text-primary">
      {verified ? "Active" : "Unverified"}
    </span>
  );
}

function fmtDate(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleDateString();
}

function fmtRelative(iso: string): string {
  const d = new Date(iso);
  const diff = (Date.now() - d.getTime()) / 1000;
  if (diff < 60) return "just now";
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
  if (diff < 86400 * 30) return `${Math.floor(diff / 86400)}d ago`;
  return d.toLocaleDateString();
}
