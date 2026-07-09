import { useEffect, useRef, useState } from "react";

import { cn } from "@/shared/lib/utils";

interface SelectOption {
  value: string;
  label: string;
}

interface SelectProps {
  value: string;
  onChange: (e: { target: { value: string } }) => void;
  options: SelectOption[];
  placeholder?: string;
  disabled?: boolean;
  className?: string;
  id?: string;
}

// Custom dropdown that matches the Combobox visually. We rolled our own
// because native <select> + Tailwind dark mode is a coin flip — Chromium
// on macOS renders the selected text in the OS chrome's default color
// (often invisible against our dark theme), and the popup escapes any
// z-index we set. This component keeps everything inside our DOM, so
// styling and stacking are predictable.
export function Select({
  value,
  onChange,
  options,
  placeholder,
  disabled,
  className,
  id,
}: SelectProps) {
  const [open, setOpen] = useState(false);
  const [highlight, setHighlight] = useState(0);
  const rootRef = useRef<HTMLDivElement>(null);

  // Click outside closes the menu.
  useEffect(() => {
    function onDoc(e: MouseEvent) {
      if (!rootRef.current?.contains(e.target as Node)) setOpen(false);
    }
    document.addEventListener("mousedown", onDoc);
    return () => document.removeEventListener("mousedown", onDoc);
  }, []);

  const selected = options.find((o) => o.value === value) ?? null;

  function pick(opt: SelectOption) {
    onChange({ target: { value: opt.value } });
    setOpen(false);
  }

  return (
    <div ref={rootRef} className={cn("relative", className)}>
      <button
        id={id}
        type="button"
        disabled={disabled}
        onClick={() => setOpen((o) => !o)}
        onKeyDown={(e) => {
          if (disabled) return;
          if (e.key === "ArrowDown" || e.key === "Enter" || e.key === " ") {
            e.preventDefault();
            if (!open) {
              setOpen(true);
              setHighlight(
                Math.max(
                  0,
                  options.findIndex((o) => o.value === value),
                ),
              );
              return;
            }
            if (e.key === "Enter") {
              pick(options[highlight]);
            } else {
              setHighlight((h) => Math.min(h + 1, options.length - 1));
            }
          } else if (e.key === "ArrowUp" && open) {
            e.preventDefault();
            setHighlight((h) => Math.max(h - 1, 0));
          } else if (e.key === "Escape") {
            setOpen(false);
          }
        }}
        aria-haspopup="listbox"
        aria-expanded={open}
        className={cn(
          "flex h-10 w-full items-center justify-between rounded-md border border-input bg-background px-3 py-2 text-left text-sm",
          "text-foreground ring-offset-background",
          "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
          "disabled:cursor-not-allowed disabled:opacity-50",
        )}
      >
        <span className={cn("truncate", !selected && "text-muted-foreground")}>
          {selected ? selected.label : (placeholder ?? "Select…")}
        </span>
        <svg
          width="12"
          height="12"
          viewBox="0 0 12 12"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.5"
          strokeLinecap="round"
          strokeLinejoin="round"
          className="ml-2 text-muted-foreground"
        >
          <polyline points="3 5 6 8 9 5" />
        </svg>
      </button>

      {open && (
        <div
          role="listbox"
          className={cn(
            // bg-card + text-card-foreground because this codebase has no
            // `--popover` token (bg-popover would render transparent).
            "absolute left-0 right-0 top-full z-50 mt-1 max-h-64 overflow-y-auto rounded-md border bg-card text-card-foreground shadow-lg",
          )}
        >
          {options.map((opt, i) => {
            const isSelected = opt.value === value;
            const isHighlighted = i === highlight;
            return (
              <button
                key={`${opt.value}-${i}`}
                type="button"
                onMouseDown={(e) => {
                  e.preventDefault();
                  pick(opt);
                }}
                onMouseEnter={() => setHighlight(i)}
                className={cn(
                  "flex w-full items-center justify-between px-3 py-2 text-left text-sm",
                  isHighlighted
                    ? "bg-accent text-accent-foreground"
                    : "text-foreground hover:bg-muted",
                )}
                role="option"
                aria-selected={isSelected}
              >
                <span className="truncate">{opt.label}</span>
                {isSelected && (
                  <span aria-hidden className="ml-2 text-xs">
                    ✓
                  </span>
                )}
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}
