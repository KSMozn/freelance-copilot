import { useId } from "react";

interface Props {
  size?: number;
  className?: string;
}

export function CareeroMark({ size = 28, className }: Props) {
  const uid = useId().replace(/:/g, "");
  const gradId = `careero-grad-${uid}`;
  const sparkGradId = `careero-spark-${uid}`;
  const stroke = size * 0.24;
  const cx = 32;
  const cy = 32;
  const r = 18;

  return (
    <svg viewBox="0 0 64 64" width={size} height={size} className={className} aria-hidden="true">
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
      <path
        d={`M ${cx + r * Math.cos(-Math.PI / 5)} ${cy + r * Math.sin(-Math.PI / 5)}
            A ${r} ${r} 0 1 0 ${cx + r * Math.cos(Math.PI / 5)} ${cy + r * Math.sin(Math.PI / 5)}`}
        fill="none"
        stroke={`url(#${gradId})`}
        strokeWidth={stroke}
        strokeLinecap="round"
      />
      <path
        d={`M 46 32
            L 50 30 L 46 28 L 44 24 L 42 28 L 38 30 L 42 32
            L 44 36 Z`}
        fill={`url(#${sparkGradId})`}
      />
    </svg>
  );
}
