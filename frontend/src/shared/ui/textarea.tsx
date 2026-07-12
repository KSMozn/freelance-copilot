import * as React from "react";

import { cn } from "@/shared/lib/utils";

export const Textarea = React.forwardRef<
  HTMLTextAreaElement,
  React.TextareaHTMLAttributes<HTMLTextAreaElement>
>(({ className, spellCheck = true, ...props }, ref) => (
  // Textareas hold prose (summaries, descriptions) — spellcheck-on by
  // default; caller can pass spellCheck={false} for structured input.
  <textarea
    ref={ref}
    spellCheck={spellCheck}
    className={cn(
      "flex min-h-[100px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50",
      className,
    )}
    {...props}
  />
));
Textarea.displayName = "Textarea";
