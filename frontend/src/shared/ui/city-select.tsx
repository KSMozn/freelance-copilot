import { useEffect, useId, useMemo, useRef, useState } from "react";
import { Check, ChevronDown, Loader2, MapPin, Search, X } from "lucide-react";

import { getCitiesForCountry, matchesCityQuery, type GeoCity } from "@/shared/lib/geo";
import type { CountryCode } from "@/shared/lib/phone";
import { cn } from "@/shared/lib/utils";

const CITY_RESULT_CAP = 100;

interface CitySelectProps {
  country: CountryCode | "";
  value: string;
  onChange: (city: GeoCity | null) => void;
  placeholder?: string;
  disabled?: boolean;
  invalid?: boolean;
  id?: string;
  "aria-label"?: string;
  className?: string;
  triggerClassName?: string;
  loadCities?: (iso: CountryCode) => Promise<GeoCity[]>;
}

export function CitySelect({
  country,
  value,
  onChange,
  placeholder = "Select city",
  disabled,
  invalid,
  id,
  "aria-label": ariaLabel,
  className,
  triggerClassName,
  loadCities = getCitiesForCountry,
}: CitySelectProps) {
  const reactId = useId();
  const baseId = id ?? reactId;
  const listboxId = `${baseId}-listbox`;
  const optionId = (index: number) => `${baseId}-opt-${index}`;

  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [highlight, setHighlight] = useState(0);
  const [cities, setCities] = useState<GeoCity[] | null>(null);
  const [loading, setLoading] = useState(false);

  const rootRef = useRef<HTMLDivElement>(null);
  const searchRef = useRef<HTMLInputElement>(null);
  const listRef = useRef<HTMLDivElement>(null);

  const isDisabled = disabled || !country;

  // Load the country's cities lazily. Reset when the country changes so a stale
  // list never leaks across countries.
  useEffect(() => {
    if (!country) {
      setCities(null);
      setLoading(false);
      return;
    }
    let cancelled = false;
    setLoading(true);
    setCities(null);
    void loadCities(country)
      .then((list) => {
        if (!cancelled) setCities(list);
      })
      .catch(() => {
        if (!cancelled) setCities([]);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [country, loadCities]);

  const filtered = useMemo(() => {
    if (!cities) return [];
    const matches: GeoCity[] = [];
    for (const city of cities) {
      if (matchesCityQuery(city, query)) {
        matches.push(city);
        if (matches.length >= CITY_RESULT_CAP) break;
      }
    }
    return matches;
  }, [cities, query]);

  const truncated = Boolean(cities) && filtered.length >= CITY_RESULT_CAP;
  const countryHasNoCities = !loading && cities !== null && cities.length === 0;

  // Close on outside click.
  useEffect(() => {
    if (!open) return;
    function onDoc(e: MouseEvent) {
      if (!rootRef.current?.contains(e.target as Node)) setOpen(false);
    }
    document.addEventListener("mousedown", onDoc);
    return () => document.removeEventListener("mousedown", onDoc);
  }, [open]);

  useEffect(() => {
    if (!open) return;
    setQuery("");
    const idx = filtered.findIndex((c) => c.name === value);
    setHighlight(idx >= 0 ? idx : 0);
    searchRef.current?.focus();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open]);

  useEffect(() => {
    if (!open) return;
    listRef.current?.querySelector<HTMLElement>('[data-active="true"]')?.scrollIntoView({
      block: "nearest",
    });
  }, [highlight, open]);

  function commit(city: GeoCity | undefined) {
    if (!city) return;
    onChange(city);
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

  const triggerLabel = value || (country ? placeholder : "Select a country first");

  return (
    <div ref={rootRef} className={cn("relative", className)}>
      <button
        id={baseId}
        type="button"
        disabled={isDisabled}
        aria-haspopup="listbox"
        aria-expanded={open}
        aria-invalid={invalid || undefined}
        aria-label={ariaLabel ?? (value ? `City: ${value}` : placeholder)}
        onClick={() => setOpen((o) => !o)}
        onKeyDown={(e) => {
          if (isDisabled) return;
          if (!open && (e.key === "ArrowDown" || e.key === "Enter" || e.key === " ")) {
            e.preventDefault();
            setOpen(true);
          }
        }}
        className={cn(
          "flex h-10 w-full items-center gap-1.5 rounded-md border border-input bg-background px-3 text-sm",
          "text-foreground ring-offset-background transition-colors",
          "hover:bg-muted focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
          "disabled:cursor-not-allowed disabled:opacity-50",
          invalid && "border-destructive focus-visible:ring-destructive",
          triggerClassName,
        )}
      >
        <MapPin aria-hidden className="h-4 w-4 shrink-0 text-muted-foreground" />
        <span className={cn("flex-1 truncate text-left", !value && "text-muted-foreground")}>
          {triggerLabel}
        </span>
        <ChevronDown aria-hidden className="h-4 w-4 shrink-0 text-muted-foreground" />
      </button>

      {open && (
        <div
          className={cn(
            "absolute left-0 top-full z-50 mt-1 w-full min-w-[15rem] max-w-[calc(100vw-1.5rem)]",
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
              aria-activedescendant={filtered[highlight] ? optionId(highlight) : undefined}
              value={query}
              placeholder="Search city…"
              onChange={(e) => {
                setQuery(e.target.value);
                setHighlight(0);
              }}
              onKeyDown={onSearchKeyDown}
              className="h-6 w-full bg-transparent text-sm outline-none placeholder:text-muted-foreground"
            />
            {query && (
              <button
                type="button"
                aria-label="Clear search"
                onMouseDown={(e) => {
                  e.preventDefault();
                  setQuery("");
                  setHighlight(0);
                  searchRef.current?.focus();
                }}
                className="shrink-0 text-muted-foreground hover:text-foreground"
              >
                <X aria-hidden className="h-4 w-4" />
              </button>
            )}
          </div>

          <div
            ref={listRef}
            id={listboxId}
            role="listbox"
            aria-label="Cities"
            className="max-h-64 overflow-y-auto py-1"
          >
            {loading ? (
              <p className="flex items-center justify-center gap-2 px-3 py-6 text-sm text-muted-foreground">
                <Loader2 aria-hidden className="h-4 w-4 animate-spin" />
                Loading cities…
              </p>
            ) : countryHasNoCities ? (
              <p className="px-3 py-6 text-center text-sm text-muted-foreground">
                No cities available for this country.
              </p>
            ) : filtered.length === 0 ? (
              <p className="px-3 py-6 text-center text-sm text-muted-foreground">
                No matching city.
              </p>
            ) : (
              filtered.map((city, i) => {
                const isSelected = city.name === value;
                const isActive = i === highlight;
                return (
                  <button
                    key={`${city.name}-${city.region ?? ""}-${i}`}
                    id={optionId(i)}
                    type="button"
                    role="option"
                    aria-selected={isSelected}
                    data-active={isActive}
                    onMouseDown={(e) => {
                      e.preventDefault(); // beat the search input's blur
                      commit(city);
                    }}
                    onMouseEnter={() => setHighlight(i)}
                    className={cn(
                      "flex w-full items-center gap-2.5 px-3 py-2 text-left text-sm",
                      isActive ? "bg-accent text-accent-foreground" : "text-foreground",
                    )}
                  >
                    <span className="min-w-0 flex-1 truncate">
                      {city.name}
                      {city.region && (
                        <span
                          className={cn(
                            "text-xs",
                            isActive ? "text-accent-foreground/80" : "text-muted-foreground",
                          )}
                        >
                          {`, ${city.region}`}
                        </span>
                      )}
                    </span>
                    <Check
                      aria-hidden
                      className={cn("h-4 w-4 shrink-0", isSelected ? "opacity-100" : "opacity-0")}
                    />
                  </button>
                );
              })
            )}
            {truncated && (
              <p className="border-t px-3 py-2 text-center text-xs text-muted-foreground">
                Showing the first {CITY_RESULT_CAP} — keep typing to narrow results.
              </p>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
CitySelect.displayName = "CitySelect";
