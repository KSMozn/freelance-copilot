import { QueryClientProvider } from "@tanstack/react-query";
import { Toaster } from "sonner";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";

import { AppLayout } from "@/components/layout/AppLayout";
import { RequireAuth } from "@/components/RequireAuth";
import { isAdminSurface } from "@/lib/api";
import { queryClient } from "@/lib/queryClient";
import { AnalyticsPage } from "@/pages/Analytics";
import { ApplicationDetailPage } from "@/pages/ApplicationDetail";
import { ApplicationsPage } from "@/pages/Applications";
import { DashboardPage } from "@/pages/Dashboard";
import { ImpersonateLanding } from "@/pages/ImpersonateLanding";
import { JobCreatePage } from "@/pages/JobCreate";
import { JobDetailPage } from "@/pages/JobDetail";
import { JobImportPage } from "@/pages/JobImport";
import { JobsPage } from "@/pages/Jobs";
import { CareerFitnessPage } from "@/pages/CareerFitness";
import { LoginPage } from "@/pages/Login";
import { OnboardingPage } from "@/pages/Onboarding";
import { PersonaNewPage } from "@/pages/PersonaNew";
import { PersonasPage } from "@/pages/Personas";
import { PlaceholderPage } from "@/pages/Placeholder";
import { SourcesPage } from "@/pages/Sources";
import { PortfolioPage } from "@/pages/Portfolio";
import { PortfolioFormPage } from "@/pages/PortfolioForm";
import { RegisterPage } from "@/pages/Register";
import { RepositoriesPage } from "@/pages/Repositories";
import { ResumeFormPage } from "@/pages/ResumeForm";
import { ResumesPage } from "@/pages/Resumes";
import { StudentFeedbackPage } from "@/pages/StudentFeedback";
import { StudentWizardPage } from "@/pages/StudentWizard";
import { AdminActivityPage } from "@/pages/admin/AdminActivity";
import { AdminLayout } from "@/pages/admin/AdminLayout";
import { AdminLoginPage } from "@/pages/admin/AdminLoginPage";
import { AdminOverviewPage } from "@/pages/admin/AdminOverview";
import { AdminTemplatesPage } from "@/pages/admin/AdminTemplatesPage";
import { AdminUserDetailPage } from "@/pages/admin/AdminUserDetail";
import { AdminUsersPage } from "@/pages/admin/AdminUsers";
import { useAuthStore } from "@/stores/auth";

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

// ---- admin.personaarmory.com — admin surface only ---------------------

function AdminRoutes() {
  return (
    <Routes>
      <Route path="/login" element={<AdminLoginPage />} />
      <Route path="/" element={<AdminLayout />}>
        <Route index element={<Navigate to="/overview" replace />} />
        <Route path="overview" element={<AdminOverviewPage />} />
        <Route path="users" element={<AdminUsersPage />} />
        <Route path="users/:id" element={<AdminUserDetailPage />} />
        <Route path="templates" element={<AdminTemplatesPage />} />
        <Route path="activity" element={<AdminActivityPage />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

// ---- app.personaarmory.com — student + freelancer surface -------------

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
      <Route
        element={
          <RequireAuth>
            <StudentGate>
              <AppLayout />
            </StudentGate>
          </RequireAuth>
        }
      >
        <Route index element={<DashboardPage />} />
        <Route path="/jobs" element={<JobsPage />} />
        <Route path="/jobs/new" element={<JobCreatePage />} />
        <Route path="/jobs/import" element={<JobImportPage />} />
        <Route path="/jobs/:id" element={<JobDetailPage />} />
        <Route path="/portfolio" element={<PortfolioPage />} />
        <Route path="/portfolio/new" element={<PortfolioFormPage />} />
        <Route path="/portfolio/:id" element={<PortfolioFormPage />} />
        <Route path="/repositories" element={<RepositoriesPage />} />
        <Route path="/resumes" element={<ResumesPage />} />
        <Route path="/resumes/new" element={<ResumeFormPage />} />
        <Route path="/resumes/:id" element={<ResumeFormPage />} />
        <Route path="/applications" element={<ApplicationsPage />} />
        <Route path="/applications/:id" element={<ApplicationDetailPage />} />
        <Route path="/personas" element={<PersonasPage />} />
        <Route path="/personas/new" element={<PersonaNewPage />} />
        <Route path="/sources" element={<SourcesPage />} />
        <Route path="/career-fitness" element={<CareerFitnessPage />} />
        <Route path="/analytics" element={<AnalyticsPage />} />
        <Route path="/settings" element={<PlaceholderPage title="Settings" phase="Phase 10" />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

// Students never see the freelancer/career-OS surface — they live in the
// wizard. Anyone else falls through to the existing app.
function StudentGate({ children }: { children: React.ReactNode }) {
  const user = useAuthStore((s) => s.user);
  if (user?.selected_persona_kind === "student") {
    return <Navigate to="/student" replace />;
  }
  return <>{children}</>;
}
