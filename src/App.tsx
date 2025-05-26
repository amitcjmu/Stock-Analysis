
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
import PlanIndex from "./pages/plan/Index";
import Timeline from "./pages/plan/Timeline";
import Resource from "./pages/plan/Resource";
import Target from "./pages/plan/Target";
import Execute from "./pages/Execute";
import ExecuteIndex from "./pages/execute/Index";
import Rehost from "./pages/execute/Rehost";
import Replatform from "./pages/execute/Replatform";
import Cutovers from "./pages/execute/Cutovers";
import Reports from "./pages/execute/Reports";
import Modernize from "./pages/Modernize";
import ModernizeIndex from "./pages/modernize/Index";
import Refactor from "./pages/modernize/Refactor";
import Rearchitect from "./pages/modernize/Rearchitect";
import Rewrite from "./pages/modernize/Rewrite";
import Progress from "./pages/modernize/Progress";
import Decommission from "./pages/Decommission";
import DecommissionIndex from "./pages/decommission/Index";
import DecommissionPlanning from "./pages/decommission/Planning";
import DataRetention from "./pages/decommission/DataRetention";
import DecommissionExecution from "./pages/decommission/Execution";
import DecommissionValidation from "./pages/decommission/Validation";
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
          <Route path="/plan/overview" element={<PlanIndex />} />
          <Route path="/plan/timeline" element={<Timeline />} />
          <Route path="/plan/resource" element={<Resource />} />
          <Route path="/plan/target" element={<Target />} />
          <Route path="/execute" element={<Execute />} />
          <Route path="/execute/overview" element={<ExecuteIndex />} />
          <Route path="/execute/rehost" element={<Rehost />} />
          <Route path="/execute/replatform" element={<Replatform />} />
          <Route path="/execute/cutovers" element={<Cutovers />} />
          <Route path="/execute/reports" element={<Reports />} />
          <Route path="/modernize" element={<Modernize />} />
          <Route path="/modernize/overview" element={<ModernizeIndex />} />
          <Route path="/modernize/refactor" element={<Refactor />} />
          <Route path="/modernize/rearchitect" element={<Rearchitect />} />
          <Route path="/modernize/rewrite" element={<Rewrite />} />
          <Route path="/modernize/progress" element={<Progress />} />
          <Route path="/decommission" element={<Decommission />} />
          <Route path="/decommission/overview" element={<DecommissionIndex />} />
          <Route path="/decommission/planning" element={<DecommissionPlanning />} />
          <Route path="/decommission/dataretention" element={<DataRetention />} />
          <Route path="/decommission/execution" element={<DecommissionExecution />} />
          <Route path="/decommission/validation" element={<DecommissionValidation />} />
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
