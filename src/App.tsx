import { useState } from "react";
import { useEffect } from "react";
import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { Route } from "react-router-dom";
import { Routes } from "react-router-dom";
import { ChatFeedbackProvider } from "./contexts/ChatFeedbackContext";
import { AuthProvider, useAuth } from "./contexts/AuthContext";
import { ClientProvider } from "./contexts/ClientContext";
import { FieldOptionsProvider } from "./contexts/FieldOptionsContext";
import { DialogProvider } from "./contexts/DialogContext";
import GlobalChatFeedback from "./components/GlobalChatFeedback";
import { AppInitializer } from "./services/appInitializer";
import { useGlobalErrorHandler } from "./hooks/useGlobalErrorHandler";
import { ErrorBoundary } from "./components/ErrorBoundary";

// Lazy Loading Infrastructure
import { LazyLoadingProvider, LoadingPriority } from "./components/lazy";
import { routePreloader } from "./utils/lazy/routePreloader";

// Lazy-loaded route components (organized by priority)
import {
  LazyAssessmentAppOnPage,
  LazyAssessmentSummary,
  LazyAgentDetailPage,
  LazyClientDetails,
  LazyEngagementDetails,
  LazyDebugContext,
} from "./components/lazy";
import {
  LazyIndex,
  LazyLogin,
  LazyDiscovery,
  LazyAssess,
  LazyPlan,
  LazyExecute,
  LazyModernize,
  LazyFinOps,
  LazyObservability,
  LazyDecommission,
  LazyDataImport,
  LazyInventory,
  LazyDependencies,
  LazyDataCleansing,
  LazyAttributeMapping,
  LazyTechDebtAnalysis,
  LazyDiscoveryDashboard,
  LazyCollectionIndex,
  LazyAdaptiveForms,
  LazyBulkUpload,
  LazyDataIntegration,
  LazyCollectionProgress,
  LazyCollectionGapAnalysis,
  LazyCollectionFlowManagement,
  LazyApplicationSelection,
  LazyTreatment,
  LazyWavePlanning,
  LazyRoadmap,
  LazyEditor,
  LazyAssessmentFlowOverview,
  LazyInitializeFlowWithInventory,
  LazyAssessmentArchitecture,
  LazyAssessmentTechDebt,
  LazyAssessmentSixRReview,
  LazyPlanIndex,
  LazySixRAnalysis,
  LazyTimeline,
  LazyResource,
  LazyTarget,
  LazyExecuteIndex,
  LazyRehost,
  LazyReplatform,
  LazyCutovers,
  LazyReports,
  LazyModernizeIndex,
  LazyRefactor,
  LazyRearchitect,
  LazyRewrite,
  LazyProgress,
  LazyDecommissionIndex,
  LazyDecommissionPlanning,
  LazyDataRetention,
  LazyDecommissionExecution,
  LazyDecommissionValidation,
  LazyCloudComparison,
  LazySavingsAnalysis,
  LazyCostAnalysis,
  LazyLLMCosts,
  LazyWaveBreakdown,
  LazyCostTrends,
  LazyBudgetAlerts,
  LazyEnhancedObservabilityDashboard,
  LazyFeedbackView,
  LazyNotFound,
  LazyAdminDashboard,
  LazyClientManagement,
  LazyEngagementManagement,
  LazyUserApprovals,
  LazyCreateUser,
  LazyCreateClient,
  LazyCreateEngagement,
  LazyUserProfile,
  LazyPlatformAdmin,
} from "./components/lazy";

// Non-lazy components that are always needed
import AdminLayout from "./components/admin/AdminLayout";
import AdminRoute from "./components/admin/AdminRoute";

