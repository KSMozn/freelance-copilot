import { useId } from "react";

interface Props {
  size?: number;
  className?: string;
  /** Draw the mark on a dark surface (e.g. rounded-square app-icon look). */
  boxed?: boolean;
}

/**
 * Careero C mark — the primary product logo used on `app.personaarmory.com`.
 * A three-quarter C in the brand gradient with a 4-point spark inside the
 * opening. Self-contained inline SVG: gradient defs use a `useId` so multiple
 * marks on the same page don't collide on the id.
 */
export function CareeroMark({ size = 28, className, boxed = false }: Props) {
  const uid = useId().replace(/:/g, "");
  const gradId = `careero-grad-${uid}`;
  const sparkGradId = `careero-spark-${uid}`;
  const stroke = size * 0.24;
  const cx = 32;
  const cy = 32;
  const r = 18;

  const mark = (
    <svg
      viewBox="0 0 64 64"
      width={size}
      height={size}
      className={className}
      aria-hidden="true"
    >
      <defs>
        <linearGradient id={gradId} x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor="hsl(var(--brand-from))" />
          <stop offset="55%" stopColor="hsl(var(--brand-mid))" />
          <stop offset="100%" stopColor="hsl(var(--brand-to))" />
        </linearGradient>
        <linearGradient id={sparkGradId} x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor="hsl(var(--brand-from))" />
          <stop offset="100%" stopColor="hsl(var(--brand-to))" />
        </linearGradient>
      </defs>
      {/* Open-C stroke — arc from ~-45° down through the bottom back up to ~45° */}
      <path
        d={`M ${cx + r * Math.cos(-Math.PI / 5)} ${cy + r * Math.sin(-Math.PI / 5)}
            A ${r} ${r} 0 1 0 ${cx + r * Math.cos(Math.PI / 5)} ${cy + r * Math.sin(Math.PI / 5)}`}
        fill="none"
        stroke={`url(#${gradId})`}
        strokeWidth={stroke}
        strokeLinecap="round"
      />
      {/* 4-point spark inside the C's opening (right side) */}
      <path
        d={`M 46 32
            L 50 30 L 46 28 L 44 24 L 42 28 L 38 30 L 42 32
            L 44 36 Z`}
        fill={`url(#${sparkGradId})`}
      />
    </svg>
  );

  if (!boxed) return mark;
  return (
    <span
      className="inline-flex items-center justify-center rounded-xl bg-[hsl(226_33%_8%)] p-1.5"
      style={{ width: size + 12, height: size + 12 }}
    >
      {mark}
    </span>
  );
}
