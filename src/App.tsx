import { useEffect, useState } from "react";
import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { Routes, Route } from "react-router-dom";
import { ChatFeedbackProvider } from "./contexts/ChatFeedbackContext";
import { AuthProvider, useAuth } from "./contexts/AuthContext";
import { ClientProvider } from "./contexts/ClientContext";
import { FieldOptionsProvider } from "./contexts/FieldOptionsContext";
import GlobalChatFeedback from "./components/GlobalChatFeedback";
import { AppInitializer } from "./services/appInitializer";

// Lazy Loading Infrastructure
import { LazyLoadingProvider, LoadingPriority } from "./components/lazy";
import { routePreloader } from "./utils/lazy/routePreloader";

// Lazy-loaded route components (organized by priority)
import {
  // CRITICAL PRIORITY - Core app routes
  LazyIndex,
  LazyLogin,
  
  // HIGH PRIORITY - Main workflow pages
  LazyDiscovery,
  LazyAssess,
  LazyPlan,
  LazyExecute,
  
  // NORMAL PRIORITY - Secondary workflow pages
  LazyModernize,
  LazyFinOps,
  LazyObservability,
  LazyDecommission,
  
  // Discovery sub-routes
  LazyDiscoveryIndex,
  LazyDataImport,
  LazyInventory,
  LazyDependencies,
  LazyDataCleansing,
  LazyAttributeMapping,
  LazyTechDebtAnalysis,
  LazyDiscoveryDashboard,
  
  // Assessment sub-routes
  LazyAssessIndex,
  LazyTreatment,
  LazyWavePlanning,
  LazyRoadmap,
  LazyEditor,
  
  // Assessment Flow routes
  LazyInitializeAssessmentFlow,
  LazyAssessmentFlowOverview,
  LazyInitializeFlowWithInventory,
  LazyAssessmentArchitecture,
  LazyAssessmentTechDebt,
  LazyAssessmentSixRReview,
  LazyAssessmentAppOnPage,
  LazyAssessmentSummary,
  
  // Plan sub-routes
  LazyPlanIndex,
  LazyTimeline,
  LazyResource,
  LazyTarget,
  
  // Execute sub-routes
  LazyExecuteIndex,
  LazyRehost,
  LazyReplatform,
  LazyCutovers,
  LazyReports,
  
  // Modernize sub-routes
  LazyModernizeIndex,
  LazyRefactor,
  LazyRearchitect,
  LazyRewrite,
  LazyProgress,
  
  // Decommission sub-routes
  LazyDecommissionIndex,
  LazyDecommissionPlanning,
  LazyDataRetention,
  LazyDecommissionExecution,
  LazyDecommissionValidation,
  
  // FinOps sub-routes
  LazyCloudComparison,
  LazySavingsAnalysis,
  LazyCostAnalysis,
  LazyLLMCosts,
  LazyWaveBreakdown,
  LazyCostTrends,
  LazyBudgetAlerts,
  
  // LOW PRIORITY - Admin and utility pages
  LazyAgentMonitoring,
  LazyFeedbackView,
  LazyNotFound,
  LazyAdminDashboard,
  LazyClientManagement,
  LazyClientDetails,
  LazyEngagementManagement,
  LazyEngagementDetails,
  LazyUserApprovals,
  LazyCreateUser,
  LazyCreateClient,
  LazyCreateEngagement,
  LazyUserProfile,
  LazyPlatformAdmin,
  LazyDebugContext
} from "./components/lazy";

// Non-lazy components that are always needed
import AdminLayout from "./components/admin/AdminLayout";
import AdminRoute from "./components/admin/AdminRoute";


