/**
 * Lazy Routes - Route-based code splitting for main pages
 */

import React from "react";
import { lazy, Suspense } from "react";
import { LoadingFallback, ErrorFallback } from "../LoadingFallback";
import { LoadingPriority } from "@/types/lazy";
import { ErrorBoundary } from "react-error-boundary";

// Define lazy loading strategies for different route categories
const createLazyRoute = <
  P extends Record<string, unknown> = Record<string, unknown>,
>(
  importFn: () => Promise<{ default: React.ComponentType<P> }>,
  componentName: string,
  priority: LoadingPriority = LoadingPriority.NORMAL,
) => {
  const LazyComponent = lazy(importFn);

  return React.forwardRef<HTMLElement, P>((props, ref) => (
    <ErrorBoundary
      FallbackComponent={({ error, resetErrorBoundary }) => (
        <ErrorFallback
          error={error}
          retry={resetErrorBoundary}
          componentName={componentName}
        />
      )}
      onError={(error) => {
        console.error(`Error loading ${componentName}:`, error);
      }}
    >
      <Suspense
        fallback={
          <LoadingFallback
            message={`Loading ${componentName}...`}
            priority={priority}
            showProgress={priority === LoadingPriority.CRITICAL}
          />
        }
      >
        <LazyComponent {...props} ref={ref} />
      </Suspense>
    </ErrorBoundary>
  ));
};

// CRITICAL PRIORITY - Core application routes
export const LazyIndex = createLazyRoute(
  () => import("@/pages/Index"),
  "Dashboard",
  LoadingPriority.CRITICAL,
);

export const LazyLogin = createLazyRoute(
  () => import("@/pages/Login"),
  "Login",
  LoadingPriority.CRITICAL,
);

export const LazyForgotPassword = createLazyRoute(
  () => import("@/pages/ForgotPassword"),
  "Forgot Password",
  LoadingPriority.CRITICAL,
);

export const LazyResetPassword = createLazyRoute(
  () => import("@/pages/ResetPassword"),
  "Reset Password",
  LoadingPriority.CRITICAL,
);

// HIGH PRIORITY - Main workflow pages
export const LazyDiscovery = createLazyRoute(
  () => import("@/pages/Discovery"),
  "Discovery",
  LoadingPriority.HIGH,
);

// NORMAL PRIORITY - Secondary workflow pages

export const LazyFinOps = createLazyRoute(
  () => import("@/pages/FinOps"),
  "FinOps",
  LoadingPriority.NORMAL,
);

export const LazyObservability = createLazyRoute(
  () => import("@/pages/Observability"),
  "Observability",
  LoadingPriority.NORMAL,
);


// Discovery Sub-routes (NORMAL priority)
export const LazyDiscoveryIndex = createLazyRoute(
  () => import("@/pages/discovery/Index"),
  "Discovery Overview",
);

export const LazyDataImport = createLazyRoute(
  () => import("@/pages/discovery/CMDBImport"),
  "Data Import",
);

export const LazyInventory = createLazyRoute(
  () => import("@/pages/discovery/Inventory"),
  "Inventory",
);

export const LazyDependencies = createLazyRoute(
  () => import("@/pages/discovery/Dependencies"),
  "Dependencies",
);

export const LazyDataCleansing = createLazyRoute(
  () => import("@/pages/discovery/DataCleansing"),
  "Data Cleansing",
);

export const LazyDataValidation = createLazyRoute(
  () => import("@/pages/discovery/DataValidation"),
  "Data Validation",
);

export const LazyAttributeMapping = createLazyRoute(
  () => import("@/pages/discovery/AttributeMapping"),
  "Attribute Mapping",
);

export const LazyTechDebtAnalysis = createLazyRoute(
  () => import("@/pages/discovery/TechDebtAnalysis"),
  "Tech Debt Analysis",
);

export const LazyDiscoveryDashboard = createLazyRoute(
  () => import("@/pages/discovery/DiscoveryDashboard"),
  "Discovery Dashboard",
);

export const LazyWatchlist = createLazyRoute(
  () => import("@/pages/discovery/Watchlist"),
  "Watchlist",
);

export const LazySearchHistory = createLazyRoute(
  () => import("@/pages/discovery/SearchHistory"),
  "Search History",
);

