import { useEffect, useRef } from "react";

// Debounced auto-save. Calls `save(value)` `delay` ms after `value`
// stops changing. Skips the first run so we don't write back the
// initial server payload, and skips when `enabled` is false.
//
// The wizard uses this on each profile-bearing step: type, pause, the
// patch fires. No explicit "save" click required, and navigating away
// mid-step doesn't lose work.
export function useAutoSave<T>(
  value: T,
  save: (v: T) => Promise<unknown> | unknown,
  opts: { delay?: number; enabled?: boolean } = {},
) {
  const { delay = 700, enabled = true } = opts;
  const firstRun = useRef(true);
  const lastSaved = useRef<T>(value);

  useEffect(() => {
    if (firstRun.current) {
      firstRun.current = false;
      lastSaved.current = value;
      return;
    }
    if (!enabled) return;
    // Cheap shallow check via JSON; objects are small (profile patch).
    if (JSON.stringify(value) === JSON.stringify(lastSaved.current)) return;
    const t = setTimeout(() => {
      lastSaved.current = value;
      void save(value);
    }, delay);
    return () => clearTimeout(t);
  }, [value, enabled, delay]); // eslint-disable-line react-hooks/exhaustive-deps
}
