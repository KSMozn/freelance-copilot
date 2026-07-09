import { cn } from "@/shared/lib/utils";

import { CareeroMark } from "./CareeroMark";
import { PersonaArmoryMark } from "./PersonaArmoryMark";

type Variant = "careero" | "personaarmory" | "personaarmory-admin";

interface Props {
  variant?: Variant;
  size?: number;
  className?: string;
  /** Hide the wordmark text — mark only. Useful on very small chrome. */
  markOnly?: boolean;
}

const LABELS: Record<Variant, string> = {
  careero: "Careero",
  personaarmory: "PersonaArmory",
  "personaarmory-admin": "PersonaArmory · Admin",
};

/**
 * Wordmark = brand mark + label, used in topbars and sidebars. Kept in a
 * single component so the pairing (mark → label) can't drift across surfaces.
 */
export function BrandWordmark({
  variant = "careero",
  size = 24,
  className,
  markOnly = false,
}: Props) {
  const Mark =
    variant === "careero" ? CareeroMark : PersonaArmoryMark;
  return (
    <span
      className={cn(
        "inline-flex items-center gap-2 font-semibold tracking-tight",
        className,
      )}
    >
      <Mark size={size} />
      {!markOnly && (
        <span className="text-[15px] leading-none">{LABELS[variant]}</span>
      )}
    </span>
  );
}