export const LazyFlowStatusMonitor = createLazyRoute(
  () => import("@/pages/discovery/FlowStatusMonitor"),
  "Flow Status Monitor",
);



// FinOps Sub-routes
export const LazyCloudComparison = createLazyRoute(
  () => import("@/pages/finops/CloudComparison"),
  "Cloud Comparison",
);

export const LazySavingsAnalysis = createLazyRoute(
  () => import("@/pages/finops/SavingsAnalysis"),
  "Savings Analysis",
);

export const LazyCostAnalysis = createLazyRoute(
  () => import("@/pages/finops/CostAnalysis"),
  "Cost Analysis",
);

export const LazyLLMCosts = createLazyRoute(
  () => import("@/pages/finops/LLMCosts"),
  "LLM Costs",
);

export const LazyWaveBreakdown = createLazyRoute(
  () => import("@/pages/finops/WaveBreakdown"),
  "Wave Breakdown",
);

export const LazyCostTrends = createLazyRoute(
  () => import("@/pages/finops/CostTrends"),
  "Cost Trends",
);

export const LazyBudgetAlerts = createLazyRoute(
  () => import("@/pages/finops/BudgetAlerts"),
  "Budget Alerts",
);

// LOW PRIORITY - Admin and utility pages
export const LazyAgentMonitoring = createLazyRoute(
  () => import("@/pages/AgentMonitoring"),
  "Agent Monitoring",
  LoadingPriority.LOW,
);

// Observability Sub-routes (Phase 4B Advanced Features)
export const LazyEnhancedObservabilityDashboard = createLazyRoute(
  () => import("@/pages/observability/EnhancedObservabilityDashboard"),
  "Enhanced Observability Dashboard",
  LoadingPriority.NORMAL,
);

export const LazyAgentDetailPage = createLazyRoute(
  () => import("@/pages/observability/IntegratedAgentDetailPage"),
  "Agent Detail Page",
  LoadingPriority.NORMAL,
);

export const LazyFeedbackView = createLazyRoute(
  () => import("@/pages/FeedbackView"),
  "Feedback View",
  LoadingPriority.LOW,
);

export const LazyNotFound = createLazyRoute(
  () => import("@/pages/NotFound"),
  "Page Not Found",
  LoadingPriority.LOW,
);

// Admin Routes (LOW priority)
export const LazyAdminDashboard = createLazyRoute(
  () => import("@/pages/admin/AdminDashboard"),
  "Admin Dashboard",
  LoadingPriority.LOW,
);

export const LazyClientManagement = createLazyRoute(
  () => import("@/pages/admin/ClientManagement"),
  "Client Management",
  LoadingPriority.LOW,
);

export const LazyClientDetails = createLazyRoute(
  () => import("@/pages/admin/ClientDetails"),
  "Client Details",
  LoadingPriority.LOW,
);

export const LazyEngagementManagement = createLazyRoute(
  () => import("@/pages/admin/EngagementManagement"),
  "Engagement Management",
  LoadingPriority.LOW,
);

export const LazyEngagementDetails = createLazyRoute(
  () => import("@/pages/admin/EngagementDetails"),
  "Engagement Details",
  LoadingPriority.LOW,
);

export const LazyUserApprovals = createLazyRoute(
  () => import("@/pages/admin/UserApprovals"),
  "User Approvals",
  LoadingPriority.LOW,
);

export const LazyCreateUser = createLazyRoute(
  () => import("@/pages/admin/CreateUser"),
  "Create User",
  LoadingPriority.LOW,
);

export const LazyCreateClient = createLazyRoute(
  () => import("@/pages/admin/CreateClient"),
  "Create Client",
  LoadingPriority.LOW,
);

export const LazyCreateEngagement = createLazyRoute(
  () => import("@/pages/admin/CreateEngagement"),
  "Create Engagement",
  LoadingPriority.LOW,
);

export const LazyUserProfile = createLazyRoute(
  () => import("@/pages/admin/UserProfile"),
  "User Profile",
  LoadingPriority.LOW,
);

export const LazyPlatformAdmin = createLazyRoute(
  () => import("@/pages/admin/PlatformAdmin"),
  "Platform Admin",
  LoadingPriority.LOW,
);

export const LazyDebugContext = createLazyRoute(
  () => import("@/pages/DebugContext"),
  "Debug Context",
  LoadingPriority.LOW,
);
