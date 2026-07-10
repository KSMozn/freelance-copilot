import { lazy, Suspense } from "react";

import { isAdminSurface } from "@/app/apiClient";

// Each surface tree is a lazy chunk: a student session never downloads the
// admin console and vice versa. The surface is fixed at module load (from
// the hostname), so exactly one chunk is ever fetched per session.
const AdminRoutes = lazy(() =>
  import("@/app/adminRoutes").then((m) => ({ default: m.AdminRoutes })),
);
const AppRoutes = lazy(() => import("@/app/appRoutes").then((m) => ({ default: m.AppRoutes })));

export function AppRouter() {
  return <Suspense fallback={null}>{isAdminSurface ? <AdminRoutes /> : <AppRoutes />}</Suspense>;
}
