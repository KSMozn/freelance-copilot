import { useCallback, useEffect, useRef } from "react";

import { getPendingSaveGeneration, registerPendingSave } from "@/shared/lib/pendingSaves";

interface PendingSave<T> {
  generation: number;
  serialized: string;
  value: T;
}

export function useAutoSave<T>(
  value: T,
  save: (v: T) => Promise<unknown> | unknown,
  opts: { delay?: number; enabled?: boolean } = {},
) {
  const { delay = 700, enabled = true } = opts;
  const firstRun = useRef(true);
  const lastSaved = useRef(JSON.stringify(value));
  const lastQueued = useRef(lastSaved.current);
  const latestSave = useRef(save);
  const enabledRef = useRef(enabled);
  const pending = useRef<PendingSave<T> | null>(null);
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const saveQueue = useRef(Promise.resolve());

  latestSave.current = save;
  enabledRef.current = enabled;

  const queueSave = useCallback((next: PendingSave<T>): Promise<void> => {
    if (next.serialized === lastQueued.current) return saveQueue.current;
    lastQueued.current = next.serialized;
    const saveValue = latestSave.current;
    saveQueue.current = saveQueue.current
      .then(async () => {
        if (next.generation !== getPendingSaveGeneration()) return;
        await saveValue(next.value);
        if (next.generation !== getPendingSaveGeneration()) return;
        lastSaved.current = next.serialized;
      })
      .catch(() => {
        if (lastQueued.current === next.serialized) {
          lastQueued.current = lastSaved.current;
        }
      });
    return saveQueue.current;
  }, []);

  const flush = useCallback(async () => {
    if (timer.current) clearTimeout(timer.current);
    const unsaved = pending.current;
    pending.current = null;
    timer.current = null;
    if (unsaved && enabledRef.current) queueSave(unsaved);
    await saveQueue.current;
  }, [queueSave]);

  useEffect(() => {
    const unregister = registerPendingSave(flush);
    return () => {
      unregister();
      void flush();
    };
  }, [flush]);

  useEffect(() => {
    if (firstRun.current) {
      firstRun.current = false;
      lastSaved.current = JSON.stringify(value);
      lastQueued.current = lastSaved.current;
      return;
    }
    pending.current = null;
    if (!enabled) return;

    const serialized = JSON.stringify(value);
    if (serialized === lastQueued.current) return;

    pending.current = {
      generation: getPendingSaveGeneration(),
      value,
      serialized,
    };
    timer.current = setTimeout(() => {
      const unsaved = pending.current;
      pending.current = null;
      timer.current = null;
      if (unsaved) queueSave(unsaved);
    }, delay);

    return () => {
      if (timer.current) clearTimeout(timer.current);
      timer.current = null;
    };
  }, [value, enabled, delay]); // eslint-disable-line react-hooks/exhaustive-deps
}
