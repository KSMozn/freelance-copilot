import { FormEvent, useState } from "react";
import { Building2, ExternalLink, Loader2, RefreshCw, Search } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/shared/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/shared/ui/card";
import { Input } from "@/shared/ui/input";
import { useResearchClient } from "@/features/professional/analysis/researchApi";
import type { CompanyResearch } from "@/features/professional/apiTypes";

function Field({ label, value }: { label: string; value: string | null | undefined }) {
  if (!value) return null;
  return (
    <div>
      <div className="text-[10px] uppercase tracking-wider text-muted-foreground">{label}</div>
      <div className="text-sm">{value}</div>
    </div>
  );
}

function StackChips({ items }: { items: string[] }) {
  if (!items.length) return null;
  return (
    <div>
      <div className="mb-1 text-[10px] uppercase tracking-wider text-muted-foreground">
        Existing stack
      </div>
      <div className="flex flex-wrap gap-1">
        {items.map((s) => (
          <span
            key={s}
            className="rounded-md border border-muted px-1.5 py-0.5 text-xs text-foreground"
          >
            {s}
          </span>
        ))}
      </div>
    </div>
  );
}

function ResearchBody({ research }: { research: CompanyResearch }) {
  return (
    <div className="space-y-3">
      {research.personalization_hook && (
        <div className="rounded-md border border-primary/30 bg-primary/5 p-3 text-sm italic">
          “{research.personalization_hook}”
        </div>
      )}
      <div className="grid gap-3 sm:grid-cols-2">
        <Field label="Business domain" value={research.business_domain} />
        <Field label="Target customers" value={research.target_customers} />
        <Field label="Funding signals" value={research.funding_signals} />
        <Field label="Likely architecture" value={research.likely_architecture} />
      </div>
      {research.product_summary && (
        <div>
          <div className="text-[10px] uppercase tracking-wider text-muted-foreground">
            Product summary
          </div>
          <p className="text-sm">{research.product_summary}</p>
        </div>
      )}
      <StackChips items={research.existing_stack} />
      <div className="flex items-center justify-between text-xs text-muted-foreground">
        <a
          href={research.source_url}
          target="_blank"
          rel="noreferrer"
          className="flex items-center gap-1 text-primary hover:underline"
        >
          {research.source_url}
          <ExternalLink className="h-3 w-3" />
        </a>
        {research.fetched_at && (
          <span>Fetched {new Date(research.fetched_at).toLocaleString()}</span>
        )}
      </div>
    </div>
  );
}

export function CompanyResearchCard({
  jobId,
  research,
}: {
  jobId: string | undefined;
  research: CompanyResearch | null | undefined;
}) {
  const mutation = useResearchClient(jobId);
  const [url, setUrl] = useState(research?.source_url ?? "");

  const run = (e: FormEvent) => {
    e.preventDefault();
    const trimmed = url.trim();
    if (!trimmed) return;
    mutation.mutate(trimmed, {
      onSuccess: (data) => {
        if (data.business_domain || data.product_summary) {
          toast.success(`Researched ${data.source_url}`);
        } else {
          toast.warning("Page fetched but little signal — try the product page directly");
        }
      },
      onError: (err: unknown) => {
        const detail =
          (err as { response?: { data?: { detail?: string } } } | undefined)?.response?.data
            ?.detail ?? "Research failed";
        toast.error(detail);
      },
    });
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-base">
          <Building2 className="h-4 w-4 text-primary" />
          Company research
        </CardTitle>
        <CardDescription className="text-xs">
          Paste the client's website or product URL — we'll extract a structured read to personalize
          the proposal.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <form onSubmit={run} className="flex gap-2">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="https://acme.com"
              className="pl-9"
              disabled={mutation.isPending}
            />
          </div>
          <Button type="submit" disabled={mutation.isPending || !url.trim()}>
            {mutation.isPending ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Researching…
              </>
            ) : research ? (
              <>
                <RefreshCw className="mr-2 h-4 w-4" />
                Re-research
              </>
            ) : (
              "Research"
            )}
          </Button>
        </form>

        {research && <ResearchBody research={research} />}
      </CardContent>
    </Card>
  );
}
