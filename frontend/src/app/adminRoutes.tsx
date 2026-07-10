import { Navigate, Route, Routes } from "react-router-dom";

import { AdminActivityPage } from "@/features/admin/AdminActivityPage";
import { AdminEmailsPage } from "@/features/admin/AdminEmailsPage";
import { AdminFeedbackPage } from "@/features/admin/AdminFeedbackPage";
import { AdminLayout } from "@/features/admin/AdminLayout";
import { AdminLoginPage } from "@/features/admin/AdminLoginPage";
import { AdminOverviewPage } from "@/features/admin/AdminOverviewPage";
import { AdminTemplatesPage } from "@/features/admin/AdminTemplatesPage";
import { AdminUserDetailPage } from "@/features/admin/AdminUserDetailPage";
import { AdminUsersPage } from "@/features/admin/AdminUsersPage";

// ---- admin.careero.app — admin surface only ---------------------------

export function AdminRoutes() {
  return (
    <Routes>
      <Route path="/login" element={<AdminLoginPage />} />
      <Route path="/" element={<AdminLayout />}>
        <Route index element={<Navigate to="/overview" replace />} />
        <Route path="overview" element={<AdminOverviewPage />} />
        <Route path="users" element={<AdminUsersPage />} />
        <Route path="users/:id" element={<AdminUserDetailPage />} />
        <Route path="feedback" element={<AdminFeedbackPage />} />
        <Route path="emails" element={<AdminEmailsPage />} />
        <Route path="templates" element={<AdminTemplatesPage />} />
        <Route path="activity" element={<AdminActivityPage />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
