import { useId } from "react";

interface Props {
  size?: number;
  className?: string;
  boxed?: boolean;
}

/**
 * PersonaArmory shield "P" — the parent-brand mark used on
 * `admin.personaarmory.com` and in the footer strip. Hex-shield silhouette
 * with a stroked P and the same brand spark inside its counter.
 */
export function PersonaArmoryMark({
  size = 28,
  className,
  boxed = false,
}: Props) {
  const uid = useId().replace(/:/g, "");
  const gradId = `pa-grad-${uid}`;
  const sparkGradId = `pa-spark-${uid}`;

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
      {/* Hex shield outline */}
      <path
        d="M32 4 L54 16 L54 40 Q54 50 32 60 Q10 50 10 40 L10 16 Z"
        fill="none"
        stroke={`url(#${gradId})`}
        strokeWidth={4}
        strokeLinejoin="round"
      />
      {/* Stylized P — vertical stem + bowl */}
      <path
        d="M22 18 L22 48 M22 18 L36 18 A9 9 0 0 1 36 36 L22 36"
        fill="none"
        stroke={`url(#${gradId})`}
        strokeWidth={5}
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      {/* Spark inside the P bowl */}
      <path
        d="M34 27 L37 25.5 L34 24 L32.5 21 L31 24 L28 25.5 L31 27 L32.5 30 Z"
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
