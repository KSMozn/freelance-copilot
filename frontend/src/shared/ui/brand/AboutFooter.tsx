import { BRAND } from "@/shared/config/brand";
import { cn } from "@/shared/lib/utils";

/**
 * Single-line brand footer. Shown on onboarding surfaces (login, register,
 * wizard preview step) so PersonaArmory is credited even though users
 * primarily interact with Careero.
 */
export function AboutFooter({ className }: { className?: string }) {
  return (
    <p className={cn("text-center text-xs text-muted-foreground", className)}>
      <span className="font-medium text-foreground/80">{BRAND.product}</span> is a{" "}
      <span className="text-brand-gradient font-semibold">{BRAND.company}</span> product ·{" "}
      {BRAND.tagline}
    </p>
  );
}