// Component to handle authenticated routes
const AuthenticatedApp = (): JSX.Element => {
  const { isLoading, isAuthenticated } = useAuth();
  const [appInitialized, setAppInitialized] = useState(false);

  // Enable global error handling for 401 errors
  useGlobalErrorHandler();

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
        path: "/",
        importFn: () => import("./pages/Index"),
        priority: LoadingPriority.CRITICAL,
      });

      routePreloader.registerRoute({
        path: "/discovery",
        importFn: () => import("./pages/Discovery"),
        priority: LoadingPriority.HIGH,
      });

      routePreloader.registerRoute({
        path: "/assess",
        importFn: () => import("./pages/Assess"),
        priority: LoadingPriority.HIGH,
      });

      // Register collection routes for preloading
      routePreloader.registerRoute({
        path: "/collection",
        importFn: () => import("./pages/collection/Index"),
        priority: LoadingPriority.HIGH,
      });

      routePreloader.registerRoute({
        path: "/collection/adaptive-forms",
        importFn: () => import("./pages/collection/AdaptiveForms"),
        priority: LoadingPriority.HIGH,
      });

      routePreloader.registerRoute({
        path: "/collection/gap-analysis",
        importFn: () => import("./pages/collection/GapAnalysis"),
        priority: LoadingPriority.NORMAL,
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
        <Route path="/login" element={<LazyLogin />} />
        <Route path="*" element={<LazyLogin />} />
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
      <Route
        path="/discovery/enhanced-dashboard"
        element={<LazyDiscoveryDashboard />}
      />
      <Route
        path="/discovery/monitor/:flowId"
        element={<LazyDiscoveryDashboard />}
      />
      <Route path="/discovery/cmdb-import" element={<LazyDataImport />} />
      <Route path="/discovery/data-import" element={<LazyDataImport />} />
      <Route path="/discovery/inventory" element={<LazyInventory />} />
      <Route path="/discovery/inventory/:flowId" element={<LazyInventory />} />
      <Route path="/discovery/dependencies" element={<LazyDependencies />} />
      <Route
        path="/discovery/dependencies/:flowId"
        element={<LazyDependencies />}
      />
      <Route path="/discovery/data-cleansing" element={<LazyDataCleansing />} />
      <Route
        path="/discovery/data-cleansing/:flowId"
        element={<LazyDataCleansing />}
      />
      <Route
        path="/discovery/attribute-mapping"
        element={<LazyAttributeMapping />}
      />
      <Route
        path="/discovery/attribute-mapping/:flowId"
        element={<LazyAttributeMapping />}
      />
      {/* Redirect for backward compatibility - field-mapping to attribute-mapping */}
      <Route
        path="/discovery/field-mapping"
        element={<LazyAttributeMapping />}
      />
      <Route
        path="/discovery/field-mapping/:flowId"
        element={<LazyAttributeMapping />}
      />

      {/* Collection workflow routes */}
      <Route path="/collection" element={<LazyCollectionIndex />} />
      <Route path="/collection/overview" element={<LazyCollectionIndex />} />
      <Route
        path="/collection/adaptive-forms"
        element={<LazyAdaptiveForms />}
      />
      <Route
        path="/collection/adaptive-forms/:applicationId"
        element={<LazyAdaptiveForms />}
      />
      <Route path="/collection/bulk-upload" element={<LazyBulkUpload />} />
      <Route
        path="/collection/data-integration"
        element={<LazyDataIntegration />}
      />
      <Route
        path="/collection/select-applications"
        element={<LazyApplicationSelection />}
      />
      <Route path="/collection/progress" element={<LazyCollectionProgress />} />
      <Route
        path="/collection/progress/:flowId"
        element={<LazyCollectionProgress />}
      />
      {/* Individual flow detail route - redirects to progress page for now */}
      <Route
        path="/collection/flow/:flowId"
        element={<LazyCollectionProgress />}
      />
      <Route
        path="/collection/gap-analysis/:flowId"
        element={<LazyCollectionGapAnalysis />}
      />
      <Route
        path="/collection/flow-management"
        element={<LazyCollectionFlowManagement />}
      />

      {/* Assessment sub-routes */}
      <Route path="/assess/overview" element={<LazyAssessmentFlowOverview />} />
      <Route path="/assess/treatment" element={<LazyTreatment />} />
      <Route path="/assess/tech-debt" element={<LazyTechDebtAnalysis />} />
      <Route path="/assess/editor" element={<LazyEditor />} />

      {/* Assessment Flow Routes */}
      <Route path="/assessment" element={<LazyAssessmentFlowOverview />} />
      <Route
        path="/assessment/overview"
        element={<LazyAssessmentFlowOverview />}
      />
      <Route
        path="/assessment/initialize"
        element={<LazyInitializeFlowWithInventory />}
      />
      <Route
        path="/assessment/:flowId/architecture"
        element={<LazyAssessmentArchitecture />}
      />
      <Route
        path="/assessment/:flowId/tech-debt"
        element={<LazyAssessmentTechDebt />}
      />
      <Route
        path="/assessment/:flowId/sixr-review"
        element={<LazyAssessmentSixRReview />}
      />
      <Route
        path="/assessment/:flowId/app-on-page"
        element={<LazyAssessmentAppOnPage />}
      />
      <Route
        path="/assessment/:flowId/summary"
        element={<LazyAssessmentSummary />}
      />

      {/* Plan sub-routes */}
      <Route path="/plan/overview" element={<LazyPlanIndex />} />
      <Route path="/plan/6r-analysis" element={<LazySixRAnalysis />} />
      <Route path="/planning/6r-analysis" element={<LazySixRAnalysis />} />
      <Route path="/plan/waveplanning" element={<LazyWavePlanning />} />
      <Route path="/plan/roadmap" element={<LazyRoadmap />} />
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
      <Route
        path="/decommission/overview"
        element={<LazyDecommissionIndex />}
      />
      <Route
        path="/decommission/planning"
        element={<LazyDecommissionPlanning />}
      />
      <Route
        path="/decommission/data-retention"
        element={<LazyDataRetention />}
      />
      <Route
        path="/decommission/execution"
        element={<LazyDecommissionExecution />}
      />
      <Route
        path="/decommission/validation"
        element={<LazyDecommissionValidation />}
      />

      <Route path="/finops" element={<LazyFinOps />} />
      <Route
        path="/finops/cloud-comparison"
        element={<LazyCloudComparison />}
      />
      <Route
        path="/finops/savings-analysis"
        element={<LazySavingsAnalysis />}
      />
      <Route path="/finops/cost-analysis" element={<LazyCostAnalysis />} />
      <Route path="/finops/llm-costs" element={<LazyLLMCosts />} />
      <Route path="/finops/wave-breakdown" element={<LazyWaveBreakdown />} />
      <Route path="/finops/cost-trends" element={<LazyCostTrends />} />
      <Route path="/finops/budget-alerts" element={<LazyBudgetAlerts />} />

      <Route path="/observability" element={<LazyObservability />} />
      <Route
        path="/observability/enhanced"
        element={<LazyEnhancedObservabilityDashboard />}
      />
      <Route
        path="/observability/agent/:agentName"
        element={<LazyAgentDetailPage />}
      />
      <Route
        path="/observability/agent-monitoring"
        element={<LazyEnhancedObservabilityDashboard />}
      />
      <Route path="/feedback-view" element={<LazyFeedbackView />} />
      <Route path="/profile" element={<LazyUserProfile />} />
      <Route path="/debug-context" element={<LazyDebugContext />} />

      {/* LOW PRIORITY - Admin Routes (Protected) */}
      <Route
        path="/admin"
        element={
          <AdminRoute>
            <AdminLayout>
              <LazyAdminDashboard />
            </AdminLayout>
          </AdminRoute>
        }
      />
      <Route
        path="/admin/dashboard"
        element={
          <AdminRoute>
            <AdminLayout>
              <LazyAdminDashboard />
            </AdminLayout>
          </AdminRoute>
        }
      />
      <Route
        path="/admin/clients"
        element={
          <AdminRoute>
            <AdminLayout>
              <LazyClientManagement />
            </AdminLayout>
          </AdminRoute>
        }
      />
      <Route
        path="/admin/clients/new"
        element={
          <AdminRoute>
            <AdminLayout>
              <LazyClientManagement />
            </AdminLayout>
          </AdminRoute>
        }
      />
      <Route
        path="/admin/clients/:clientId"
        element={
          <AdminRoute>
            <AdminLayout>
              <LazyClientDetails />
            </AdminLayout>
          </AdminRoute>
        }
      />
      <Route
        path="/admin/engagements"
        element={
          <AdminRoute>
            <AdminLayout>
              <LazyEngagementManagement />
            </AdminLayout>
          </AdminRoute>
        }
      />
      <Route
        path="/admin/engagements/:engagementId"
        element={
          <AdminRoute>
            <AdminLayout>
              <LazyEngagementDetails />
            </AdminLayout>
          </AdminRoute>
        }
      />
      <Route
        path="/admin/users/approvals"
        element={
          <AdminRoute>
            <AdminLayout>
              <LazyUserApprovals />
            </AdminLayout>
          </AdminRoute>
        }
      />
      <Route
        path="/admin/users/create"
        element={
          <AdminRoute>
            <AdminLayout>
              <LazyCreateUser />
            </AdminLayout>
          </AdminRoute>
        }
      />
      <Route
        path="/admin/users"
        element={
          <AdminRoute>
            <AdminLayout>
              <LazyUserApprovals />
            </AdminLayout>
          </AdminRoute>
        }
      />
      <Route
        path="/admin/users/access"
        element={
          <AdminRoute>
            <AdminLayout>
              <LazyUserApprovals />
            </AdminLayout>
          </AdminRoute>
        }
      />
      <Route
        path="/admin/reports"
        element={
          <AdminRoute>
            <AdminLayout>
              <LazyReports />
            </AdminLayout>
          </AdminRoute>
        }
      />
      <Route
        path="/admin/clients/create"
        element={
          <AdminRoute>
            <AdminLayout>
              <LazyCreateClient />
            </AdminLayout>
          </AdminRoute>
        }
      />
      <Route
        path="/admin/engagements/create"
        element={
          <AdminRoute>
            <AdminLayout>
              <LazyCreateEngagement />
            </AdminLayout>
          </AdminRoute>
        }
      />
      <Route
        path="/admin/platform"
        element={
          <AdminRoute>
            <AdminLayout>
              <LazyPlatformAdmin />
            </AdminLayout>
          </AdminRoute>
        }
      />
      <Route
        path="/admin/profile"
        element={
          <AdminRoute>
            <AdminLayout>
              <LazyUserProfile />
            </AdminLayout>
          </AdminRoute>
        }
      />

      {/* Catch-all route */}
      <Route path="*" element={<LazyNotFound />} />
    </Routes>
  );
};

const App = (): JSX.Element => (
  <ErrorBoundary>
    <TooltipProvider>
      <Toaster />
      <Sonner />
      <LazyLoadingProvider
        globalOptions={{
          priority: LoadingPriority.NORMAL,
          timeout: 30000,
          retryAttempts: 3,
          cacheStrategy: "memory",
        }}
      >
        <AuthProvider>
          <ClientProvider>
            <FieldOptionsProvider>
              <DialogProvider>
                <ChatFeedbackProvider>
                  <AuthenticatedApp />
                  <GlobalChatFeedback />
                </ChatFeedbackProvider>
              </DialogProvider>
            </FieldOptionsProvider>
          </ClientProvider>
        </AuthProvider>
      </LazyLoadingProvider>
    </TooltipProvider>
  </ErrorBoundary>
);

export default App;
