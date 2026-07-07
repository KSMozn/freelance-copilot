import { QueryClientProvider } from "@tanstack/react-query";
import { Toaster } from "sonner";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";

import { RequireAuth } from "@/components/RequireAuth";
import { isAdminSurface } from "@/lib/api";
import { queryClient } from "@/lib/queryClient";
import { ImpersonateLanding } from "@/pages/ImpersonateLanding";
import { LoginPage } from "@/pages/Login";
import { OnboardingPage } from "@/pages/Onboarding";
import { RegisterPage } from "@/pages/Register";
import { StudentFeedbackPage } from "@/pages/StudentFeedback";
import { StudentWizardPage } from "@/pages/StudentWizard";
import { AdminActivityPage } from "@/pages/admin/AdminActivity";
import { AdminEmailsPage } from "@/pages/admin/AdminEmails";
import { AdminFeedbackPage } from "@/pages/admin/AdminFeedback";
import { AdminLayout } from "@/pages/admin/AdminLayout";
import { AdminLoginPage } from "@/pages/admin/AdminLoginPage";
import { AdminOverviewPage } from "@/pages/admin/AdminOverview";
import { AdminTemplatesPage } from "@/pages/admin/AdminTemplatesPage";
import { AdminUserDetailPage } from "@/pages/admin/AdminUserDetail";
import { AdminUsersPage } from "@/pages/admin/AdminUsers";

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        {isAdminSurface ? <AdminRoutes /> : <AppRoutes />}
      </BrowserRouter>
      <Toaster richColors position="top-right" theme="dark" />
    </QueryClientProvider>
  );
}

// ---- admin.careero.app — admin surface only ---------------------------

function AdminRoutes() {
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

// ---- app.careero.app — student CV builder only ------------------------
//
// The wider freelance / career-OS surface (jobs, personas, portfolio,
// applications, analytics, career fitness, etc.) is intentionally *not*
// mounted here. All that code is still in the repo — the routes are
// simply not registered. To bring it back, restore the AppLayout branch
// from git history (see commit 4c18fb7 and earlier).
//
// Every authenticated user lands directly in the student wizard;
// unauthenticated users get bounced to /login.

function AppRoutes() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route path="/impersonate" element={<ImpersonateLanding />} />
      <Route
        path="/student"
        element={
          <RequireAuth>
            <StudentWizardPage />
          </RequireAuth>
        }
      />
      <Route
        path="/feedback"
        element={
          <RequireAuth>
            <StudentFeedbackPage />
          </RequireAuth>
        }
      />
      <Route
        path="/onboarding"
        element={
          <RequireAuth>
            <OnboardingPage />
          </RequireAuth>
        }
      />
      {/* Root + any unknown path → wizard for authed users, /login otherwise
          (RequireAuth handles the auth redirect). */}
      <Route
        path="*"
        element={
          <RequireAuth>
            <Navigate to="/student" replace />
          </RequireAuth>
        }
      />
    </Routes>
  );
}
