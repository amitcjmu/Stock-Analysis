
import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import Index from "./pages/Index";
import Assess from "./pages/Assess";
import Discovery from "./pages/Discovery";
import DiscoveryIndex from "./pages/discovery/Index";
import Inventory from "./pages/discovery/Inventory";
import Dependencies from "./pages/discovery/Dependencies";
import Scan from "./pages/discovery/Scan";
import AssessIndex from "./pages/assess/Index";
import Treatment from "./pages/assess/Treatment";
import WavePlanning from "./pages/assess/WavePlanning";
import Roadmap from "./pages/assess/Roadmap";
import Editor from "./pages/assess/Editor";
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
          <Route path="/discovery/overview" element={<DiscoveryIndex />} />
          <Route path="/discovery/inventory" element={<Inventory />} />
          <Route path="/discovery/dependencies" element={<Dependencies />} />
          <Route path="/discovery/scan" element={<Scan />} />
          <Route path="/assess" element={<Assess />} />
          <Route path="/assess/overview" element={<AssessIndex />} />
          <Route path="/assess/treatment" element={<Treatment />} />
          <Route path="/assess/waveplanning" element={<WavePlanning />} />
          <Route path="/assess/roadmap" element={<Roadmap />} />
          <Route path="/assess/editor" element={<Editor />} />
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
