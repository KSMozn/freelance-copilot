import { QueryClientProvider } from "@tanstack/react-query";
import { Toaster } from "sonner";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";

import { AppLayout } from "@/components/layout/AppLayout";
import { RequireAuth } from "@/components/RequireAuth";
import { queryClient } from "@/lib/queryClient";
import { AnalyticsPage } from "@/pages/Analytics";
import { ApplicationDetailPage } from "@/pages/ApplicationDetail";
import { ApplicationsPage } from "@/pages/Applications";
import { DashboardPage } from "@/pages/Dashboard";
import { JobCreatePage } from "@/pages/JobCreate";
import { JobDetailPage } from "@/pages/JobDetail";
import { JobImportPage } from "@/pages/JobImport";
import { JobsPage } from "@/pages/Jobs";
import { LoginPage } from "@/pages/Login";
import { OnboardingPage } from "@/pages/Onboarding";
import { PersonaNewPage } from "@/pages/PersonaNew";
import { PersonasPage } from "@/pages/Personas";
import { PlaceholderPage } from "@/pages/Placeholder";
import { PortfolioPage } from "@/pages/Portfolio";
import { PortfolioFormPage } from "@/pages/PortfolioForm";
import { RegisterPage } from "@/pages/Register";
import { RepositoriesPage } from "@/pages/Repositories";
import { ResumeFormPage } from "@/pages/ResumeForm";
import { ResumesPage } from "@/pages/Resumes";

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
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
                <AppLayout />
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
            <Route path="/analytics" element={<AnalyticsPage />} />
            <Route path="/settings" element={<PlaceholderPage title="Settings" phase="Phase 10" />} />
          </Route>
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
      <Toaster richColors position="top-right" theme="dark" />
    </QueryClientProvider>
  );
}
