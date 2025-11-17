import React from 'react'
import { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom';

// Import layout components
import Sidebar from '@/components/Sidebar';
import ContextBreadcrumbs from '@/components/context/ContextBreadcrumbs';

// Import collection flow API
import { collectionFlowApi } from '@/services/api/collection-flow';
import { useToast } from '@/components/ui/use-toast';

// Import auth context for flow management
import { useAuth } from '@/contexts/AuthContext';

// Import RBAC utilities
import { canCreateCollectionFlow, getRoleName } from '@/utils/rbac';

// Import flow routing configuration
import { FLOW_PHASE_ROUTES } from '@/config/flowRoutes';

import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { FormInput, Upload, Settings, BarChart3, Clock, CheckCircle, AlertCircle, Loader2, Shield, Info, ChevronDown, ChevronRight } from 'lucide-react'

/**
 * Guided workflow configuration
 * Externalizes business rules (e.g., application count thresholds) from UI components
 * Update these values to change workflow recommendations without modifying component code
 */
const GUIDED_WORKFLOW_CONFIG = {
  question: "How many applications do you need to collect data for?",
  options: [
    {
      id: 'adaptive' as const,
      value: 'adaptive',
      threshold: '1-50 applications',
      title: 'Adaptive Forms',
      description: 'Interactive guided forms with AI assistance for smaller portfolios',
      icon: FormInput,
      estimatedTime: '15-30 min per application'
    },
    {
      id: 'bulk' as const,
      value: 'bulk',
      threshold: '50+ applications',
      title: 'Bulk Upload',
      description: 'CSV/Excel import for large application portfolios',
      icon: Upload,
      estimatedTime: '5-10 min for 100+ applications'
    }
  ]
};

/**
 * Collection workflow index page
 * Provides overview and entry points for all collection workflows
 */
const CollectionIndex: React.FC = () => {
  const navigate = useNavigate();
  const { toast } = useToast();
  const { setCurrentFlow, user } = useAuth();
  const [isCreatingFlow, setIsCreatingFlow] = useState<string | null>(null);
  const navigationTimeoutRef = useRef<number | null>(null);
  const errorNavigationTimeoutRef = useRef<number | null>(null);
  const [collectionMetrics, setCollectionMetrics] = useState({
    activeForms: 0,
    bulkUploads: 0,
    pendingConflicts: 0,
    completionRate: 0,
    hasActiveFlow: false,
    activeFlowId: null as string | null,
    activeFlowStatus: null as string | null
  });

  // New state for guided workflow
  const [selectedMethod, setSelectedMethod] = useState<'adaptive' | 'bulk' | null>(null);
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [showNewFlowForm, setShowNewFlowForm] = useState(false);

  // Cleanup timeouts on unmount
  useEffect(() => {
    return () => {
      if (navigationTimeoutRef.current) {
        clearTimeout(navigationTimeoutRef.current);
      }
      if (errorNavigationTimeoutRef.current) {
        clearTimeout(errorNavigationTimeoutRef.current);
      }
    };
  }, []);

  // Fetch collection status on mount
  useEffect(() => {
    const fetchCollectionStatus = async () => {
      try {
        // Get auth data from correct localStorage keys
        const authToken = localStorage.getItem('auth_token');
        const clientId = localStorage.getItem('auth_client_id');
        const engagementStr = localStorage.getItem('auth_engagement');
        const userStr = localStorage.getItem('auth_user');
        let engagementId = '';
        let userId = '';

        if (engagementStr) {
          try {
            const engagement = JSON.parse(engagementStr);
            engagementId = engagement.id;
          } catch (e) {
            console.error('Failed to parse engagement data:', e);
          }
        }

        if (userStr) {
          try {
            const user = JSON.parse(userStr);
            userId = user.id;
          } catch (e) {
            console.error('Failed to parse user data:', e);
          }
        }

        const response = await fetch('/api/v1/collection/status', {
          headers: {
            'Authorization': `Bearer ${authToken}`,
            'Content-Type': 'application/json',
            'X-Client-Account-ID': clientId || '',
            'X-Engagement-ID': engagementId || '',
            'X-User-ID': userId || ''
          }
        });

        if (response.ok) {
          const data = await response.json();

          // Check if there's an active flow
          if (data.status !== 'no_active_flow') {
            setCollectionMetrics(prev => ({
              ...prev,
              hasActiveFlow: true,
              activeFlowId: data.flow_id,
              activeFlowStatus: data.status,
              activeForms: data.status === 'initialized' || data.status === 'platform_detection' ? 1 : 0,
              completionRate: data.progress || 0
            }));
          }
        }
      } catch (error) {
        console.error('Failed to fetch collection status:', error);
      }
    };

    fetchCollectionStatus();
    // Refresh status every 10 seconds
    const interval = setInterval(fetchCollectionStatus, 10000);
    return () => clearInterval(interval);
  }, []);

  const advancedWorkflowOptions = [
    {
      id: 'gap-analysis',
      title: 'Gap Analysis Only',
      description: 'Identify missing data in existing applications',
      icon: <AlertCircle className="h-5 w-5" />,
      path: '/collection/gap-analysis',
      estimatedTime: '10-15 min'
    },
    {
      id: 'data-integration',
      title: 'Data Integration & Validation',
      description: 'Import and validate application data',
      icon: <Settings className="h-5 w-5" />,
      path: '/collection/data-integration',
      estimatedTime: '10-20 min'
    },
    {
      id: 'progress-monitoring',
      title: 'Progress Monitor',
      description: 'Track ongoing collection workflows',
      icon: <BarChart3 className="h-5 w-5" />,
      path: '/collection/progress',
      estimatedTime: 'Real-time monitoring'
    }
  ];

  /**
   * Handle resuming an active collection flow
   * FIX BUG#801: Navigate directly to current phase instead of progress monitor
   */
  const handleResumeFlow = async (flowId: string) => {
    console.log(`🔄 Resuming collection flow: ${flowId}`);

    try {
      // Get flow details to determine current phase
      const flowDetails = await collectionFlowApi.getFlow(flowId);
      const currentPhase = flowDetails.current_phase || 'asset_selection';

      console.log(`📍 Current phase: ${currentPhase}`);

      // Navigate directly to current phase
      const phaseRoute = FLOW_PHASE_ROUTES.collection[currentPhase];

      if (phaseRoute) {
        const targetRoute = phaseRoute(flowId);
        console.log(`🧭 Navigating to ${currentPhase} phase: ${targetRoute}`);
        navigate(targetRoute);
      } else {
        // Fallback to progress monitor if phase not found
        console.warn(`⚠️ No route found for phase: ${currentPhase}, showing progress monitor`);
        navigate(`/collection/progress/${flowId}`);
      }
    } catch (error) {
      console.error('Error resuming flow:', error);
      toast({
        title: 'Resume Failed',
        description: 'Failed to resume collection flow. Showing progress monitor instead.',
        variant: 'destructive'
      });
      // Fallback to progress monitor on error
      navigate(`/collection/progress/${flowId}`);
    }
  };

  /**
   * Handle starting a new collection via guided workflow
   */
  const handleStartCollection = async () => {
    if (!selectedMethod) {
      toast({
        title: 'Selection Required',
        description: 'Please select a collection method to continue.',
        variant: 'destructive'
      });
      return;
    }

    const workflowId = selectedMethod === 'adaptive' ? 'adaptive-forms' : 'bulk-upload';
    const workflowPath = selectedMethod === 'adaptive' ? '/collection/adaptive-forms' : '/collection/bulk-upload';

    await startCollectionWorkflow(workflowId, workflowPath);
  };

  const getStatusBadge = (status: string, completionRate: number): JSX.Element => {
    if (completionRate > 0) {
      return <Badge variant="secondary"><CheckCircle className="h-3 w-3 mr-1" />{completionRate}% Complete</Badge>;
    }
    switch (status) {
      case 'available':
        return <Badge variant="outline">Ready to Start</Badge>;
      case 'in-progress':
        return <Badge variant="default"><Clock className="h-3 w-3 mr-1" />In Progress</Badge>;
      case 'requires-attention':
        return <Badge variant="destructive"><AlertCircle className="h-3 w-3 mr-1" />Needs Attention</Badge>;
      default:
        return <Badge variant="outline">Available</Badge>;
    }
  };

  /**
   * Start a collection workflow by creating a flow through CrewAI
   */
  const startCollectionWorkflow = async (workflowId: string, workflowPath: string): Promise<void> => {
    console.log(`🚀 Frontend: Starting collection workflow: ${workflowId}`);

    // Check if user has permission to create collection flows
    if (!canCreateCollectionFlow(user)) {
      toast({
        title: 'Permission Denied',
        description: `You do not have permission to create collection flows. Only analysts and above can create flows. Your role: ${getRoleName(user?.role)}`,
        variant: 'destructive'
      });
      return;
    }

    setIsCreatingFlow(workflowId);

    try {
      console.log(`🚀 Starting collection workflow: ${workflowId}`);

      // Determine automation tier and collection config based on workflow type
      let automationTier = 'tier_2'; // Default to mixed environment
      const collectionConfig: unknown = {
        workflow_type: workflowId,
        initiated_from: 'collection_overview'
      };

      switch (workflowId) {
        case 'adaptive-forms':
          automationTier = 'tier_2'; // Mixed: manual forms with some automation
          collectionConfig.collection_method = 'adaptive_forms';
          collectionConfig.form_type = 'dynamic';
          break;

        case 'bulk-upload':
          automationTier = 'tier_3'; // Restricted: mostly manual with file processing
          collectionConfig.collection_method = 'bulk_upload';
          collectionConfig.upload_type = 'spreadsheet';
          break;

        case 'gap-analysis':
          automationTier = 'tier_1'; // Modern: AI-powered gap analysis
          collectionConfig.collection_method = 'gap_analysis';
          collectionConfig.analysis_type = 'two_phase';
          break;

        case 'data-integration':
          automationTier = 'tier_1'; // Modern: mostly automated integration
          collectionConfig.collection_method = 'integration';
          collectionConfig.integration_type = 'multi_source';
          break;

        case 'progress-monitoring':
          // For monitoring, just navigate without creating a flow
          navigate(workflowPath);
          return;
      }

      // Create the collection flow - this triggers CrewAI agents
      console.log('🤖 Creating collection flow with CrewAI orchestration...');
      console.log('📋 Flow data:', { automation_tier: automationTier, collection_config: collectionConfig });

      const flowResponse = await collectionFlowApi.createFlow({
        automation_tier: automationTier,
        collection_config: collectionConfig
      });

      console.log('✅ Flow response:', flowResponse);

      console.log(`✅ Collection flow created: ${flowResponse.id}`);
      console.log(`📊 Master flow started, CrewAI agents are initializing...`);
      console.log(`📍 Flow current phase: ${flowResponse.current_phase || 'unknown'}`);

      // Update the auth context with the new collection flow
      setCurrentFlow({
        id: flowResponse.id,
        name: 'Collection Flow',
        type: 'collection',
        status: flowResponse.status || 'active',
        engagement_id: flowResponse.engagement_id
      });

      toast({
        title: 'Collection Workflow Started',
        description: `CrewAI agents are initializing the ${workflowId} workflow. You will be redirected shortly.`
      });

      // Clear any existing timeout before setting a new one
      if (navigationTimeoutRef.current) {
        clearTimeout(navigationTimeoutRef.current);
      }

      // Give the flow a moment to initialize before navigating
      navigationTimeoutRef.current = window.setTimeout(() => {
        // Navigate based on the flow's current_phase, not hardcoded workflowPath
        // This ensures we respect backend phase routing (e.g., asset_selection before gap_analysis)
        const currentPhase = flowResponse.current_phase || 'gap_analysis'; // Fallback to gap_analysis for backward compat
        const phaseRoute = FLOW_PHASE_ROUTES.collection[currentPhase];

        if (phaseRoute) {
          const targetRoute = phaseRoute(flowResponse.id);
          console.log(`🧭 Navigating to ${currentPhase} phase: ${targetRoute}`);
          navigate(targetRoute);
        } else {
          // Fallback to old behavior if phase not in routes
          console.warn(`⚠️ No route found for phase: ${currentPhase}, using fallback navigation`);
          if (workflowId === 'gap-analysis') {
            navigate(`${workflowPath}/${flowResponse.id}`);
          } else {
            navigate(`${workflowPath}?flowId=${flowResponse.id}`);
          }
        }
        navigationTimeoutRef.current = null;
      }, 1500);

    } catch (error: unknown) {
      console.error(`❌ Failed to start collection workflow ${workflowId}:`, error);

      const errorMessage = error?.response?.data?.detail ||
                          error?.message ||
                          'Failed to start collection workflow';

      toast({
        title: 'Workflow Start Failed',
        description: errorMessage,
        variant: 'destructive'
      });

      // Check if there's an active flow that's blocking
      if (errorMessage.includes('active collection flow already exists')) {
        toast({
          title: 'Active Flow Detected',
          description: 'Please complete or cancel the existing flow before starting a new one.',
          variant: 'destructive'
        });

        // Clear any existing timeout before setting a new one
        if (errorNavigationTimeoutRef.current) {
          clearTimeout(errorNavigationTimeoutRef.current);
        }

        // Navigate to progress monitoring to see active flows
        errorNavigationTimeoutRef.current = window.setTimeout(() => {
          navigate('/collection/progress');
          errorNavigationTimeoutRef.current = null;
        }, 2000);
      }
    } finally {
      setIsCreatingFlow(null);
    }
  };

  return (
    <div className="flex min-h-screen bg-gray-50">
      <div className="hidden lg:block w-64 border-r bg-white">
        <Sidebar />
      </div>
      <div className="flex-1 overflow-y-auto">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-4 sm:py-6 lg:py-8 max-w-5xl">
          <div className="mb-6">
            <ContextBreadcrumbs />
          </div>
          <div className="space-y-6">
      {/* Header */}
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold">Data Curation</h1>
            <p className="text-muted-foreground">
              Collect application data for your migration portfolio
            </p>
          </div>
          {/* Role indicator */}
          <div className="flex items-center space-x-2 text-sm">
            <Shield className="h-4 w-4 text-muted-foreground" />
            <span className="text-muted-foreground">Your role:</span>
            <Badge variant={canCreateCollectionFlow(user) ? "default" : "secondary"}>
              {getRoleName(user?.role)}
            </Badge>
            {!canCreateCollectionFlow(user) && (
              <span className="text-xs text-muted-foreground">(View only)</span>
            )}
          </div>
        </div>
      </div>

      {/* Active Flow Banner - shows when active flow exists */}
      {collectionMetrics.hasActiveFlow && !showNewFlowForm && (
        <div className="rounded-lg border-2 border-blue-500 bg-blue-50 p-6 shadow-sm">
          <div className="mb-3 flex items-center justify-between">
            <div>
              <h3 className="text-lg font-semibold text-blue-900">
                Active Collection Flow Detected
              </h3>
              <p className="text-sm text-blue-700">
                Flow ID: {collectionMetrics.activeFlowId?.slice(0, 8)}... | Status: {collectionMetrics.activeFlowStatus}
              </p>
            </div>
          </div>
          <div className="flex gap-3">
            <Button
              onClick={() => {
                if (collectionMetrics.activeFlowId) {
                  handleResumeFlow(collectionMetrics.activeFlowId);
                }
              }}
              className="bg-blue-600 hover:bg-blue-700 text-white"
              disabled={!canCreateCollectionFlow(user) || !collectionMetrics.activeFlowId}
            >
              Continue Collection
            </Button>
            <Button
              onClick={() => setShowNewFlowForm(true)}
              variant="outline"
              className="border-2 border-blue-600 text-blue-600 hover:bg-blue-50"
              disabled={!canCreateCollectionFlow(user)}
            >
              Start New
            </Button>
          </div>
        </div>
      )}

      {/* Guided Collection Form - shows when no active flow OR user clicked "Start New" */}
      {(!collectionMetrics.hasActiveFlow || showNewFlowForm) && (
        <div className="rounded-lg border border-gray-200 bg-white p-8 shadow-sm">
          <h2 className="mb-4 text-2xl font-bold text-gray-900">
            Start New Data Curation
          </h2>
          <p className="mb-6 text-gray-600">
            {GUIDED_WORKFLOW_CONFIG.question}
          </p>

          <div className="space-y-4 mb-6">
            {GUIDED_WORKFLOW_CONFIG.options.map((option) => {
              const IconComponent = option.icon;
              return (
                <label
                  key={option.id}
                  className={`flex items-start gap-4 p-4 border-2 rounded-lg cursor-pointer transition ${
                    selectedMethod === option.value
                      ? 'border-blue-500 bg-blue-50'
                      : 'border-gray-200 hover:border-blue-300'
                  } ${!canCreateCollectionFlow(user) ? 'opacity-50 cursor-not-allowed' : ''}`}
                >
                  <input
                    type="radio"
                    name="collectionMethod"
                    value={option.value}
                    className="mt-1"
                    checked={selectedMethod === option.value}
                    onChange={() => setSelectedMethod(option.value)}
                    disabled={!canCreateCollectionFlow(user)}
                  />
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <IconComponent className="h-5 w-5 text-gray-700" />
                      <div className="font-semibold text-gray-900">{option.threshold} → {option.title}</div>
                    </div>
                    <div className="text-sm text-gray-600">
                      {option.description}
                    </div>
                    <div className="mt-2 flex items-center gap-1 text-xs text-gray-500">
                      <Clock className="h-3 w-3" />
                      <span>{option.estimatedTime}</span>
                    </div>
                  </div>
                </label>
              );
            })}
          </div>

          <Button
            onClick={handleStartCollection}
            disabled={!selectedMethod || isCreatingFlow !== null || !canCreateCollectionFlow(user)}
            className="w-full bg-green-600 hover:bg-green-700 text-white disabled:bg-gray-300 disabled:cursor-not-allowed"
          >
            {isCreatingFlow !== null ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Starting Collection...
              </>
            ) : (
              'Start Collection'
            )}
          </Button>

          {!canCreateCollectionFlow(user) && (
            <p className="mt-3 text-sm text-center text-red-600">
              Only analysts and above can create collection flows. Your role: {getRoleName(user?.role)}
            </p>
          )}

          {showNewFlowForm && (
            <Button
              onClick={() => setShowNewFlowForm(false)}
              variant="ghost"
              className="w-full mt-3"
            >
              Cancel
            </Button>
          )}
        </div>
      )}

      {/* Advanced Options - collapsible */}
      <div className="rounded-lg border border-gray-200 bg-gray-50 p-4">
        <button
          onClick={() => setShowAdvanced(!showAdvanced)}
          className="flex w-full items-center justify-between text-left"
        >
          <span className="font-semibold text-gray-700">Advanced Options</span>
          {showAdvanced ? (
            <ChevronDown className="h-5 w-5 text-gray-500" />
          ) : (
            <ChevronRight className="h-5 w-5 text-gray-500" />
          )}
        </button>

        {showAdvanced && (
          <div className="mt-4 grid gap-3">
            {advancedWorkflowOptions.map((workflow) => (
              <button
                key={workflow.id}
                onClick={() => {
                  if (workflow.id === 'progress-monitoring') {
                    // Progress monitor doesn't need flow creation
                    navigate(workflow.path);
                  } else {
                    startCollectionWorkflow(workflow.id, workflow.path);
                  }
                }}
                disabled={!canCreateCollectionFlow(user) && workflow.id !== 'progress-monitoring'}
                className="rounded-lg border border-gray-300 bg-white p-4 text-left hover:border-blue-500 hover:bg-blue-50 transition disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <div className="flex items-start gap-3">
                  <div className="p-2 bg-gray-100 rounded-lg">
                    {workflow.icon}
                  </div>
                  <div className="flex-1">
                    <div className="font-semibold text-gray-900">{workflow.title}</div>
                    <div className="text-sm text-gray-600 mt-1">{workflow.description}</div>
                    <div className="mt-2 flex items-center gap-1 text-xs text-gray-500">
                      <Clock className="h-3 w-3" />
                      <span>{workflow.estimatedTime}</span>
                    </div>
                  </div>
                </div>
              </button>
            ))}
          </div>
        )}
      </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CollectionIndex;
