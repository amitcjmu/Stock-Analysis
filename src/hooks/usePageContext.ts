/**
 * usePageContext Hook - Provides page context for the AI Chat Assistant
 *
 * This hook fetches the current page's context from the Page Context Registry
 * and optionally fetches flow state from the backend.
 *
 * Issue: #1219 - [Frontend] Page Context Registry
 * Milestone: Contextual AI Chat Assistant
 */

import { useLocation, useParams } from 'react-router-dom';
import { useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  getPageContext,
  getWorkflowNavigation,
  getSuggestedHelpTopics,
} from '../config/pageContextRegistry';
import type {
  PageContext,
  FlowType,
} from '../config/pageContextRegistry';
import { apiCall } from '../config/api';

export interface FlowStateContext {
  flow_id: string | null;
  flow_type: FlowType | null;
  current_phase: string | null;
  completion_percentage: number | null;
  status: string | null;
  pending_actions: string[];
}

export interface UsePageContextResult {
  pageContext: PageContext | null;
  flowState: FlowStateContext | null;
  breadcrumb: string;
  helpTopics: string[];
  workflowNav: {
    current: PageContext | null;
    next: PageContext | null;
    previous: PageContext | null;
  };
  // Serialized context for API calls
  serializedContext: {
    page_context: PageContext | null;
    flow_state: FlowStateContext | null;
    breadcrumb: string;
    timestamp: string;
  };
}

/**
 * Extract flow ID from URL params or path
 */
function extractFlowId(params: Record<string, string | undefined>, pathname: string): string | null {
  // Check common param names
  const flowId = params.flowId || params.flow_id || params.applicationId;
  if (flowId) return flowId;

  // Try to extract UUID from path
  const uuidRegex = /[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}/i;
  const match = pathname.match(uuidRegex);
  return match ? match[0] : null;
}

/**
 * Detect flow type from the URL path
 */
function detectFlowType(pathname: string): FlowType | null {
  if (pathname.startsWith('/discovery')) return 'discovery';
  if (pathname.startsWith('/collection')) return 'collection';
  if (pathname.startsWith('/assessment')) return 'assessment';
  if (pathname.startsWith('/plan')) return 'planning';
  if (pathname.startsWith('/execute')) return 'execute';
  if (pathname.startsWith('/modernize')) return 'modernize';
  if (pathname.startsWith('/decommission') || pathname.startsWith('/decom')) return 'decommission';
  if (pathname.startsWith('/finops')) return 'finops';
  if (pathname.startsWith('/observability')) return 'observability';
  if (pathname.startsWith('/admin')) return 'admin';
  return 'general';
}

/**
 * Generate breadcrumb from path
 */
function generateBreadcrumb(pathname: string, pageContext: PageContext | null): string {
  if (!pathname || pathname === '/') return 'Home';

  const segments = pathname.split('/').filter(Boolean);
  const breadcrumbParts: string[] = [];

  // Map segments to readable names
  const segmentNames: Record<string, string> = {
    discovery: 'Discovery',
    collection: 'Collection',
    assessment: 'Assessment',
    plan: 'Planning',
    execute: 'Execute',
    modernize: 'Modernize',
    decommission: 'Decommission',
    decom: 'Decommission',
    finops: 'FinOps',
    observability: 'Observability',
    admin: 'Admin',
    'data-import': 'Data Import',
    'cmdb-import': 'Data Import',
    'attribute-mapping': 'Attribute Mapping',
    'data-cleansing': 'Data Cleansing',
    'data-validation': 'Data Validation',
    inventory: 'Asset Inventory',
    dependencies: 'Dependencies',
    'adaptive-forms': 'Adaptive Forms',
    'bulk-upload': 'Bulk Upload',
    progress: 'Progress',
    'gap-analysis': 'Gap Analysis',
    overview: 'Overview',
    waveplanning: 'Wave Planning',
    timeline: 'Timeline',
    resource: 'Resources',
    target: 'Target',
    'llm-costs': 'LLM Costs',
    clients: 'Clients',
    engagements: 'Engagements',
    users: 'Users',
  };

  for (const segment of segments) {
    // Skip UUID segments
    if (/^[0-9a-f]{8}-[0-9a-f]{4}-/i.test(segment)) continue;

    const name = segmentNames[segment] || segment.charAt(0).toUpperCase() + segment.slice(1).replace(/-/g, ' ');
    breadcrumbParts.push(name);
  }

  // If we have a page context, use its name for the last part
  if (pageContext && breadcrumbParts.length > 0) {
    breadcrumbParts[breadcrumbParts.length - 1] = pageContext.page_name;
  }

  return breadcrumbParts.join(' > ');
}

