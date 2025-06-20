import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Routes, Route } from "react-router-dom";
import { ChatFeedbackProvider } from "./contexts/ChatFeedbackContext";
import { AuthProvider, useAuth } from "./contexts/AuthContext";
import { SessionProvider } from "./contexts/SessionContext";
import { ClientProvider } from "./contexts/ClientContext";
// import { AppContextProvider } from "./hooks/useContext";
import GlobalChatFeedback from "./components/GlobalChatFeedback";
import Index from "./pages/Index";
import Login from "./pages/Login";
import Assess from "./pages/Assess";
import Discovery from "./pages/Discovery";
import DiscoveryIndex from "./pages/discovery/Index";
import DataImport from "./pages/discovery/CMDBImport";
import Inventory from "./pages/discovery/Inventory";
import Dependencies from "./pages/discovery/Dependencies";
import DataCleansing from "./pages/discovery/DataCleansing";
import AttributeMapping from "./pages/discovery/AttributeMapping";
import TechDebtAnalysis from "./pages/discovery/TechDebtAnalysis";
import DiscoveryDashboard from "./pages/discovery/EnhancedDiscoveryDashboard";
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
import LLMCosts from "./pages/finops/LLMCosts";
import WaveBreakdown from "./pages/finops/WaveBreakdown";
import CostTrends from "./pages/finops/CostTrends";
import BudgetAlerts from "./pages/finops/BudgetAlerts";
import Observability from "./pages/Observability";
import AgentMonitoring from "./pages/AgentMonitoring";
import FeedbackView from "./pages/FeedbackView";
import NotFound from "./pages/NotFound";
import AdminDashboard from "./pages/admin/AdminDashboard";
import ClientManagement from "./pages/admin/ClientManagement";
import ClientDetails from "./pages/admin/ClientDetails";
import EngagementManagement from "./pages/admin/EngagementManagement";
import EngagementDetails from "./pages/admin/EngagementDetails";
import UserApprovals from "./pages/admin/UserApprovals";
import CreateUser from "./pages/admin/CreateUser";
import CreateClient from "./pages/admin/CreateClient";
import CreateEngagement from "./pages/admin/CreateEngagement";
import UserProfile from "./pages/admin/UserProfile";
import PlatformAdmin from "./pages/admin/PlatformAdmin";
import AdminLayout from "./components/admin/AdminLayout";
import AdminRoute from "./components/admin/AdminRoute";

const queryClient = new QueryClient();

// Component to handle authenticated routes
const AuthenticatedApp = () => {
  const { isLoading, isAuthenticated } = useAuth();

  // Show loading screen while authentication is being determined
  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }

  return (
    <Routes>
              <Route path="/" element={<Index />} />
              <Route path="/login" element={<Login />} />
              <Route path="/discovery" element={<Discovery />} />
              <Route path="/discovery/overview" element={<DiscoveryDashboard />} />
              <Route path="/discovery/dashboard" element={<DiscoveryDashboard />} />
              <Route path="/discovery/import" element={<DataImport />} />
              <Route path="/discovery/inventory" element={<Inventory />} />
              <Route path="/discovery/dependencies" element={<Dependencies />} />
              <Route path="/discovery/data-cleansing" element={<DataCleansing />} />
              <Route path="/discovery/attribute-mapping" element={<AttributeMapping />} />
              <Route path="/discovery/tech-debt" element={<TechDebtAnalysis />} />
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
              <Route path="/finops/llm-costs" element={<LLMCosts />} />
              <Route path="/finops/wave-breakdown" element={<WaveBreakdown />} />
              <Route path="/finops/cost-trends" element={<CostTrends />} />
              <Route path="/finops/budget-alerts" element={<BudgetAlerts />} />
              <Route path="/observability" element={<Observability />} />
              <Route path="/observability/agent-monitoring" element={<AgentMonitoring />} />
              <Route path="/feedback-view" element={<FeedbackView />} />
              <Route path="/profile" element={<UserProfile />} />
              {/* Admin Routes - Protected */}
              <Route path="/admin" element={<AdminRoute><AdminLayout><AdminDashboard /></AdminLayout></AdminRoute>} />
              <Route path="/admin/dashboard" element={<AdminRoute><AdminLayout><AdminDashboard /></AdminLayout></AdminRoute>} />
              <Route path="/admin/clients" element={<AdminRoute><AdminLayout><ClientManagement /></AdminLayout></AdminRoute>} />
              <Route path="/admin/clients/new" element={<AdminRoute><AdminLayout><ClientManagement /></AdminLayout></AdminRoute>} />
              <Route path="/admin/clients/:clientId" element={<AdminRoute><AdminLayout><ClientDetails /></AdminLayout></AdminRoute>} />
              <Route path="/admin/engagements" element={<AdminRoute><AdminLayout><EngagementManagement /></AdminLayout></AdminRoute>} />
              <Route path="/admin/engagements/:engagementId" element={<AdminRoute><AdminLayout><EngagementDetails /></AdminLayout></AdminRoute>} />
              <Route path="/admin/users/approvals" element={<AdminRoute><AdminLayout><UserApprovals /></AdminLayout></AdminRoute>} />
              <Route path="/admin/users/create" element={<AdminRoute><AdminLayout><CreateUser /></AdminLayout></AdminRoute>} />
              <Route path="/admin/users" element={<AdminRoute><AdminLayout><UserApprovals /></AdminLayout></AdminRoute>} />
              <Route path="/admin/users/access" element={<AdminRoute><AdminLayout><UserApprovals /></AdminLayout></AdminRoute>} />
              <Route path="/admin/reports" element={<AdminRoute><AdminLayout><Reports /></AdminLayout></AdminRoute>} />
              <Route path="/admin/clients/create" element={<AdminRoute><AdminLayout><CreateClient /></AdminLayout></AdminRoute>} />
              <Route path="/admin/engagements/create" element={<AdminRoute><AdminLayout><CreateEngagement /></AdminLayout></AdminRoute>} />
              <Route path="/admin/platform" element={<AdminRoute><AdminLayout><PlatformAdmin /></AdminLayout></AdminRoute>} />
              <Route path="/admin/profile" element={<AdminRoute><AdminLayout><UserProfile /></AdminLayout></AdminRoute>} />
              {/* ADD ALL CUSTOM ROUTES ABOVE THE CATCH-ALL "*" ROUTE */}
              <Route path="*" element={<NotFound />} />
              </Routes>
  );
};

const App = () => (
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>
      <Toaster />
      <Sonner />
      <AuthProvider>
        <SessionProvider>
          <ClientProvider>
            <ChatFeedbackProvider>
              <AuthenticatedApp />
              <GlobalChatFeedback />
            </ChatFeedbackProvider>
          </ClientProvider>
        </SessionProvider>
      </AuthProvider>
    </TooltipProvider>
  </QueryClientProvider>
);

export default App;