// Component to handle authenticated routes
const AuthenticatedApp = () => {
  const { isLoading, isAuthenticated } = useAuth();
  const [appInitialized, setAppInitialized] = useState(false);

  // Initialize app only when authenticated
  useEffect(() => {
    if (isAuthenticated && !appInitialized) {
      AppInitializer.initialize()
        .then(() => setAppInitialized(true))
        .catch(() => setAppInitialized(true)); // Continue anyway - don't block the app
    }
  }, [isAuthenticated, appInitialized]);

  // Setup route preloading when authenticated
  useEffect(() => {
    if (isAuthenticated) {
      // Register critical routes for preloading
      routePreloader.registerRoute({
        path: '/',
        importFn: () => import('./pages/Index'),
        priority: LoadingPriority.CRITICAL
      });
      
      routePreloader.registerRoute({
        path: '/discovery',
        importFn: () => import('./pages/Discovery'),
        priority: LoadingPriority.HIGH
      });

      routePreloader.registerRoute({
        path: '/assess',
        importFn: () => import('./pages/Assess'),
        priority: LoadingPriority.HIGH
      });

      // Start intelligent preloading
      routePreloader.setupHoverPreloading();
      routePreloader.setupViewportPreloading();
      routePreloader.preloadFromCurrentLocation(window.location.pathname);
    }
  }, [isAuthenticated]);

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

  // If user is not authenticated, show only login route
  if (!isAuthenticated) {
    return (
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="*" element={<Login />} />
      </Routes>
    );
  }

  // User is authenticated, show all routes with lazy loading
  return (
    <Routes>
              {/* CRITICAL PRIORITY ROUTES */}
              <Route path="/" element={<LazyIndex />} />
              <Route path="/login" element={<LazyLogin />} />
              
              {/* HIGH PRIORITY - Main workflow routes */}
              <Route path="/discovery" element={<LazyDiscovery />} />
              <Route path="/assess" element={<LazyAssess />} />
              <Route path="/plan" element={<LazyPlan />} />
              <Route path="/execute" element={<LazyExecute />} />
              
              {/* NORMAL PRIORITY - Discovery sub-routes */}
              <Route path="/discovery/overview" element={<LazyDiscoveryDashboard />} />
              <Route path="/discovery/dashboard" element={<LazyDiscoveryDashboard />} />
              <Route path="/discovery/enhanced-dashboard" element={<LazyDiscoveryDashboard />} />
              <Route path="/discovery/cmdb-import" element={<LazyDataImport />} />
              <Route path="/discovery/inventory" element={<LazyInventory />} />
              <Route path="/discovery/inventory/:flowId" element={<LazyInventory />} />
              <Route path="/discovery/dependencies" element={<LazyDependencies />} />
              <Route path="/discovery/dependencies/:flowId" element={<LazyDependencies />} />
              <Route path="/discovery/data-cleansing" element={<LazyDataCleansing />} />
              <Route path="/discovery/data-cleansing/:flowId" element={<LazyDataCleansing />} />
              <Route path="/discovery/attribute-mapping" element={<LazyAttributeMapping />} />
              <Route path="/discovery/attribute-mapping/:flowId" element={<LazyAttributeMapping />} />
              <Route path="/discovery/tech-debt" element={<LazyTechDebtAnalysis />} />
              <Route path="/discovery/tech-debt/:flowId" element={<LazyTechDebtAnalysis />} />
              
              {/* Assessment sub-routes */}
              <Route path="/assess/overview" element={<LazyAssessmentFlowOverview />} />
              <Route path="/assess/treatment" element={<LazyTreatment />} />
              <Route path="/assess/waveplanning" element={<LazyWavePlanning />} />
              <Route path="/assess/roadmap" element={<LazyRoadmap />} />
              <Route path="/assess/editor" element={<LazyEditor />} />
              
              {/* Assessment Flow Routes */}
              <Route path="/assessment" element={<LazyAssessmentFlowOverview />} />
              <Route path="/assessment/overview" element={<LazyAssessmentFlowOverview />} />
              <Route path="/assessment/initialize" element={<LazyInitializeFlowWithInventory />} />
              <Route path="/assessment/:flowId/architecture" element={<LazyAssessmentArchitecture />} />
              <Route path="/assessment/:flowId/tech-debt" element={<LazyAssessmentTechDebt />} />
              <Route path="/assessment/:flowId/sixr-review" element={<LazyAssessmentSixRReview />} />
              <Route path="/assessment/:flowId/app-on-page" element={<LazyAssessmentAppOnPage />} />
              <Route path="/assessment/:flowId/summary" element={<LazyAssessmentSummary />} />
              
              {/* Plan sub-routes */}
              <Route path="/plan/overview" element={<LazyPlanIndex />} />
              <Route path="/plan/timeline" element={<LazyTimeline />} />
              <Route path="/plan/resource" element={<LazyResource />} />
              <Route path="/plan/target" element={<LazyTarget />} />
              
              {/* Execute sub-routes */}
              <Route path="/execute/overview" element={<LazyExecuteIndex />} />
              <Route path="/execute/rehost" element={<LazyRehost />} />
              <Route path="/execute/replatform" element={<LazyReplatform />} />
              <Route path="/execute/cutovers" element={<LazyCutovers />} />
              <Route path="/execute/reports" element={<LazyReports />} />
              
              {/* NORMAL PRIORITY - Secondary workflow routes */}
              <Route path="/modernize" element={<LazyModernize />} />
              <Route path="/modernize/overview" element={<LazyModernizeIndex />} />
              <Route path="/modernize/refactor" element={<LazyRefactor />} />
              <Route path="/modernize/rearchitect" element={<LazyRearchitect />} />
              <Route path="/modernize/rewrite" element={<LazyRewrite />} />
              <Route path="/modernize/progress" element={<LazyProgress />} />
              
              <Route path="/decommission" element={<LazyDecommission />} />
              <Route path="/decommission/overview" element={<LazyDecommissionIndex />} />
              <Route path="/decommission/planning" element={<LazyDecommissionPlanning />} />
              <Route path="/decommission/data-retention" element={<LazyDataRetention />} />
              <Route path="/decommission/execution" element={<LazyDecommissionExecution />} />
              <Route path="/decommission/validation" element={<LazyDecommissionValidation />} />
              
              <Route path="/finops" element={<LazyFinOps />} />
              <Route path="/finops/cloud-comparison" element={<LazyCloudComparison />} />
              <Route path="/finops/savings-analysis" element={<LazySavingsAnalysis />} />
              <Route path="/finops/cost-analysis" element={<LazyCostAnalysis />} />
              <Route path="/finops/llm-costs" element={<LazyLLMCosts />} />
              <Route path="/finops/wave-breakdown" element={<LazyWaveBreakdown />} />
              <Route path="/finops/cost-trends" element={<LazyCostTrends />} />
              <Route path="/finops/budget-alerts" element={<LazyBudgetAlerts />} />
              
              <Route path="/observability" element={<LazyObservability />} />
              <Route path="/observability/agent-monitoring" element={<LazyAgentMonitoring />} />
              <Route path="/feedback-view" element={<LazyFeedbackView />} />
              <Route path="/profile" element={<LazyUserProfile />} />
              <Route path="/debug-context" element={<LazyDebugContext />} />
              
              {/* LOW PRIORITY - Admin Routes (Protected) */}
              <Route path="/admin" element={<AdminRoute><AdminLayout><LazyAdminDashboard /></AdminLayout></AdminRoute>} />
              <Route path="/admin/dashboard" element={<AdminRoute><AdminLayout><LazyAdminDashboard /></AdminLayout></AdminRoute>} />
              <Route path="/admin/clients" element={<AdminRoute><AdminLayout><LazyClientManagement /></AdminLayout></AdminRoute>} />
              <Route path="/admin/clients/new" element={<AdminRoute><AdminLayout><LazyClientManagement /></AdminLayout></AdminRoute>} />
              <Route path="/admin/clients/:clientId" element={<AdminRoute><AdminLayout><LazyClientDetails /></AdminLayout></AdminRoute>} />
              <Route path="/admin/engagements" element={<AdminRoute><AdminLayout><LazyEngagementManagement /></AdminLayout></AdminRoute>} />
              <Route path="/admin/engagements/:engagementId" element={<AdminRoute><AdminLayout><LazyEngagementDetails /></AdminLayout></AdminRoute>} />
              <Route path="/admin/users/approvals" element={<AdminRoute><AdminLayout><LazyUserApprovals /></AdminLayout></AdminRoute>} />
              <Route path="/admin/users/create" element={<AdminRoute><AdminLayout><LazyCreateUser /></AdminLayout></AdminRoute>} />
              <Route path="/admin/users" element={<AdminRoute><AdminLayout><LazyUserApprovals /></AdminLayout></AdminRoute>} />
              <Route path="/admin/users/access" element={<AdminRoute><AdminLayout><LazyUserApprovals /></AdminLayout></AdminRoute>} />
              <Route path="/admin/reports" element={<AdminRoute><AdminLayout><LazyReports /></AdminLayout></AdminRoute>} />
              <Route path="/admin/clients/create" element={<AdminRoute><AdminLayout><LazyCreateClient /></AdminLayout></AdminRoute>} />
              <Route path="/admin/engagements/create" element={<AdminRoute><AdminLayout><LazyCreateEngagement /></AdminLayout></AdminRoute>} />
              <Route path="/admin/platform" element={<AdminRoute><AdminLayout><LazyPlatformAdmin /></AdminLayout></AdminRoute>} />
              <Route path="/admin/profile" element={<AdminRoute><AdminLayout><LazyUserProfile /></AdminLayout></AdminRoute>} />
              
              {/* Catch-all route */}
              <Route path="*" element={<LazyNotFound />} />
              </Routes>
  );
};

const App = () => (
  <TooltipProvider>
    <Toaster />
    <Sonner />
    <LazyLoadingProvider
      globalOptions={{
        priority: LoadingPriority.NORMAL,
        timeout: 30000,
        retryAttempts: 3,
        cacheStrategy: 'memory'
      }}
    >
      <AuthProvider>
        <ClientProvider>
          <FieldOptionsProvider>
            <ChatFeedbackProvider>
              <AuthenticatedApp />
              <GlobalChatFeedback />
            </ChatFeedbackProvider>
          </FieldOptionsProvider>
        </ClientProvider>
      </AuthProvider>
    </LazyLoadingProvider>
  </TooltipProvider>
);

export default App;
