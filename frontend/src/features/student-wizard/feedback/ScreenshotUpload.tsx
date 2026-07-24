import { Image as ImageIcon, Upload, X } from "lucide-react";
import { useEffect, useRef, useState } from "react";

import { SCREENSHOT_ACCEPT_ATTR } from "@/features/student-wizard/feedback/feedbackSchema";
import { cn } from "@/shared/lib/utils";

interface ScreenshotUploadProps {
  value: File | null;
  onSelect: (file: File | null) => void;
  error?: string | null;
  disabled?: boolean;
  labelId?: string;
}

export function ScreenshotUpload({
  value,
  onSelect,
  error,
  disabled,
  labelId,
}: ScreenshotUploadProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragOver, setDragOver] = useState(false);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);

  useEffect(() => {
    if (!value || error) {
      setPreviewUrl(null);
      return;
    }
    const url = URL.createObjectURL(value);
    setPreviewUrl(url);
    return () => URL.revokeObjectURL(url);
  }, [value, error]);

  const openPicker = () => {
    if (!disabled) inputRef.current?.click();
  };

  const pick = (file: File | null) => {
    onSelect(file);
    if (inputRef.current) inputRef.current.value = "";
  };

  const errorId = "feedback-screenshot-error";

  return (
    <div role="group" aria-labelledby={labelId} aria-describedby={error ? errorId : undefined}>
      <input
        ref={inputRef}
        type="file"
        accept={SCREENSHOT_ACCEPT_ATTR}
        className="sr-only"
        tabIndex={-1}
        aria-hidden="true"
        disabled={disabled}
        onChange={(e) => pick(e.target.files?.[0] ?? null)}
      />

      {value ? (
        <div className="rounded-md border border-input bg-background p-3">
          <div className="flex items-center gap-3">
            {previewUrl ? (
              <img
                src={previewUrl}
                alt={`Preview of ${value.name}`}
                className="h-14 w-14 shrink-0 rounded object-cover"
              />
            ) : (
              <div className="flex h-14 w-14 shrink-0 items-center justify-center rounded bg-muted">
                <ImageIcon className="h-5 w-5 text-muted-foreground" aria-hidden />
              </div>
            )}
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-medium">{value.name}</p>
              <p className="text-xs text-muted-foreground">{formatBytes(value.size)}</p>
            </div>
            <div className="flex shrink-0 items-center gap-3">
              <button
                type="button"
                onClick={openPicker}
                disabled={disabled}
                className="text-xs text-primary hover:underline disabled:pointer-events-none disabled:opacity-50"
              >
                Replace
              </button>
              <button
                type="button"
                onClick={() => pick(null)}
                disabled={disabled}
                aria-label="Remove screenshot"
                className="inline-flex items-center gap-1 text-xs text-muted-foreground transition-colors hover:text-foreground disabled:pointer-events-none disabled:opacity-50"
              >
                <X className="h-3.5 w-3.5" aria-hidden />
                Remove
              </button>
            </div>
          </div>
        </div>
      ) : (
        <button
          type="button"
          onClick={openPicker}
          disabled={disabled}
          onDragOver={(e) => {
            e.preventDefault();
            if (!disabled) setDragOver(true);
          }}
          onDragLeave={() => setDragOver(false)}
          onDrop={(e) => {
            e.preventDefault();
            setDragOver(false);
            if (disabled) return;
            const file = e.dataTransfer.files?.[0];
            if (file) pick(file);
          }}
          className={cn(
            "flex w-full flex-col items-center justify-center gap-1.5 rounded-md border border-dashed border-input bg-background px-4 py-6 text-center transition-colors hover:bg-muted/50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50",
            dragOver && "border-primary bg-primary/5",
          )}
        >
          <Upload className="h-5 w-5 text-muted-foreground" aria-hidden />
          <span className="text-sm font-medium">Drag &amp; drop or click to upload</span>
          <span className="text-xs text-muted-foreground">PNG, JPEG, or WebP · up to 5 MB</span>
        </button>
      )}

      {error && (
        <p id={errorId} role="alert" className="mt-1.5 text-xs text-destructive">
          {error}
        </p>
      )}
    </div>
  );
}

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${Math.round(bytes / 1024)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}
