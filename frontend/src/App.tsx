import React from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ToastProvider } from "./components/ui/Toast";
import { AppLayout } from "./components/layout/AppLayout";
import { Home } from "./pages/Home";
import { Analytics } from "./pages/Analytics";
import { InvoiceDetail } from "./pages/InvoiceDetail";
import { SettingsPage } from "./pages/SettingsPage";
import { Login } from "./pages/Login";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      staleTime: 1000 * 60, // 1 minute
      retry: 1,
    },
  },
});

export const App: React.FC = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <ToastProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/" element={<AppLayout />}>
              <Route index element={<Home />} />
              <Route path="analyses" element={<Analytics />} />
              <Route path="facture" element={<InvoiceDetail />} />
              <Route path="reglages" element={<SettingsPage />} />
            </Route>
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </BrowserRouter>
      </ToastProvider>
    </QueryClientProvider>
  );
};

export default App;
