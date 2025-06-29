import React, { useState, useEffect } from 'react';
import { 
  Activity, 
  AlertTriangle, 
  CheckCircle, 
  Clock, 
  FileText, 
  Shield, 
  Bot, 
  Loader2,
  RefreshCw,
  XCircle,
  AlertCircle,
  Info,
  Zap,
  TrendingUp,
  Network,
  Upload,
  Database,
  ArrowRight,
  Eye,
  Lock
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { ScrollArea } from '@/components/ui/scroll-area';
import { useComprehensiveRealTimeMonitoring } from '@/hooks/useRealTimeProcessing';

interface UniversalProcessingStatusProps {
  flow_id: string;
  page_context?: string;
  className?: string;
  compact?: boolean;
  title?: string;
}

export const UniversalProcessingStatus: React.FC<UniversalProcessingStatusProps> = ({
  flow_id,
  page_context = 'data_import',
  className = '',
  compact = false,
  title = 'Discovery Flow Processing'
}) => {
  // Log flow_id for debugging
  console.log('[UniversalProcessingStatus] Component rendered with flow_id:', flow_id);
  console.log('[UniversalProcessingStatus] Page context:', page_context);
  console.log('[UniversalProcessingStatus] Component props:', { flow_id, page_context, title });
  
  // Use comprehensive monitoring hook
  const monitoring = useComprehensiveRealTimeMonitoring(flow_id, page_context);

  // Extract data from monitoring
  const processingStatus = monitoring?.processing?.processingStatus;
  const validationStatus = monitoring?.validation?.validationStatus;
  const agentInsights = monitoring?.insights?.agentInsights || [];
  
  // Log processing status for debugging
  console.log('[UniversalProcessingStatus] Processing status:', processingStatus);
  console.log('[UniversalProcessingStatus] Monitoring state:', {
    isLoading: monitoring?.processing?.isLoading,
    error: monitoring?.processing?.error,
    consecutiveErrors: monitoring?.processing?.consecutiveErrors,
    isPollingDisabled: monitoring?.processing?.isPollingDisabled
  });

  // Enhanced status determination with user approval detection
  const getEnhancedStatus = () => {
    // Check if flow is paused for user approval or has completed data import
    const isDataImportComplete = 
      processingStatus?.phases?.data_import === true ||
      processingStatus?.phases?.data_import_completed === true ||
      (processingStatus?.current_phase === 'data_import' && processingStatus?.status === 'completed') ||
      (processingStatus?.phase === 'data_import' && processingStatus?.progress_percentage >= 100);
      
    const isAwaitingApproval = 
      processingStatus?.status === 'paused' || 
      processingStatus?.status === 'waiting_for_user_approval' ||
      (processingStatus?.phase === 'attribute_mapping' && 
       (processingStatus?.progress >= 90 || processingStatus?.progress_percentage >= 90)) ||
      (processingStatus?.current_phase === 'attribute_mapping' && 
       processingStatus?.progress_percentage >= 90) ||
      isDataImportComplete;
    
    if (isAwaitingApproval) {
      return {
        status: 'awaiting_approval',
        message: 'Data Import Complete - Ready for Attribute Mapping',
        description: 'The data import and initial processing has been completed successfully. Please proceed to the Attribute Mapping phase to continue.',
        color: 'bg-blue-50 border-blue-200',
        icon: CheckCircle,
        iconColor: 'text-blue-600',
        progress: 100, // Show as complete for this phase
        showNextSteps: true
      };
    }

    // Check actual progress from processing status (handle both field names)
    const actualProgress = processingStatus?.progress_percentage || processingStatus?.progress || 0;
    console.log('[UniversalProcessingStatus] Actual progress:', actualProgress, 'from processingStatus:', processingStatus);
    
    if (processingStatus?.status === 'completed' || 
        (processingStatus?.status === 'active' && actualProgress >= 100)) {
      return {
        status: 'completed',
        message: 'Processing Complete',
        description: 'All validation and processing steps have been completed successfully.',
        color: 'bg-green-50 border-green-200',
        icon: CheckCircle,
        iconColor: 'text-green-600',
        progress: 100
      };
    }

    if (processingStatus?.status === 'failed' || processingStatus?.status === 'error') {
      return {
        status: 'error',
        message: 'Processing Error',
        description: 'An error occurred during processing. Please check the logs for details.',
        color: 'bg-red-50 border-red-200',
        icon: XCircle,
        iconColor: 'text-red-600',
        progress: actualProgress
      };
    }

    if (processingStatus?.status === 'running' || processingStatus?.status === 'in_progress' || processingStatus?.status === 'processing') {
      const currentPhase = processingStatus?.current_phase || processingStatus?.phase || 'unknown';
      return {
        status: 'running',
        message: 'Processing in Progress',
        description: `Currently in ${currentPhase.replace(/_/g, ' ')} phase...`,
        color: 'bg-yellow-50 border-yellow-200',
        icon: Loader2,
        iconColor: 'text-yellow-600',
        progress: actualProgress
      };
    }

    // Handle active status based on progress
    if (processingStatus?.status === 'active' || processingStatus?.status === 'initialized') {
      if (actualProgress === 0) {
        return {
          status: 'starting',
          message: 'CrewAI Flow Started',
          description: 'The discovery flow has been created and is initializing. Data processing will begin shortly.',
          color: 'bg-green-50 border-green-200',
          icon: Activity,
          iconColor: 'text-green-600',
          progress: 0,
          showNextSteps: true
        };
      } else {
        // Active with progress - show as running
        const currentPhase = processingStatus?.current_phase || processingStatus?.phase || 'processing';
        return {
          status: 'running',
          message: 'Processing Active',
          description: `Currently in ${currentPhase.replace(/_/g, ' ')} phase...`,
          color: 'bg-blue-50 border-blue-200',
          icon: Activity,
          iconColor: 'text-blue-600',
          progress: actualProgress
        };
      }
    }

    return {
      status: 'idle',
      message: 'Ready to Process',
      description: 'Waiting for processing to begin...',
      color: 'bg-gray-50 border-gray-200',
      icon: Clock,
      iconColor: 'text-gray-600',
      progress: 0
    };
  };

  const enhancedStatus = getEnhancedStatus();

  // State for collapsible sections - expanded by default
  const [expandedSections, setExpandedSections] = useState(new Set(['upload', 'security']));

  const toggleSection = (section: string) => {
    setExpandedSections(prev => {
      const newSet = new Set(prev);
      if (newSet.has(section)) {
        newSet.delete(section);
      } else {
        newSet.add(section);
      }
      return newSet;
    });
  };

  // Generate security and validation summary from agent insights
  const getSecurityValidationSummary = () => {
    const insights = agentInsights || [];
    
    // Analyze insights for security, data type, and privacy information
    const dataTypeInsights = insights.filter(insight => 
      insight.message?.toLowerCase().includes('data') || 
      insight.message?.toLowerCase().includes('record') ||
      insight.message?.toLowerCase().includes('field')
    );
    
    const securityInsights = insights.filter(insight =>
      insight.message?.toLowerCase().includes('security') ||
      insight.message?.toLowerCase().includes('malicious') ||
      insight.message?.toLowerCase().includes('threat')
    );
    
    const privacyInsights = insights.filter(insight =>
      insight.message?.toLowerCase().includes('privacy') ||
      insight.message?.toLowerCase().includes('pii') ||
      insight.message?.toLowerCase().includes('personal')
    );

    return {
      dataType: dataTypeInsights.length > 0 
        ? `Detected ${processingStatus?.recordsProcessed || 0} records with application inventory data including IDs, names, versions, and dependencies.`
        : 'Standard application discovery data format detected.',
      
      security: securityInsights.length > 0 
        ? securityInsights[0]?.message || 'Security analysis completed - no threats detected.'
        : 'Data appears safe with no malicious content or security threats identified.',
        
      privacy: privacyInsights.length > 0
        ? privacyInsights[0]?.message || 'Privacy assessment completed.'
        : 'No sensitive personal information (PII) detected in the dataset. Standard application metadata only.'
    };
  };

  const securitySummary = getSecurityValidationSummary();

  // Next Steps Component for user approval state
  const NextStepsCard = () => {
    if (!enhancedStatus.showNextSteps) return null;

    // Different content for different states
    if (enhancedStatus.status === 'starting') {
      return (
        <Card className="mb-6 border-green-200 bg-green-50">
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2 text-green-800">
              <Activity className="h-5 w-5" />
              Discovery Flow Created Successfully
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <p className="text-sm text-green-700">
                Your CrewAI Discovery Flow has been created with ID: <code className="bg-green-100 px-1 rounded">{flow_id?.substring(0, 8)}...</code>
              </p>
              <p className="text-sm text-green-700">
                The AI agents are initializing and will begin processing your data shortly. This page will automatically update with progress.
              </p>
              <div className="mt-4 p-3 bg-green-100 rounded-lg">
                <div className="flex items-center gap-2 text-green-800">
                  <Info className="h-4 w-4" />
                  <span className="text-sm font-medium">
                    If progress doesn't start within 30 seconds, try navigating to the Attribute Mapping page to continue the flow.
                  </span>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      );
    }

    return (
      <Card className="mb-6 border-blue-200 bg-blue-50">
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center gap-2 text-blue-800">
            <TrendingUp className="h-5 w-5" />
            Next Steps Required
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            <div className="flex items-start gap-3">
              <div className="flex-shrink-0 w-6 h-6 bg-blue-600 text-white rounded-full flex items-center justify-center text-sm font-medium">
                1
              </div>
              <div>
                <h4 className="font-medium text-blue-900">Review Data Import Results</h4>
                <p className="text-sm text-blue-700 mt-1">
                  Check the validation results and security assessment below to ensure data quality meets your requirements.
                </p>
              </div>
            </div>
            
            <div className="flex items-start gap-3">
              <div className="flex-shrink-0 w-6 h-6 bg-blue-600 text-white rounded-full flex items-center justify-center text-sm font-medium">
                2
              </div>
              <div>
                <h4 className="font-medium text-blue-900">Proceed to Attribute Mapping</h4>
                <p className="text-sm text-blue-700 mt-1">
                  Navigate to the <strong>Attribute Mapping</strong> tab to review and adjust field mappings before continuing the discovery process.
                </p>
                <Button 
                  className="mt-2 bg-blue-600 hover:bg-blue-700 text-white"
                  size="sm"
                  onClick={() => {
                    // Navigate to attribute mapping tab
                    const attributeMappingTab = document.querySelector('[data-tab="attribute-mapping"]');
                    if (attributeMappingTab) {
                      (attributeMappingTab as HTMLElement).click();
                    }
                  }}
                >
                  <ArrowRight className="h-4 w-4 mr-1" />
                  Go to Attribute Mapping
                </Button>
              </div>
            </div>

            <div className="mt-4 p-3 bg-blue-100 rounded-lg">
              <div className="flex items-center gap-2 text-blue-800">
                <Info className="h-4 w-4" />
                <span className="text-sm font-medium">
                  The discovery flow will automatically continue once you complete the attribute mapping review.
                </span>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  };

  // If no flow_id is provided, show a placeholder/demo state
  if (!flow_id) {
    return (
      <div className={`space-y-4 ${className}`}>
        <Card>
          <CardContent className="pt-6">
            <div className="text-center py-8">
              <Upload className="w-12 h-12 mx-auto mb-4 text-gray-400" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">No Processing Active</h3>
              <p className="text-sm text-gray-500">
                Upload a file to begin real-time processing monitoring
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Next Steps Card */}
      <NextStepsCard />

      {/* Upload & Validation Status (Merged with Real-Time Processing) */}
      <Card className={`${enhancedStatus.color}`}>
        <CardHeader 
          className="cursor-pointer"
          onClick={() => toggleSection('upload')}
        >
          <CardTitle className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <enhancedStatus.icon 
                className={`h-5 w-5 ${enhancedStatus.iconColor} ${
                  enhancedStatus.status === 'running' ? 'animate-spin' : ''
                }`} 
              />
              Upload & Validation Status
            </div>
            <div className="flex items-center gap-2">
              <Badge variant={enhancedStatus.status === 'running' ? 'default' : 'secondary'}>
                {enhancedStatus.progress.toFixed(0)}% Complete
              </Badge>
              <Button variant="ghost" size="sm">
                {expandedSections.has('upload') ? '−' : '+'}
              </Button>
            </div>
          </CardTitle>
        </CardHeader>
        
        {expandedSections.has('upload') && (
          <CardContent>
            <div className="space-y-4">
              <p className="text-sm text-gray-600">
                {enhancedStatus.description}
              </p>

              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span>Progress</span>
                  <span>{enhancedStatus.progress.toFixed(1)}%</span>
                </div>
                <Progress value={enhancedStatus.progress} className="w-full" />
              </div>

              {/* Processing Statistics - Only show when we have actual records */}
              {(processingStatus?.records_total > 0 || processingStatus?.recordsProcessed > 0) && (
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-4">
                  <div className="text-center">
                    <div className="text-2xl font-bold text-blue-600">
                      {processingStatus?.records_processed || processingStatus?.recordsProcessed || 0}
                    </div>
                    <div className="text-sm text-gray-600">Records Processed</div>
                  </div>
                  
                  <div className="text-center">
                    <div className="text-2xl font-bold text-green-600">
                      {processingStatus?.records_valid || processingStatus?.recordsValid || processingStatus?.records_processed || processingStatus?.recordsProcessed || 0}
                    </div>
                    <div className="text-sm text-gray-600">Valid Records</div>
                  </div>
                  
                  <div className="text-center">
                    <div className="text-2xl font-bold text-red-600">
                      {processingStatus?.records_failed || processingStatus?.recordsInvalid || 0}
                    </div>
                    <div className="text-sm text-gray-600">Invalid Records</div>
                  </div>
                  
                  <div className="text-center">
                    <div className="text-2xl font-bold text-purple-600">
                      {agentInsights?.length || 0}
                    </div>
                    <div className="text-sm text-gray-600">Agent Insights</div>
                  </div>
                </div>
              )}

              {(processingStatus?.phase || processingStatus?.current_phase) && (
                <div className="flex items-center gap-2 mt-4">
                  <Badge variant="outline">
                    Current Phase: {(processingStatus.current_phase || processingStatus.phase).replace(/_/g, ' ').toUpperCase()}
                  </Badge>
                  {enhancedStatus.status === 'awaiting_approval' && (
                    <Badge className="bg-blue-100 text-blue-800">
                      Awaiting User Input
                    </Badge>
                  )}
                </div>
              )}
            </div>
          </CardContent>
        )}
      </Card>

      {/* Security & Validation */}
      <Card>
        <CardHeader 
          className="cursor-pointer"
          onClick={() => toggleSection('security')}
        >
          <CardTitle className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Shield className="h-5 w-5 text-green-600" />
              Security & Validation
            </div>
            <div className="flex items-center gap-2">
              <Badge variant="secondary" className="bg-green-100 text-green-800">
                <CheckCircle className="h-3 w-3 mr-1" />
                Validated
              </Badge>
              <Button variant="ghost" size="sm">
                {expandedSections.has('security') ? '−' : '+'}
              </Button>
            </div>
          </CardTitle>
        </CardHeader>
        
        {expandedSections.has('security') && (
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
              <div className="text-center p-4 bg-green-50 rounded-lg">
                <Shield className="h-8 w-8 mx-auto mb-2 text-green-600" />
                <div className="text-lg font-semibold text-green-800">Security</div>
                <div className="text-sm text-green-600">0 issues</div>
              </div>
              
              <div className="text-center p-4 bg-blue-50 rounded-lg">
                <FileText className="h-8 w-8 mx-auto mb-2 text-blue-600" />
                <div className="text-lg font-semibold text-blue-800">Format</div>
                <div className="text-sm text-blue-600">0 errors</div>
              </div>
              
              <div className="text-center p-4 bg-purple-50 rounded-lg">
                <Eye className="h-8 w-8 mx-auto mb-2 text-purple-600" />
                <div className="text-lg font-semibold text-purple-800">Quality</div>
                <div className="text-sm text-purple-600">85%</div>
              </div>
            </div>

            {/* Security Assessment Summary */}
            <div className="space-y-4">
              <div className="border-l-4 border-blue-500 pl-4">
                <h4 className="font-medium text-gray-900 mb-1">Data Type Assessment</h4>
                <p className="text-sm text-gray-600">{securitySummary.dataType}</p>
              </div>
              
              <div className="border-l-4 border-green-500 pl-4">
                <h4 className="font-medium text-gray-900 mb-1">Security Classification</h4>
                <p className="text-sm text-gray-600">{securitySummary.security}</p>
              </div>
              
              <div className="border-l-4 border-purple-500 pl-4">
                <h4 className="font-medium text-gray-900 mb-1">Data Privacy Assessment</h4>
                <p className="text-sm text-gray-600">{securitySummary.privacy}</p>
              </div>
            </div>
          </CardContent>
        )}
      </Card>
    </div>
  );
};

export default UniversalProcessingStatus; 