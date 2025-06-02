import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { ChatFeedbackProvider } from "./contexts/ChatFeedbackContext";
import GlobalChatFeedback from "./components/GlobalChatFeedback";
import Index from "./pages/Index";
import Assess from "./pages/Assess";
import Discovery from "./pages/Discovery";
import DiscoveryIndex from "./pages/discovery/Index";
import DataImport from "./pages/discovery/CMDBImport";
import Inventory from "./pages/discovery/Inventory";
import Dependencies from "./pages/discovery/Dependencies";
import DataCleansing from "./pages/discovery/DataCleansing";
import AttributeMapping from "./pages/discovery/AttributeMapping";
import TechDebtAnalysis from "./pages/discovery/TechDebtAnalysis";
import DiscoveryDashboard from "./pages/discovery/DiscoveryDashboard";
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
import CloudComparison from "./pages/finops/CloudComparison";
import SavingsAnalysis from "./pages/finops/SavingsAnalysis";
import CostAnalysis from "./pages/finops/CostAnalysis";
import WaveBreakdown from "./pages/finops/WaveBreakdown";
import CostTrends from "./pages/finops/CostTrends";
import BudgetAlerts from "./pages/finops/BudgetAlerts";
import Observability from "./pages/Observability";
import AgentMonitoring from "./pages/AgentMonitoring";
import FeedbackView from "./pages/FeedbackView";
import NotFound from "./pages/NotFound";
import AdminDashboard from "./pages/admin/AdminDashboard";
import ClientManagement from "./pages/admin/ClientManagement";
import EngagementManagement from "./pages/admin/EngagementManagement";
import UserApprovals from "./pages/admin/UserApprovals";

const queryClient = new QueryClient();

const App = () => (
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>
      <Toaster />
      <Sonner />
      <BrowserRouter>
        <ChatFeedbackProvider>
        <Routes>
          <Route path="/" element={<Index />} />
          <Route path="/discovery" element={<Discovery />} />
          <Route path="/discovery/overview" element={<DiscoveryDashboard />} />
          <Route path="/discovery/dashboard" element={<DiscoveryDashboard />} />
          <Route path="/discovery/data-import" element={<DataImport />} />
          <Route path="/discovery/inventory" element={<Inventory />} />
          <Route path="/discovery/data-cleansing" element={<DataCleansing />} />
          <Route path="/discovery/attribute-mapping" element={<AttributeMapping />} />
          <Route path="/discovery/tech-debt-analysis" element={<TechDebtAnalysis />} />
          <Route path="/discovery/dependencies" element={<Dependencies />} />
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
          <Route path="/finops/cloud-comparison" element={<CloudComparison />} />
          <Route path="/finops/savings-analysis" element={<SavingsAnalysis />} />
          <Route path="/finops/cost-analysis" element={<CostAnalysis />} />
          <Route path="/finops/wave-breakdown" element={<WaveBreakdown />} />
          <Route path="/finops/cost-trends" element={<CostTrends />} />
          <Route path="/finops/budget-alerts" element={<BudgetAlerts />} />
          <Route path="/observability" element={<Observability />} />
          <Route path="/observability/agent-monitoring" element={<AgentMonitoring />} />
          <Route path="/feedback-view" element={<FeedbackView />} />
          {/* Admin Routes */}
          <Route path="/admin" element={<AdminDashboard />} />
          <Route path="/admin/dashboard" element={<AdminDashboard />} />
          <Route path="/admin/clients" element={<ClientManagement />} />
          <Route path="/admin/engagements" element={<EngagementManagement />} />
          <Route path="/admin/users/approvals" element={<UserApprovals />} />
          {/* ADD ALL CUSTOM ROUTES ABOVE THE CATCH-ALL "*" ROUTE */}
          <Route path="*" element={<NotFound />} />
        </Routes>
        <GlobalChatFeedback />
      </ChatFeedbackProvider>
    </BrowserRouter>
  </TooltipProvider>
</QueryClientProvider>
);

export default App;
