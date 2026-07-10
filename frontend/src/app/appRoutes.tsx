import { Navigate, Route, Routes } from "react-router-dom";

import { ForgotPasswordPage } from "@/features/auth/ForgotPasswordPage";
import { ImpersonateLanding } from "@/features/auth/ImpersonateLandingPage";
import { LoginPage } from "@/features/auth/LoginPage";
import { OnboardingPage } from "@/features/auth/OnboardingPage";
import { RegisterPage } from "@/features/auth/RegisterPage";
import { RequireAuth } from "@/features/auth/RequireAuth";
import { ResetPasswordPage } from "@/features/auth/ResetPasswordPage";
import { StudentFeedbackPage } from "@/features/student-wizard/feedback/StudentFeedbackPage";
import { StudentWizardPage } from "@/features/student-wizard/StudentWizardPage";

// ---- app.careero.app — student CV builder only ------------------------
//
// The wider freelance / career-OS surface (jobs, personas, portfolio,
// applications, analytics, career fitness, etc.) is intentionally *not*
// mounted here. All that code is still in the repo — it now lives under
// src/features/professional/ — the routes are simply not registered. To
// bring it back, restore the AppLayout branch from git history (see
// commit 4c18fb7 and earlier) and point it at the relocated files.
//
// Every authenticated user lands directly in the student wizard;
// unauthenticated users get bounced to /login.

export function AppRoutes() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route path="/forgot-password" element={<ForgotPasswordPage />} />
      <Route path="/reset-password" element={<ResetPasswordPage />} />
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
