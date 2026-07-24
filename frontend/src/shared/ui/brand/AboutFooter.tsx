import { BRAND } from "@/shared/config/brand";
import { cn } from "@/shared/lib/utils";

export function AboutFooter({ className }: { className?: string }) {
  return (
    <p className={cn("text-center text-xs text-muted-foreground", className)}>
      <span className="text-brand-gradient font-semibold">{BRAND.product}</span> · {BRAND.tagline}
    </p>
  );
}
