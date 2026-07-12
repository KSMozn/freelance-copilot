let generation = 0;
let controller = new AbortController();

export function getSessionRequestContext(): {
  generation: number;
  signal: AbortSignal;
} {
  return { generation, signal: controller.signal };
}

export function isCurrentSessionGeneration(candidate: number): boolean {
  return candidate === generation;
}

export function advanceSessionBoundary(): void {
  controller.abort();
  generation += 1;
  controller = new AbortController();
}
