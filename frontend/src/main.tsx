import React from "react";
import ReactDOM from "react-dom/client";
import { QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter } from "react-router-dom";
import { Toaster } from "sonner";

import { queryClient } from "@/app/queryClient";
import { AppRouter } from "@/app/router";

import "@/shared/styles/globals.css";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AppRouter />
      </BrowserRouter>
      <Toaster richColors position="top-right" theme="dark" />
    </QueryClientProvider>
  </React.StrictMode>,
);
