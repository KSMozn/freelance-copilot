import { BRAND } from "@/shared/config/brand";
import { cn } from "@/shared/lib/utils";

import { CareeroMark } from "./CareeroMark";

type Variant = "careero" | "careero-admin";

interface Props {
  variant?: Variant;
  size?: number;
  className?: string;
}

const LABELS: Record<Variant, string> = {
  careero: BRAND.product,
  "careero-admin": BRAND.adminWordmark,
};

export function BrandWordmark({ variant = "careero", size = 24, className }: Props) {
  return (
    <span className={cn("inline-flex items-center gap-2 font-semibold tracking-tight", className)}>
      <CareeroMark size={size} />
      <span className="text-[15px] leading-none">{LABELS[variant]}</span>
    </span>
  );
}
