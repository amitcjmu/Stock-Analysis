import React from 'react'
import { useState } from 'react'
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

import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { FormInput, Upload, Settings, BarChart3, Clock, CheckCircle, AlertCircle, Loader2, Shield } from 'lucide-react'

/**
 * Collection workflow index page
 * Provides overview and entry points for all collection workflows
 */
const CollectionIndex: React.FC = () => {
  const navigate = useNavigate();
  const { toast } = useToast();
  const { setCurrentFlow, user } = useAuth();
  const [isCreatingFlow, setIsCreatingFlow] = useState<string | null>(null);

  const workflowOptions = [
    {
      id: 'adaptive-forms',
      title: 'Adaptive Data Collection',
      description: 'Dynamic forms that adapt based on application attributes and user responses',
      icon: <FormInput className="h-6 w-6" />,
      path: '/collection/adaptive-forms',
      status: 'available',
      completionRate: 0,
      estimatedTime: '15-30 min per application'
    },
    {
      id: 'bulk-upload',
      title: 'Bulk Data Upload',
      description: 'Upload and process multiple applications data via CSV/Excel templates',
      icon: <Upload className="h-6 w-6" />,
      path: '/collection/bulk-upload',
      status: 'available',
      completionRate: 0,
      estimatedTime: '5-10 min for 100+ applications'
    },
    {
      id: 'data-integration',
      title: 'Data Integration & Validation',
      description: 'Resolve conflicts and validate data from multiple collection sources',
      icon: <Settings className="h-6 w-6" />,
      path: '/collection/data-integration',
      status: 'available',
      completionRate: 0,
      estimatedTime: '10-20 min'
    },
    {
      id: 'progress-monitoring',
      title: 'Collection Progress Monitor',
      description: 'Monitor collection workflows and track completion status',
      icon: <BarChart3 className="h-6 w-6" />,
      path: '/collection/progress',
      status: 'available',
      completionRate: 0,
      estimatedTime: 'Real-time monitoring'
    }
  ];

  const getStatusBadge = (status: string, completionRate: number) => {
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
  const startCollectionWorkflow = async (workflowId: string, workflowPath: string) => {
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
      
      // Give the flow a moment to initialize before navigating
      setTimeout(() => {
        // Navigate to the workflow page with the flow ID
        navigate(`${workflowPath}?flowId=${flowResponse.id}`);
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
        
        // Navigate to progress monitoring to see active flows
        setTimeout(() => {
          navigate('/collection/progress');
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
        <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-4 sm:py-6 lg:py-8 max-w-7xl">
          <div className="mb-6">
            <ContextBreadcrumbs />
          </div>
          <div className="space-y-6">
      {/* Header */}
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold">Data Collection Workflows</h1>
            <p className="text-muted-foreground">
              Choose the best data collection approach for your applications and infrastructure
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

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center space-x-2">
              <div className="p-2 bg-blue-100 rounded-lg">
                <FormInput className="h-4 w-4 text-blue-600" />
              </div>
              <div>
                <p className="text-sm font-medium">Active Forms</p>
                <p className="text-2xl font-bold">0</p>
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center space-x-2">
              <div className="p-2 bg-green-100 rounded-lg">
                <Upload className="h-4 w-4 text-green-600" />
              </div>
              <div>
                <p className="text-sm font-medium">Bulk Uploads</p>
                <p className="text-2xl font-bold">0</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center space-x-2">
              <div className="p-2 bg-orange-100 rounded-lg">
                <Settings className="h-4 w-4 text-orange-600" />
              </div>
              <div>
                <p className="text-sm font-medium">Pending Conflicts</p>
                <p className="text-2xl font-bold">0</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center space-x-2">
              <div className="p-2 bg-purple-100 rounded-lg">
                <CheckCircle className="h-4 w-4 text-purple-600" />
              </div>
              <div>
                <p className="text-sm font-medium">Completion Rate</p>
                <p className="text-2xl font-bold">0%</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Workflow Options */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {workflowOptions.map((workflow) => (
          <Card key={workflow.id} className="hover:shadow-lg transition-shadow cursor-pointer">
            <CardHeader>
              <div className="flex items-start justify-between">
                <div className="flex items-center space-x-3">
                  <div className="p-2 bg-primary/10 rounded-lg">
                    {workflow.icon}
                  </div>
                  <div>
                    <CardTitle className="text-lg">{workflow.title}</CardTitle>
                    <div className="mt-1">
                      {getStatusBadge(workflow.status, workflow.completionRate)}
                    </div>
                  </div>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <p className="text-muted-foreground mb-4">{workflow.description}</p>
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-1 text-sm text-muted-foreground">
                  <Clock className="h-3 w-3" />
                  <span>{workflow.estimatedTime}</span>
                </div>
                <Button 
                  onClick={() => startCollectionWorkflow(workflow.id, workflow.path)}
                  variant="outline"
                  size="sm"
                  disabled={isCreatingFlow === workflow.id || !canCreateCollectionFlow(user)}
                  title={!canCreateCollectionFlow(user) ? `Only analysts and above can create collection flows. Your role: ${getRoleName(user?.role)}` : ''}
                >
                  {isCreatingFlow === workflow.id ? (
                    <>
                      <Loader2 className="h-3 w-3 mr-1 animate-spin" />
                      Starting...
                    </>
                  ) : (
                    'Start Workflow'
                  )}
                </Button>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Getting Started Tips */}
      <Card>
        <CardHeader>
          <CardTitle>Getting Started with Data Collection</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <h4 className="font-medium mb-2">For Small to Medium Portfolios (1-50 apps)</h4>
              <p className="text-sm text-muted-foreground mb-2">
                Start with Adaptive Data Collection for detailed, application-specific insights
              </p>
              <Button 
                variant="outline" 
                size="sm"
                onClick={() => startCollectionWorkflow('adaptive-forms', '/collection/adaptive-forms')}
                disabled={isCreatingFlow === 'adaptive-forms' || !canCreateCollectionFlow(user)}
                title={!canCreateCollectionFlow(user) ? `Only analysts and above can create collection flows. Your role: ${getRoleName(user?.role)}` : ''}
              >
                {isCreatingFlow === 'adaptive-forms' ? (
                  <>
                    <Loader2 className="h-3 w-3 mr-1 animate-spin" />
                    Starting...
                  </>
                ) : (
                  'Start Adaptive Collection'
                )}
              </Button>
            </div>
            <div>
              <h4 className="font-medium mb-2">For Large Portfolios (50+ apps)</h4>
              <p className="text-sm text-muted-foreground mb-2">
                Begin with Bulk Data Upload to efficiently process large application inventories
              </p>
              <Button 
                variant="outline" 
                size="sm"
                onClick={() => startCollectionWorkflow('bulk-upload', '/collection/bulk-upload')}
                disabled={isCreatingFlow === 'bulk-upload' || !canCreateCollectionFlow(user)}
                title={!canCreateCollectionFlow(user) ? `Only analysts and above can create collection flows. Your role: ${getRoleName(user?.role)}` : ''}
              >
                {isCreatingFlow === 'bulk-upload' ? (
                  <>
                    <Loader2 className="h-3 w-3 mr-1 animate-spin" />
                    Starting...
                  </>
                ) : (
                  'Start Bulk Upload'
                )}
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CollectionIndex;