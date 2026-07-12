import { useEffect, useRef, useState } from "react";

interface PhotoPositionerProps {
  photoUrl: string;
  offsetX: number; // 0-100
  offsetY: number; // 0-100
  zoom: number; // 100-300
  onChange: (next: { photo_offset_x: number; photo_offset_y: number; photo_zoom: number }) => void;
  sizePx?: number;
}

const MIN_ZOOM = 100;
const MAX_ZOOM = 300;
const WHEEL_STEP = 5; // percent per wheel tick

const clamp = (n: number, lo: number, hi: number) => Math.max(lo, Math.min(hi, n));

/**
 * Facebook-style crop control. Renders the uploaded photo inside a
 * circular frame; the student drags to pan and scrolls to zoom. Local
 * state tracks the transform mid-gesture so paint is smooth; `onChange`
 * fires on every settled value so the parent can autosave.
 *
 * Uses CSS `background-image` + `background-size` + `background-position`
 * (rather than <img object-fit>) because that trio composes cleanly
 * with zoom-and-pan math on both the client and the server-rendered
 * CV template.
 */
export function PhotoPositioner({
  photoUrl,
  offsetX,
  offsetY,
  zoom,
  onChange,
  sizePx = 112,
}: PhotoPositionerProps) {
  const [x, setX] = useState(offsetX);
  const [y, setY] = useState(offsetY);
  const [z, setZ] = useState(zoom);
  const [dragging, setDragging] = useState(false);

  // Sync in from props whenever the parent-loaded profile changes
  // (e.g. reload restores the persisted values).
  useEffect(() => setX(offsetX), [offsetX]);
  useEffect(() => setY(offsetY), [offsetY]);
  useEffect(() => setZ(zoom), [zoom]);

  const rootRef = useRef<HTMLDivElement | null>(null);
  const startRef = useRef<{
    px: number;
    py: number;
    ox: number;
    oy: number;
  } | null>(null);

  function beginDrag(e: React.PointerEvent<HTMLDivElement>) {
    if (!rootRef.current) return;
    rootRef.current.setPointerCapture(e.pointerId);
    startRef.current = { px: e.clientX, py: e.clientY, ox: x, oy: y };
    setDragging(true);
  }

  function moveDrag(e: React.PointerEvent<HTMLDivElement>) {
    if (!dragging || !startRef.current) return;
    const { px, py, ox, oy } = startRef.current;
    // Drag-right pans the visible window left within the image, which
    // in `background-position` percentage terms means SUBTRACTING x.
    const dx = ((e.clientX - px) / sizePx) * 100;
    const dy = ((e.clientY - py) / sizePx) * 100;
    setX(clamp(ox - dx, 0, 100));
    setY(clamp(oy - dy, 0, 100));
  }

  function endDrag(e: React.PointerEvent<HTMLDivElement>) {
    if (!dragging) return;
    rootRef.current?.releasePointerCapture(e.pointerId);
    setDragging(false);
    startRef.current = null;
    // Settle: notify the parent so it can autosave.
    onChange({
      photo_offset_x: Math.round(x),
      photo_offset_y: Math.round(y),
      photo_zoom: Math.round(z),
    });
  }

  // Wheel needs `passive: false` so we can preventDefault the page
  // scroll while the pointer is over the circle. React's onWheel is
  // always passive; attach imperatively.
  useEffect(() => {
    const el = rootRef.current;
    if (!el) return;
    const handler = (e: WheelEvent) => {
      e.preventDefault();
      setZ((prev) => {
        const dir = e.deltaY < 0 ? 1 : -1;
        const next = clamp(prev + dir * WHEEL_STEP, MIN_ZOOM, MAX_ZOOM);
        // Fire settled value up so autosave lands (debounced by parent).
        onChange({
          photo_offset_x: Math.round(x),
          photo_offset_y: Math.round(y),
          photo_zoom: Math.round(next),
        });
        return next;
      });
    };
    el.addEventListener("wheel", handler, { passive: false });
    return () => el.removeEventListener("wheel", handler);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [x, y]);

  return (
    <div className="space-y-2">
      <div
        ref={rootRef}
        onPointerDown={beginDrag}
        onPointerMove={moveDrag}
        onPointerUp={endDrag}
        onPointerCancel={endDrag}
        role="img"
        aria-label="Profile photo — drag to reposition, scroll to zoom"
        className="select-none ring-1 ring-border"
        style={{
          width: sizePx,
          height: sizePx,
          borderRadius: "50%",
          backgroundImage: `url("${photoUrl}")`,
          backgroundPosition: `${x}% ${y}%`,
          backgroundSize: `${z}%`,
          backgroundRepeat: "no-repeat",
          cursor: dragging ? "grabbing" : "grab",
          touchAction: "none",
        }}
      />
      <p className="text-xs text-muted-foreground">Drag to reposition · scroll to zoom</p>
    </div>
  );
}
