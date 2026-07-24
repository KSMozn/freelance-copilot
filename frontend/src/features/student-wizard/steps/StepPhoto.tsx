import { useEffect, useRef, useState } from "react";
import { toast } from "sonner";

import { useCoachPhoto } from "@/features/student-wizard/coaching/coachingApi";
import { CoachWarnings } from "@/features/student-wizard/coaching/CoachWarnings";
import type { CoachWarning } from "@/features/student-wizard/coaching/coachingTypes";
import { PhotoPositioner } from "@/features/student-wizard/PhotoPositioner";
import {
  useStudentPhotoBlob,
  useStudentProfile,
  useUpdateStudentProfile,
  useUploadStudentPhoto,
} from "@/features/student-wizard/studentApi";
import { registerPendingSave } from "@/shared/lib/pendingSaves";
import { Button } from "@/shared/ui/button";

export function StepPhoto({ onSaved }: { onSaved: () => Promise<void> | void }) {
  const { data: profile } = useStudentProfile();
  const upload = useUploadStudentPhoto();
  const coach = useCoachPhoto();
  const updateProfile = useUpdateStudentProfile();
  const photoUrl = useStudentPhotoBlob(profile?.photo_file_id);
  const [warnings, setWarnings] = useState<CoachWarning[]>([]);
  const [summary, setSummary] = useState<string | null>(null);
  const [confirmed, setConfirmed] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const busy = upload.isPending || coach.isPending;

  async function onPick(file: File) {
    const judgement = await coach.mutateAsync(file).catch(() => null);
    if (judgement) {
      setWarnings(judgement.warnings);
      setSummary(judgement.summary);
    }
    await upload.mutateAsync(file);
    toast.success("Photo saved");
  }

  // Debounce autosave for the crop transform — the positioner fires
  // `onChange` on every pointer settle and every wheel tick.
  const saveTransformRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const pendingTransformRef = useRef<{
    photo_offset_x: number;
    photo_offset_y: number;
    photo_zoom: number;
  } | null>(null);
  const updateProfileRef = useRef(updateProfile);
  updateProfileRef.current = updateProfile;

  async function flushTransform() {
    if (saveTransformRef.current) clearTimeout(saveTransformRef.current);
    const pending = pendingTransformRef.current;
    pendingTransformRef.current = null;
    saveTransformRef.current = null;
    if (pending) await updateProfileRef.current.mutateAsync(pending);
  }

  useEffect(() => {
    const unregister = registerPendingSave(flushTransform);
    return () => {
      unregister();
      void flushTransform().catch(() => undefined);
    };
  }, []);

  function saveTransform(next: {
    photo_offset_x: number;
    photo_offset_y: number;
    photo_zoom: number;
  }) {
    if (saveTransformRef.current) clearTimeout(saveTransformRef.current);
    pendingTransformRef.current = next;
    saveTransformRef.current = setTimeout(() => {
      pendingTransformRef.current = null;
      saveTransformRef.current = null;
      void updateProfile.mutateAsync(next).catch(() => undefined);
    }, 250);
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-col items-center gap-4 rounded-lg border border-border/60 bg-muted/20 p-4 sm:flex-row sm:gap-5">
        {photoUrl ? (
          <PhotoPositioner
            photoUrl={photoUrl}
            offsetX={profile?.photo_offset_x ?? 50}
            offsetY={profile?.photo_offset_y ?? 50}
            zoom={profile?.photo_zoom ?? 100}
            onChange={saveTransform}
          />
        ) : (
          <div className="grid h-28 w-28 shrink-0 place-items-center rounded-full bg-muted text-center text-xs text-muted-foreground ring-1 ring-border">
            No photo
          </div>
        )}
        <div className="flex flex-col items-center gap-1.5 sm:items-start">
          <Button
            type="button"
            variant="outline"
            onClick={() => fileInputRef.current?.click()}
            disabled={busy}
          >
            {busy ? "Uploading…" : photoUrl ? "Replace photo" : "Upload photo"}
          </Button>
          <p className="text-xs text-muted-foreground">JPG, PNG or WebP · square works best.</p>
          {photoUrl && (
            <p className="text-xs text-muted-foreground">Drag to reposition · scroll to zoom.</p>
          )}
          <input
            ref={fileInputRef}
            type="file"
            accept="image/jpeg,image/png,image/webp"
            className="hidden"
            onChange={(e) => {
              const f = e.target.files?.[0];
              if (f) void onPick(f);
              e.target.value = "";
            }}
          />
        </div>
      </div>
      {summary && (
        <p className="text-sm text-muted-foreground">
          <span className="font-medium">Reviewer:</span> {summary}
        </p>
      )}
      <CoachWarnings warnings={warnings} />
      {warnings.length > 0 && (
        <label className="flex items-center gap-2 text-xs text-muted-foreground">
          <input
            type="checkbox"
            checked={confirmed}
            onChange={(e) => setConfirmed(e.target.checked)}
          />
          I'm happy with this photo.
        </label>
      )}
      <div>
        <Button onClick={() => void onSaved()} disabled={warnings.length > 0 && !confirmed}>
          Continue
        </Button>
      </div>
    </div>
  );
}
