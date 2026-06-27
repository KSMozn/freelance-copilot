import { QueryClientProvider } from "@tanstack/react-query";
import { Toaster } from "sonner";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";

import { AppLayout } from "@/components/layout/AppLayout";
import { RequireAuth } from "@/components/RequireAuth";
import { queryClient } from "@/lib/queryClient";
import { DashboardPage } from "@/pages/Dashboard";
import { JobCreatePage } from "@/pages/JobCreate";
import { JobDetailPage } from "@/pages/JobDetail";
import { JobsPage } from "@/pages/Jobs";
import { LoginPage } from "@/pages/Login";
import { PlaceholderPage } from "@/pages/Placeholder";
import { RegisterPage } from "@/pages/Register";

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
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
            <Route path="/jobs/:id" element={<JobDetailPage />} />
            <Route path="/portfolio" element={<PlaceholderPage title="Portfolio" phase="Phase 3" />} />
            <Route path="/resumes" element={<PlaceholderPage title="Resumes" phase="Phase 5" />} />
            <Route
              path="/applications"
              element={<PlaceholderPage title="Applications" phase="Phase 7" />}
            />
            <Route
              path="/analytics"
              element={<PlaceholderPage title="Analytics" phase="Phase 8" />}
            />
            <Route path="/settings" element={<PlaceholderPage title="Settings" phase="Phase 10" />} />
          </Route>
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
      <Toaster richColors position="top-right" theme="dark" />
    </QueryClientProvider>
  );
}
