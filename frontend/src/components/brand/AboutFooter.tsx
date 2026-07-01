import { cn } from "@/lib/utils";

/**
 * Single-line brand footer. Shown on onboarding surfaces (login, register,
 * wizard preview step) so PersonaArmory is credited even though users
 * primarily interact with Careero.
 */
export function AboutFooter({ className }: { className?: string }) {
  return (
    <p
      className={cn(
        "text-center text-xs text-muted-foreground",
        className,
      )}
    >
      <span className="font-medium text-foreground/80">Careero</span> is a{" "}
      <span className="text-brand-gradient font-semibold">PersonaArmory</span>{" "}
      product · Equip. Empower. Elevate.
    </p>
  );
}
