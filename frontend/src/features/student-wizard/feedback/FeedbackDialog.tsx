import { Dialog } from "@base-ui/react/dialog";
import { X } from "lucide-react";

import { cn } from "@/shared/lib/utils";
import { FeedbackForm } from "@/features/student-wizard/feedback/FeedbackForm";

export function FeedbackDialog({ triggerClassName }: { triggerClassName?: string }) {
  return (
    <Dialog.Root>
      <Dialog.Trigger
        className={cn(
          "text-muted-foreground transition-colors hover:text-foreground",
          triggerClassName,
        )}
      >
        Send feedback →
      </Dialog.Trigger>
      <Dialog.Portal>
        <Dialog.Backdrop className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm transition-opacity duration-150 data-[ending-style]:opacity-0 data-[starting-style]:opacity-0" />
        <Dialog.Popup className="fixed left-1/2 top-1/2 z-50 w-[calc(100vw-2rem)] max-w-lg -translate-x-1/2 -translate-y-1/2 rounded-2xl border border-border bg-card p-6 text-card-foreground shadow-xl transition-all duration-150 data-[ending-style]:scale-95 data-[starting-style]:scale-95 data-[ending-style]:opacity-0 data-[starting-style]:opacity-0">
          <div className="mb-4 flex items-start justify-between gap-4">
            <div className="space-y-1">
              <Dialog.Title className="text-lg font-semibold tracking-tight">Feedback</Dialog.Title>
              <Dialog.Description className="text-sm text-muted-foreground">
                Bugs, gripes, features you wish existed, anything. Every message lands in our inbox.
              </Dialog.Description>
            </div>
            <Dialog.Close
              aria-label="Close"
              className="-mr-1 -mt-1 rounded-md p-1 text-muted-foreground transition-colors hover:text-foreground"
            >
              <X className="h-4 w-4" />
            </Dialog.Close>
          </div>
          <FeedbackForm />
        </Dialog.Popup>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
