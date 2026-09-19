import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Link, Route, Routes } from "react-router-dom";

import { ProviderBadge } from "@/components/ProviderBadge";
import { Toaster } from "@/components/ui/sonner";
import { CustomerDetail } from "@/pages/CustomerDetail";
import { Dashboard } from "@/pages/Dashboard";

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: 1, refetchOnWindowFocus: false } },
});

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <div className="min-h-screen">
          <nav className="border-b bg-card">
            <div className="mx-auto flex max-w-5xl items-center justify-between px-4 py-3">
              <Link to="/" className="font-semibold tracking-tight">
                Micro-CRM <span className="font-normal text-muted-foreground">· who needs attention today</span>
              </Link>
              <ProviderBadge />
            </div>
          </nav>
          <main className="mx-auto max-w-5xl px-4 py-6">
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/customers/:id" element={<CustomerDetail />} />
            </Routes>
          </main>
        </div>
        <Toaster richColors position="bottom-right" />
      </BrowserRouter>
    </QueryClientProvider>
  );
}