/**
 * API response type for flow context
 */
interface FlowContextApiResponse {
  flow_id: string | null;
  flow_type: string | null;
  current_phase: string | null;
  completion_percentage: number | null;
  status: string | null;
  pending_actions: string[];
  metadata: Record<string, unknown>;
}

/**
 * Fetch flow context from the backend API
 */
async function fetchFlowContext(
  flowType: string,
  flowId: string
): Promise<FlowContextApiResponse | null> {
  try {
    const response = await apiCall<FlowContextApiResponse>(
      `/chat/flow-context/${flowType}/${flowId}`,
      { method: 'GET' }
    );

    if (response && typeof response === 'object' && 'flow_id' in response) {
      return response as FlowContextApiResponse;
    }
    return null;
  } catch (error) {
    console.warn('Failed to fetch flow context:', error);
    return null;
  }
}

/**
 * Hook to get current page context for the AI Chat Assistant
 */
export function usePageContext(): UsePageContextResult {
  const location = useLocation();
  const params = useParams();
  const pathname = location.pathname;

  // Get page context from registry
  const pageContext = useMemo(() => {
    return getPageContext(pathname);
  }, [pathname]);

  // Extract basic flow info from URL
  const basicFlowInfo = useMemo(() => {
    const flowId = extractFlowId(params, pathname);
    const flowType = detectFlowType(pathname);
    return { flowId, flowType };
  }, [params, pathname]);

  // Fetch dynamic flow state from backend when we have a flow ID
  const { data: dynamicFlowState, isLoading: isLoadingFlowState } = useQuery<
    FlowContextApiResponse | null
  >({
    queryKey: [
      'chat-flow-context',
      basicFlowInfo.flowType,
      basicFlowInfo.flowId,
    ],
    queryFn: () =>
      basicFlowInfo.flowId && basicFlowInfo.flowType
        ? fetchFlowContext(basicFlowInfo.flowType, basicFlowInfo.flowId)
        : Promise.resolve(null),
    enabled: !!basicFlowInfo.flowId && !!basicFlowInfo.flowType,
    staleTime: 30000, // 30 seconds - flow state doesn't change frequently
    refetchOnWindowFocus: false,
    retry: 1, // Only retry once on failure
  });

  // Combine static and dynamic flow state
  const flowState = useMemo((): FlowStateContext | null => {
    const { flowId, flowType } = basicFlowInfo;

    if (!flowId && !flowType) return null;

    // If we have dynamic flow state from API, use it
    if (dynamicFlowState && dynamicFlowState.status !== 'not_found') {
      return {
        flow_id: dynamicFlowState.flow_id || flowId,
        flow_type: (dynamicFlowState.flow_type as FlowType) || flowType,
        current_phase: dynamicFlowState.current_phase,
        completion_percentage: dynamicFlowState.completion_percentage,
        status: dynamicFlowState.status,
        pending_actions: dynamicFlowState.pending_actions || [],
      };
    }

    // Fall back to basic flow state from URL
    return {
      flow_id: flowId,
      flow_type: flowType,
      current_phase: pageContext?.workflow?.phase || null,
      completion_percentage: null,
      status: null,
      pending_actions: [],
    };
  }, [basicFlowInfo, dynamicFlowState, pageContext]);

  // Generate breadcrumb
  const breadcrumb = useMemo(() => {
    return generateBreadcrumb(pathname, pageContext);
  }, [pathname, pageContext]);

  // Get help topics
  const helpTopics = useMemo(() => {
    return getSuggestedHelpTopics(pathname);
  }, [pathname]);

  // Get workflow navigation
  const workflowNav = useMemo(() => {
    return getWorkflowNavigation(pathname);
  }, [pathname]);

  // Serialized context for API calls
  const serializedContext = useMemo(() => {
    return {
      page_context: pageContext,
      flow_state: flowState,
      breadcrumb,
      timestamp: new Date().toISOString(),
    };
  }, [pageContext, flowState, breadcrumb]);

  return {
    pageContext,
    flowState,
    breadcrumb,
    helpTopics,
    workflowNav,
    serializedContext,
  };
}

/**
 * Hook to get just the serialized context string for the chat API
 */
export function useSerializedPageContext(): string {
  const { serializedContext } = usePageContext();

  return useMemo(() => {
    return JSON.stringify(serializedContext);
  }, [serializedContext]);
}

export default usePageContext;
