import React, { useState } from "react";
import { useEffect } from "react";
import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { Route, Navigate } from "react-router-dom";
import { Routes } from "react-router-dom";
import { ChatFeedbackProvider } from "./contexts/ChatFeedbackContext";
import { AuthProvider, useAuth } from "./contexts/AuthContext";
import { ClientProvider } from "./contexts/ClientContext";
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
  LazyAgentDetailPage,
  LazyClientDetails,
  LazyEngagementDetails,
  LazyDebugContext,
} from "./components/lazy";
import {
  LazyIndex,
  LazyLogin,
  LazyForgotPassword,
  LazyResetPassword,
  LazyDiscovery,
  LazyFinOps,
  LazyObservability,
  LazyDataImport,
  LazyInventory,
  LazyDependencies,
  LazyDataCleansing,
  LazyDataValidation,
  LazyAttributeMapping,
  LazyTechDebtAnalysis,
  LazyDiscoveryDashboard,
  LazyWatchlist,
  LazySearchHistory,
  LazyFlowStatusMonitor,
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

  // If user is not authenticated, show login, forgot password, and reset password routes
  if (!isAuthenticated) {
    return (
      <Routes>
        <Route path="/login" element={<LazyLogin />} />
        <Route path="/forgot-password" element={<LazyForgotPassword />} />
        <Route path="/reset-password" element={<LazyResetPassword />} />
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


      {/* NORMAL PRIORITY - Discovery sub-routes */}
      <Route path="/discovery" element={<LazyDiscoveryDashboard />} />
      <Route path="/discovery/stock-analysis" element={<LazyDiscoveryDashboard />} />
      <Route path="/discovery/watchlist" element={<LazyWatchlist />} />
      <Route path="/discovery/search-history" element={<LazySearchHistory />} />
      <Route path="/discovery/overview" element={<LazyDiscoveryDashboard />} />
      <Route path="/discovery/dashboard" element={<LazyDiscoveryDashboard />} />
      <Route
        path="/discovery/enhanced-dashboard"
        element={<LazyDiscoveryDashboard />}
      />
      <Route
        path="/discovery/monitor/:flowId"
        element={<LazyFlowStatusMonitor />}
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
      <Route path="/discovery/data-validation" element={<LazyDataValidation />} />
      <Route
        path="/discovery/data-validation/:flowId"
        element={<LazyDataValidation />}
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
            <DialogProvider>
              <ChatFeedbackProvider>
                <AuthenticatedApp />
                <GlobalChatFeedback />
              </ChatFeedbackProvider>
            </DialogProvider>
          </ClientProvider>
        </AuthProvider>
      </LazyLoadingProvider>
    </TooltipProvider>
  </ErrorBoundary>
);

export default App;
