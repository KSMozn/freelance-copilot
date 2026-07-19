import { useEffect, useId, useMemo, useRef, useState } from "react";

import { Check, ChevronDown, Search } from "lucide-react";

import {
  getCountryOptions,
  matchesCountryQuery,
  type CountryCode,
  type CountryOption,
} from "@/shared/lib/phone";
import { cn } from "@/shared/lib/utils";

interface CountrySelectProps {
  value: CountryCode | "";
  onChange: (iso: CountryCode) => void;
  variant?: "compact" | "full";
  showCallingCode?: boolean;
  placeholder?: string;
  disabled?: boolean;
  id?: string;
  "aria-label"?: string;
  locale?: string;
  className?: string;
  triggerClassName?: string;
}

export function CountrySelect({
  value,
  onChange,
  variant = "full",
  showCallingCode = true,
  placeholder = "Select country",
  disabled,
  id,
  "aria-label": ariaLabel,
  locale,
  className,
  triggerClassName,
}: CountrySelectProps) {
  const reactId = useId();
  const baseId = id ?? reactId;
  const listboxId = `${baseId}-listbox`;
  const optionId = (iso: string) => `${baseId}-opt-${iso}`;

  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [highlight, setHighlight] = useState(0);

  const rootRef = useRef<HTMLDivElement>(null);
  const searchRef = useRef<HTMLInputElement>(null);
  const listRef = useRef<HTMLDivElement>(null);

  const options = useMemo(() => getCountryOptions(locale), [locale]);
  const selected: CountryOption | undefined = useMemo(
    () => options.find((o) => o.iso === value),
    [options, value],
  );
  const filtered = useMemo(
    () => options.filter((o) => matchesCountryQuery(o, query)),
    [options, query],
  );

  // Close on outside click.
  useEffect(() => {
    if (!open) return;
    function onDoc(e: MouseEvent) {
      if (!rootRef.current?.contains(e.target as Node)) setOpen(false);
    }
    document.addEventListener("mousedown", onDoc);
    return () => document.removeEventListener("mousedown", onDoc);
  }, [open]);

  // On open: focus the search box and highlight the current selection.
  useEffect(() => {
    if (!open) return;
    setQuery("");
    const idx = filtered.findIndex((o) => o.iso === value);
    setHighlight(idx >= 0 ? idx : 0);
    searchRef.current?.focus();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open]);

  // Keep the highlighted row in view.
  useEffect(() => {
    if (!open) return;
    listRef.current?.querySelector<HTMLElement>('[data-active="true"]')?.scrollIntoView({
      block: "nearest",
    });
  }, [highlight, open]);

  function commit(option: CountryOption | undefined) {
    if (!option) return;
    onChange(option.iso);
    setOpen(false);
  }

  function onSearchKeyDown(e: React.KeyboardEvent) {
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setHighlight((h) => Math.min(h + 1, filtered.length - 1));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setHighlight((h) => Math.max(h - 1, 0));
    } else if (e.key === "Home") {
      e.preventDefault();
      setHighlight(0);
    } else if (e.key === "End") {
      e.preventDefault();
      setHighlight(filtered.length - 1);
    } else if (e.key === "Enter") {
      e.preventDefault();
      commit(filtered[highlight]);
    } else if (e.key === "Escape") {
      e.preventDefault();
      setOpen(false);
    }
  }

  return (
    <div ref={rootRef} className={cn("relative", className)}>
      <button
        id={baseId}
        type="button"
        disabled={disabled}
        aria-haspopup="listbox"
        aria-expanded={open}
        aria-label={ariaLabel ?? (selected ? `Country: ${selected.name}` : placeholder)}
        onClick={() => setOpen((o) => !o)}
        onKeyDown={(e) => {
          if (disabled) return;
          if (!open && (e.key === "ArrowDown" || e.key === "Enter" || e.key === " ")) {
            e.preventDefault();
            setOpen(true);
          }
        }}
        className={cn(
          "flex h-10 items-center gap-1.5 rounded-md border border-input bg-background px-3 text-sm",
          "text-foreground ring-offset-background transition-colors",
          "hover:bg-muted focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
          "disabled:cursor-not-allowed disabled:opacity-50",
          variant === "full" && "w-full",
          triggerClassName,
        )}
      >
        <span aria-hidden className="text-base leading-none">
          {selected?.flag ?? "\u{1F3F3}"}
        </span>
        {variant === "full" && (
          <span className={cn("flex-1 truncate text-left", !selected && "text-muted-foreground")}>
            {selected?.name ?? placeholder}
          </span>
        )}
        {selected && showCallingCode && (
          <span className={cn(variant === "full" ? "pl-2 text-muted-foreground" : "")}>
            +{selected.callingCode}
          </span>
        )}
        <ChevronDown aria-hidden className="h-4 w-4 shrink-0 text-muted-foreground" />
      </button>

      {open && (
        <div
          className={cn(
            "absolute left-0 top-full z-50 mt-1 w-max min-w-[17rem] max-w-[calc(100vw-1.5rem)]",
            "rounded-md border bg-card text-card-foreground shadow-lg",
          )}
        >
          <div className="flex items-center gap-2 border-b px-3 py-2">
            <Search aria-hidden className="h-4 w-4 shrink-0 text-muted-foreground" />
            <input
              ref={searchRef}
              type="text"
              role="combobox"
              aria-expanded="true"
              aria-controls={listboxId}
              aria-autocomplete="list"
              aria-activedescendant={
                filtered[highlight] ? optionId(filtered[highlight].iso) : undefined
              }
              value={query}
              placeholder="Search country or code…"
              onChange={(e) => {
                setQuery(e.target.value);
                setHighlight(0);
              }}
              onKeyDown={onSearchKeyDown}
              className="h-6 w-full bg-transparent text-sm outline-none placeholder:text-muted-foreground"
            />
          </div>

          <div
            ref={listRef}
            id={listboxId}
            role="listbox"
            aria-label="Countries"
            className="max-h-64 overflow-y-auto py-1"
          >
            {filtered.length === 0 ? (
              <p className="px-3 py-6 text-center text-sm text-muted-foreground">
                No matching country.
              </p>
            ) : (
              filtered.map((option, i) => {
                const isSelected = option.iso === value;
                const isActive = i === highlight;
                return (
                  <button
                    key={option.iso}
                    id={optionId(option.iso)}
                    type="button"
                    role="option"
                    aria-selected={isSelected}
                    data-active={isActive}
                    onMouseDown={(e) => {
                      e.preventDefault(); // beat the search input's blur
                      commit(option);
                    }}
                    onMouseEnter={() => setHighlight(i)}
                    className={cn(
                      "flex w-full items-center gap-2.5 px-3 py-2 text-left text-sm",
                      isActive ? "bg-accent text-accent-foreground" : "text-foreground",
                    )}
                  >
                    <span aria-hidden className="text-base leading-none">
                      {option.flag}
                    </span>
                    <span className="min-w-0 flex-1 truncate">{option.name}</span>
                    {showCallingCode && (
                      <span
                        className={cn(
                          "shrink-0 tabular-nums",
                          isActive ? "text-accent-foreground/80" : "text-muted-foreground",
                        )}
                      >
                        +{option.callingCode}
                      </span>
                    )}
                    <Check
                      aria-hidden
                      className={cn("h-4 w-4 shrink-0", isSelected ? "opacity-100" : "opacity-0")}
                    />
                  </button>
                );
              })
            )}
          </div>
        </div>
      )}
    </div>
  );
}
CountrySelect.displayName = "CountrySelect";
