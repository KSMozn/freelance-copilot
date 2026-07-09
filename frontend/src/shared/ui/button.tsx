import { Button as ButtonPrimitive } from "@base-ui/react/button";
import { cva, type VariantProps } from "class-variance-authority";
import * as React from "react";

import { cn } from "@/shared/lib/utils";

const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:pointer-events-none disabled:opacity-50",
  {
    variants: {
      variant: {
        default: "bg-primary text-primary-foreground hover:bg-primary/90",
        // Brand-gradient CTA — reserve for the single most important action
        // per surface (login, download, "Set as default"). Overuse dilutes
        // the emphasis, per the brand guide.
        brand:
          "bg-brand-gradient text-white shadow-lg shadow-primary/20 hover:brightness-110 hover:shadow-primary/30 transition-[filter,box-shadow]",
        destructive: "bg-destructive text-destructive-foreground hover:bg-destructive/90",
        outline: "border border-input bg-background hover:bg-accent hover:text-accent-foreground",
        secondary: "bg-secondary text-secondary-foreground hover:bg-secondary/80",
        ghost: "hover:bg-accent hover:text-accent-foreground",
        link: "text-primary underline-offset-4 hover:underline",
      },
      size: {
        default: "h-10 px-4 py-2",
        sm: "h-9 rounded-md px-3",
        lg: "h-11 rounded-md px-8",
        icon: "h-10 w-10",
      },
    },
    defaultVariants: { variant: "default", size: "default" },
  },
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>, VariantProps<typeof buttonVariants> {
  /**
   * Render the button's props/styles onto the child element instead of a
   * <button> (e.g. `<Button asChild><Link …/></Button>`). Kept API-compatible
   * with the previous Radix Slot implementation; internally this maps onto
   * Base UI's `render` prop, which merges props the same way.
   */
  asChild?: boolean;
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, children, ...props }, ref) => {
    if (asChild && React.isValidElement(children)) {
      // Radix-Slot-equivalent composition: merge the button's classes and
      // remaining props onto the child element (child's own props win) —
      // deliberately WITHOUT Base UI's button wiring. A Link rendered via
      // asChild must keep its link semantics; Base UI's render prop with
      // nativeButton={false} injects role="button" onto the anchor
      // (verified in the Storybook AsChild story), which the old Slot
      // behavior never did. Note: unlike Slot, handlers are not composed —
      // no asChild call site passes handlers on the Button side.
      const child = children as React.ReactElement<Record<string, unknown>>;
      const childClassName = (child.props as { className?: string }).className;
      return React.cloneElement(child, {
        ...props,
        ...(child.props as Record<string, unknown>),
        className: cn(buttonVariants({ variant, size, className }), childClassName),
        ref,
      } as Record<string, unknown>);
    }
    return (
      <ButtonPrimitive
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        {...props}
      >
        {children}
      </ButtonPrimitive>
    );
  },
);
Button.displayName = "Button";
