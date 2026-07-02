import { useEffect, useMemo, useRef, useState } from "react";

import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";

interface ComboboxProps {
  value: string;
  onChange: (v: string) => void;
  // Called when the user commits their entry — either by clicking a
  // suggestion, pressing Enter, or blurring the field. Receives the
  // committed value directly so the parent doesn't race the pending
  // `onChange` state update (clicking "Python" would otherwise commit
  // whatever half-typed string the parent had, e.g. "Py").
  onBlurCommit?: (value: string) => void;
  options: string[];
  placeholder?: string;
  id?: string;
  className?: string;
  // Don't show suggestions until the user has typed at least this many
  // characters. Avoids flashing the full list while the field is empty.
  minChars?: number;
  // Max suggestions to surface at once. Cap is for UX (long lists feel
  // overwhelming) not perf.
  maxResults?: number;
}

// Minimal autocomplete: a text input plus a filtered-by-typed-substring
// suggestion list underneath. Accepts free text — the dropdown is a
// shortcut, never a constraint.
export function Combobox({
  value,
  onChange,
  onBlurCommit,
  options,
  placeholder,
  id,
  className,
  minChars = 1,
  maxResults = 8,
}: ComboboxProps) {
  const [open, setOpen] = useState(false);
  const [highlight, setHighlight] = useState(0);
  const rootRef = useRef<HTMLDivElement>(null);

  // Click outside closes the list.
  useEffect(() => {
    function onDoc(e: MouseEvent) {
      if (!rootRef.current?.contains(e.target as Node)) setOpen(false);
    }
    document.addEventListener("mousedown", onDoc);
    return () => document.removeEventListener("mousedown", onDoc);
  }, []);

  const filtered = useMemo(() => {
    const q = value.trim().toLowerCase();
    if (q.length < minChars) return [];
    const matches = options.filter((o) => o.toLowerCase().includes(q));
    // Prefer matches that START with the query.
    matches.sort((a, b) => {
      const aStarts = a.toLowerCase().startsWith(q) ? 0 : 1;
      const bStarts = b.toLowerCase().startsWith(q) ? 0 : 1;
      return aStarts - bStarts || a.localeCompare(b);
    });
    return matches.slice(0, maxResults);
  }, [value, options, minChars, maxResults]);

  function pick(v: string) {
    onChange(v);
    setOpen(false);
    onBlurCommit?.(v);
  }

  return (
    <div ref={rootRef} className={cn("relative", className)}>
      <Input
        id={id}
        value={value}
        placeholder={placeholder}
        onChange={(e) => {
          onChange(e.target.value);
          setOpen(true);
          setHighlight(0);
        }}
        onFocus={() => setOpen(true)}
        onBlur={() => {
          // Defer so a click on a suggestion still registers.
          setTimeout(() => {
            setOpen(false);
            onBlurCommit?.(value);
          }, 120);
        }}
        onKeyDown={(e) => {
          if (!open || filtered.length === 0) return;
          if (e.key === "ArrowDown") {
            e.preventDefault();
            setHighlight((h) => Math.min(h + 1, filtered.length - 1));
          } else if (e.key === "ArrowUp") {
            e.preventDefault();
            setHighlight((h) => Math.max(h - 1, 0));
          } else if (e.key === "Enter") {
            e.preventDefault();
            pick(filtered[highlight]);
          } else if (e.key === "Escape") {
            setOpen(false);
          }
        }}
        autoComplete="off"
      />
      {open && filtered.length > 0 && (
        <div className="absolute left-0 right-0 top-full z-50 mt-1 max-h-64 overflow-y-auto rounded-md border bg-card text-card-foreground shadow-lg">
          {filtered.map((opt, i) => (
            <button
              key={opt}
              type="button"
              onMouseDown={(e) => {
                // mousedown beats input's onBlur so the click registers.
                e.preventDefault();
                pick(opt);
              }}
              onMouseEnter={() => setHighlight(i)}
              className={cn(
                "block w-full px-3 py-2 text-left text-sm transition-colors",
                i === highlight
                  ? "bg-accent text-accent-foreground"
                  : "hover:bg-muted",
              )}
            >
              {opt}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
