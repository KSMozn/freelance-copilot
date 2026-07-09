import { useState } from "react";
import { Link } from "react-router-dom";

import { useAdminLlmCalls } from "@/features/admin/adminApi";
import type { LlmSpendSummary } from "@/features/admin/adminTypes";

/**
 * Reusable LLM spend card used on both the Overview page (all users)
 * and the user-detail page (single user). Renders total-stat header,
 * per-model breakdown table with click-to-expand call detail.
 *
 * `userId` when present scopes the drill-down `/admin/llm-calls` fetch
 * to that user so a click on a model row only lists that user's calls.
 */
export function LlmSpendCardBody({
  summary,
  userId,
  emptyMessage = "No LLM calls recorded in the selected window.",
}: {
  summary: LlmSpendSummary;
  userId?: string;
  emptyMessage?: string;
}) {
  if (summary.total_calls === 0) {
    return <div className="text-sm text-muted-foreground">{emptyMessage}</div>;
  }
  const totalTokens =
    summary.total_prompt_tokens + summary.total_completion_tokens;
  return (
    <div className="space-y-3">
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <Stat label="Calls" value={summary.total_calls.toLocaleString()} />
        <Stat label="Total tokens" value={totalTokens.toLocaleString()} />
        <Stat
          label="Prompt / completion"
          value={`${summary.total_prompt_tokens.toLocaleString()} / ${summary.total_completion_tokens.toLocaleString()}`}
          small
        />
        <Stat
          label="Est. cost"
          value={`$${summary.total_cost_usd.toFixed(4)}`}
        />
      </div>
      <ModelBreakdownTable models={summary.by_model} userId={userId} />
    </div>
  );
}

function ModelBreakdownTable({
  models,
  userId,
}: {
  models: LlmSpendSummary["by_model"];
  userId?: string;
}) {
  const [expandedModel, setExpandedModel] = useState<string | null>(null);
  return (
    <div className="text-sm">
      <div className="grid grid-cols-[1fr_auto_auto_auto_auto_20px] gap-x-3 border-b py-1 text-xs uppercase tracking-wide text-muted-foreground">
        <div>Model</div>
        <div className="text-right">Calls</div>
        <div className="text-right">Prompt</div>
        <div className="text-right">Completion</div>
        <div className="text-right">Cost</div>
        <div />
      </div>
      {models.map((m) => {
        const open = expandedModel === m.model;
        return (
          <div key={m.model} className="border-b last:border-none">
            <button
              type="button"
              onClick={() => setExpandedModel(open ? null : m.model)}
              className="grid w-full grid-cols-[1fr_auto_auto_auto_auto_20px] items-center gap-x-3 py-2 text-left transition-colors hover:bg-muted/40"
            >
              <div className="font-mono text-xs">{m.model}</div>
              <div className="text-right tabular-nums">
                {m.calls.toLocaleString()}
              </div>
              <div className="text-right tabular-nums">
                {m.prompt_tokens.toLocaleString()}
              </div>
              <div className="text-right tabular-nums">
                {m.completion_tokens.toLocaleString()}
              </div>
              <div className="text-right tabular-nums">
                ${m.cost_usd.toFixed(4)}
              </div>
              <div
                className={
                  "text-xs text-muted-foreground transition-transform " +
                  (open ? "rotate-90" : "")
                }
              >
                ▸
              </div>
            </button>
            {open && <LlmCallList model={m.model} userId={userId} />}
          </div>
        );
      })}
    </div>
  );
}

function LlmCallList({
  model,
  userId,
}: {
  model: string;
  userId?: string;
}) {
  const { data, isLoading } = useAdminLlmCalls({ model, userId });

  if (isLoading) {
    return (
      <div className="border-t bg-muted/20 p-3 text-xs text-muted-foreground">
        Loading calls…
      </div>
    );
  }
  if (!data || data.items.length === 0) {
    return (
      <div className="border-t bg-muted/20 p-3 text-xs text-muted-foreground">
        No calls for this model in the selected window.
      </div>
    );
  }
  return (
    <div className="border-t bg-muted/20 p-2">
      <div className="mb-2 flex items-center justify-between px-1 text-[10px] uppercase tracking-wide text-muted-foreground">
        <span>
          {data.total} calls · total ${data.total_cost_usd.toFixed(4)}
        </span>
      </div>
      <div className="overflow-x-auto rounded border bg-background">
        <table className="w-full text-xs">
          <thead>
            <tr className="border-b bg-muted/40 text-[10px] uppercase text-muted-foreground">
              <th className="px-2 py-1.5 text-left font-medium">When</th>
              <th className="px-2 py-1.5 text-left font-medium">Kind</th>
              {!userId && (
                <th className="px-2 py-1.5 text-left font-medium">User</th>
              )}
              <th className="px-2 py-1.5 text-right font-medium">Prompt</th>
              <th className="px-2 py-1.5 text-right font-medium">Completion</th>
              <th className="px-2 py-1.5 text-right font-medium">Total</th>
              <th className="px-2 py-1.5 text-right font-medium">Cost</th>
              <th className="px-2 py-1.5 text-right font-medium">Latency</th>
              <th className="px-2 py-1.5 text-left font-medium">Status</th>
            </tr>
          </thead>
          <tbody>
            {data.items.map((c) => (
              <tr key={c.id} className="border-b last:border-none">
                <td className="whitespace-nowrap px-2 py-1.5">
                  {new Date(c.created_at).toLocaleString()}
                </td>
                <td className="whitespace-nowrap px-2 py-1.5 font-mono">
                  {c.kind}
                </td>
                {!userId && (
                  <td className="whitespace-nowrap px-2 py-1.5">
                    {c.user_id && c.user_email ? (
                      <Link
                        to={`/users/${c.user_id}`}
                        className="text-primary hover:underline"
                      >
                        {c.user_email}
                      </Link>
                    ) : (
                      <span className="text-muted-foreground">—</span>
                    )}
                  </td>
                )}
                <td className="px-2 py-1.5 text-right tabular-nums">
                  {c.prompt_tokens.toLocaleString()}
                </td>
                <td className="px-2 py-1.5 text-right tabular-nums">
                  {c.completion_tokens.toLocaleString()}
                </td>
                <td className="px-2 py-1.5 text-right tabular-nums">
                  {c.total_tokens.toLocaleString()}
                </td>
                <td className="px-2 py-1.5 text-right tabular-nums">
                  {c.cost_usd !== null ? `$${c.cost_usd.toFixed(6)}` : "—"}
                </td>
                <td className="px-2 py-1.5 text-right tabular-nums">
                  {c.duration_ms !== null ? `${c.duration_ms}ms` : "—"}
                </td>
                <td className="whitespace-nowrap px-2 py-1.5">
                  <span
                    className={
                      "rounded px-1 text-[10px] font-semibold uppercase " +
                      (c.status === "error"
                        ? "bg-destructive/10 text-destructive"
                        : "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400")
                    }
                  >
                    {c.status}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function Stat({
  label,
  value,
  small,
}: {
  label: string;
  value: string;
  small?: boolean;
}) {
  return (
    <div className="rounded-md border bg-muted/20 p-3">
      <div className="text-[10px] uppercase tracking-wide text-muted-foreground">
        {label}
      </div>
      <div
        className={
          small
            ? "text-sm font-medium tabular-nums"
            : "text-lg font-semibold tabular-nums"
        }
      >
        {value}
      </div>
    </div>
  );
}
