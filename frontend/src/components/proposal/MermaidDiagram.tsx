import { useEffect, useId, useRef, useState } from "react";

import { Button } from "@/shared/ui/button";
import { Copy } from "lucide-react";
import { toast } from "sonner";

let _initialized = false;
async function ensureMermaid() {
  const mod = (await import("mermaid")).default;
  if (!_initialized) {
    // Match the app's dark palette so diagrams don't look like a brochure.
    mod.initialize({
      startOnLoad: false,
      theme: "dark",
      securityLevel: "strict",
      themeVariables: {
        background: "transparent",
        primaryColor: "#1f2937",
        primaryTextColor: "#e5e7eb",
        primaryBorderColor: "#6366f1",
        lineColor: "#94a3b8",
      },
    });
    _initialized = true;
  }
  return mod;
}

export function MermaidDiagram({ source }: { source: string }) {
  const id = useId().replace(/:/g, "_");
  const ref = useRef<HTMLDivElement>(null);
  const [error, setError] = useState<string | null>(null);
  const [showSource, setShowSource] = useState(false);

  useEffect(() => {
    let cancelled = false;
    setError(null);
    ensureMermaid()
      .then(async (mermaid) => {
        if (cancelled || !ref.current) return;
        try {
          const { svg } = await mermaid.render(`mmd-${id}`, source);
          if (!cancelled && ref.current) ref.current.innerHTML = svg;
        } catch (err) {
          if (!cancelled) {
            const message = err instanceof Error ? err.message : String(err);
            setError(message);
          }
        }
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : String(err));
        }
      });
    return () => {
      cancelled = true;
    };
  }, [id, source]);

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(source);
      toast.success("Mermaid source copied");
    } catch {
      toast.error("Copy failed");
    }
  };

  return (
    <div className="space-y-2">
      {error ? (
        <div className="rounded-md border border-destructive/40 bg-destructive/10 p-3 text-xs text-destructive">
          Diagram render failed: {error}
        </div>
      ) : (
        <div
          ref={ref}
          className="overflow-x-auto rounded-md border border-border/70 bg-muted/30 p-3 [&_svg]:mx-auto"
        />
      )}
      <div className="flex justify-end gap-2">
        <Button size="sm" variant="ghost" onClick={() => setShowSource((v) => !v)}>
          {showSource ? "Hide source" : "Show source"}
        </Button>
        <Button size="sm" variant="ghost" onClick={copy}>
          <Copy className="mr-1 h-3.5 w-3.5" />
          Copy
        </Button>
      </div>
      {showSource && (
        <pre className="overflow-x-auto rounded-md border border-border/70 bg-muted/40 p-3 text-xs">
          <code>{source}</code>
        </pre>
      )}
    </div>
  );
}
