import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { ErrorBoundary } from "./components/ErrorBoundary";
import { AppRouter } from "./router";
import "./index.css";

const queryClient = new QueryClient();
const REPO = import.meta.env.VITE_GITHUB_REPO ?? "jreakin/jre-vidget";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <ErrorBoundary repo={REPO}>
      <QueryClientProvider client={queryClient}>
        <AppRouter />
      </QueryClientProvider>
    </ErrorBoundary>
  </StrictMode>,
);
