
import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import Index from "./pages/Index";
import Assess from "./pages/Assess";
import Discovery from "./pages/Discovery";
import Plan from "./pages/Plan";
import Execute from "./pages/Execute";
import Modernize from "./pages/Modernize";
import Decommission from "./pages/Decommission";
import FinOps from "./pages/FinOps";
import Observability from "./pages/Observability";
import NotFound from "./pages/NotFound";

const queryClient = new QueryClient();

const App = () => (
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>
      <Toaster />
      <Sonner />
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Index />} />
          <Route path="/discovery" element={<Discovery />} />
          <Route path="/assess" element={<Assess />} />
          <Route path="/plan" element={<Plan />} />
          <Route path="/execute" element={<Execute />} />
          <Route path="/modernize" element={<Modernize />} />
          <Route path="/decommission" element={<Decommission />} />
          <Route path="/finops" element={<FinOps />} />
          <Route path="/observability" element={<Observability />} />
          {/* ADD ALL CUSTOM ROUTES ABOVE THE CATCH-ALL "*" ROUTE */}
          <Route path="*" element={<NotFound />} />
        </Routes>
      </BrowserRouter>
    </TooltipProvider>
  </QueryClientProvider>
);

export default App;
