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

// HIGH PRIORITY - Main workflow pages
export const LazyDiscovery = createLazyRoute(
  () => import("@/pages/Discovery"),
  "Discovery",
  LoadingPriority.HIGH,
);

export const LazyAssess = createLazyRoute(
  () => import("@/pages/Assess"),
  "Assessment",
  LoadingPriority.HIGH,
);

export const LazyPlan = createLazyRoute(
  () => import("@/pages/Plan"),
  "Planning",
  LoadingPriority.HIGH,
);

export const LazyExecute = createLazyRoute(
  () => import("@/pages/Execute"),
  "Execution",
  LoadingPriority.HIGH,
);

// NORMAL PRIORITY - Secondary workflow pages
export const LazyModernize = createLazyRoute(
  () => import("@/pages/Modernize"),
  "Modernization",
  LoadingPriority.NORMAL,
);

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

export const LazyDecommission = createLazyRoute(
  () => import("@/pages/Decommission"),
  "Decommissioning",
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

export const LazyAttributeMapping = createLazyRoute(
  () => import("@/pages/discovery/AttributeMapping"),
  "Attribute Mapping",
);

export const LazyTechDebtAnalysis = createLazyRoute(
  () => import("@/pages/discovery/TechDebtAnalysis"),
  "Tech Debt Analysis",
);

export const LazyDiscoveryDashboard = createLazyRoute(
  () => import("@/pages/discovery/EnhancedDiscoveryDashboard"),
  "Discovery Dashboard",
);

// Collection Sub-routes (HIGH priority - frequently accessed workflows)
export const LazyCollectionIndex = createLazyRoute(
  () => import("@/pages/collection/Index"),
  "Collection Overview",
  LoadingPriority.HIGH,
);

export const LazyAdaptiveForms = createLazyRoute(
  () => import("@/pages/collection/adaptive-forms"),
  "Adaptive Forms",
  LoadingPriority.HIGH,
);

export const LazyBulkUpload = createLazyRoute(
  () => import("@/pages/collection/BulkUpload"),
  "Bulk Upload",
  LoadingPriority.HIGH,
);

export const LazyDataIntegration = createLazyRoute(
  () => import("@/pages/collection/DataIntegration"),
  "Data Integration",
  LoadingPriority.HIGH,
);

export const LazyCollectionProgress = createLazyRoute(
  () => import("@/pages/collection/Progress"),
  "Collection Progress",
  LoadingPriority.NORMAL,
);

export const LazyCollectionGapAnalysis = createLazyRoute(
  () => import("@/pages/collection/GapAnalysis"),
  "Gap Analysis",
  LoadingPriority.NORMAL,
);

export const LazyCollectionFlowManagement = createLazyRoute(
  () => import("@/pages/CollectionFlowManagementPage"),
  "Collection Flow Management",
  LoadingPriority.HIGH,
);

export const LazyApplicationSelection = createLazyRoute(
  () => import("@/pages/collection/ApplicationSelection"),
  "Application Selection",
  LoadingPriority.HIGH,
);

export const LazyCollectionSummary = createLazyRoute(
  () => import("@/pages/collection/Summary"),
  "Collection Summary",
  LoadingPriority.NORMAL,
);

// Assessment Sub-routes
export const LazyAssessIndex = createLazyRoute(
  () => import("@/pages/assess/Index"),
  "Assessment Overview",
);

export const LazyTreatment = createLazyRoute(
  () => import("@/pages/assess/Treatment"),
  "Treatment Planning",
);

export const LazyWavePlanning = createLazyRoute(
  () => import("@/pages/assess/WavePlanning"),
  "Wave Planning",
);

export const LazyRoadmap = createLazyRoute(
  () => import("@/pages/assess/Roadmap"),
  "Roadmap",
);

export const LazyEditor = createLazyRoute(
  () => import("@/pages/assess/Editor"),
  "Assessment Editor",
);

// Assessment Flow Routes
export const LazyInitializeAssessmentFlow = createLazyRoute(
  () => import("@/pages/assessment/InitializeFlow"),
  "Initialize Assessment",
);

export const LazyAssessmentFlowOverview = createLazyRoute(
  () => import("@/pages/assessment/AssessmentFlowOverview"),
  "Assessment Flow Overview",
);

export const LazyInitializeFlowWithInventory = createLazyRoute(
  () => import("@/pages/assessment/InitializeFlowWithInventory"),
  "Initialize Flow with Inventory",
);

export const LazyAssessmentArchitecture = createLazyRoute(
  () => import("@/pages/assessment/[flowId]/architecture"),
  "Assessment Architecture",
);

export const LazyAssessmentTechDebt = createLazyRoute(
  () => import("@/pages/assessment/[flowId]/tech-debt"),
  "Assessment Tech Debt",
);

export const LazyAssessmentSixRReview = createLazyRoute(
  () => import("@/pages/assessment/[flowId]/sixr-review"),
  "Assessment 6R Review",
);

export const LazyAssessmentAppOnPage = createLazyRoute(
  () => import("@/pages/assessment/[flowId]/app-on-page"),
  "Assessment App Details",
);

export const LazyAssessmentSummary = createLazyRoute(
  () => import("@/pages/assessment/[flowId]/summary"),
  "Assessment Summary",
);

// Assessment Phase Routes (ADR-027 - Migrated from Discovery)
export const LazyAssessmentDependencyAnalysis = createLazyRoute(
  () => import("@/pages/assessment/DependencyAnalysis"),
  "Assessment Dependency Analysis",
);

export const LazyAssessmentTechDebtAssessment = createLazyRoute(
  () => import("@/pages/assessment/TechDebtAssessment"),
  "Assessment Tech Debt Assessment",
);

// Plan Sub-routes
export const LazyPlanIndex = createLazyRoute(
  () => import("@/pages/plan/Index"),
  "Plan Overview",
);

export const LazySixRAnalysis = createLazyRoute(
  () => import("@/pages/planning/SixRAnalysis"),
  "6R Analysis",
);

export const LazyTimeline = createLazyRoute(
  () => import("@/pages/plan/Timeline"),
  "Timeline",
);

export const LazyResource = createLazyRoute(
  () => import("@/pages/plan/Resource"),
  "Resource Planning",
);

export const LazyTarget = createLazyRoute(
  () => import("@/pages/plan/Target"),
  "Target Architecture",
);

// Execute Sub-routes
export const LazyExecuteIndex = createLazyRoute(
  () => import("@/pages/execute/Index"),
  "Execute Overview",
);

export const LazyRehost = createLazyRoute(
  () => import("@/pages/execute/Rehost"),
  "Rehosting",
);

export const LazyReplatform = createLazyRoute(
  () => import("@/pages/execute/Replatform"),
  "Replatforming",
);

export const LazyCutovers = createLazyRoute(
  () => import("@/pages/execute/Cutovers"),
  "Cutovers",
);

export const LazyReports = createLazyRoute(
  () => import("@/pages/execute/Reports"),
  "Reports",
);

// Modernize Sub-routes
export const LazyModernizeIndex = createLazyRoute(
  () => import("@/pages/modernize/Index"),
  "Modernize Overview",
);

export const LazyRefactor = createLazyRoute(
  () => import("@/pages/modernize/Refactor"),
  "Refactoring",
);

export const LazyRearchitect = createLazyRoute(
  () => import("@/pages/modernize/Rearchitect"),
  "Rearchitecting",
);

export const LazyRewrite = createLazyRoute(
  () => import("@/pages/modernize/Rewrite"),
  "Rewriting",
);

export const LazyProgress = createLazyRoute(
  () => import("@/pages/modernize/Progress"),
  "Progress Tracking",
);

// Decommission Sub-routes
export const LazyDecommissionIndex = createLazyRoute(
  () => import("@/pages/decommission/Index"),
  "Decommission Overview",
);

export const LazyDecommissionPlanning = createLazyRoute(
  () => import("@/pages/decommission/Planning"),
  "Decommission Planning",
);

export const LazyDataRetention = createLazyRoute(
  () => import("@/pages/decommission/DataRetention"),
  "Data Retention",
);

export const LazyDecommissionExecution = createLazyRoute(
  () => import("@/pages/decommission/Execution"),
  "Decommission Execution",
);

export const LazyDecommissionValidation = createLazyRoute(
  () => import("@/pages/decommission/Validation"),
  "Decommission Validation",
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
