const pendingSaveFlushers = new Set<() => Promise<void>>();
let pendingSaveGeneration = 0;

export function getPendingSaveGeneration(): number {
  return pendingSaveGeneration;
}

export function advancePendingSaveBoundary(): void {
  pendingSaveGeneration += 1;
}

export function registerPendingSave(flush: () => Promise<void>): () => void {
  pendingSaveFlushers.add(flush);
  return () => pendingSaveFlushers.delete(flush);
}

export async function flushPendingSaves(timeoutMs = 5_000): Promise<void> {
  const settled = Promise.allSettled([...pendingSaveFlushers].map((flush) => flush()));
  await Promise.race([
    settled,
    new Promise<void>((resolve) => {
      setTimeout(resolve, timeoutMs);
    }),
  ]);
}
