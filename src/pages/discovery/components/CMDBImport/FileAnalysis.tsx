import React, { useEffect } from 'react';
import { 
  CheckCircle, 
  AlertTriangle, 
  RefreshCw, 
  FileSpreadsheet, 
  ExternalLink,
  AlertCircle,
  Lightbulb,
  ArrowRight,
  Loader2,
  Bot,
  Clock
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { UploadedFile, useDiscoveryFlowStatus } from '../../hooks/useCMDBImport';
import { useQueryClient } from '@tanstack/react-query';

interface FileAnalysisProps {
  file: UploadedFile;
  onRetry?: () => void;
  onNavigate: (path: string, state?: any) => void;
}

export const FileAnalysis: React.FC<FileAnalysisProps> = ({ file, onRetry, onNavigate }) => {
  const queryClient = useQueryClient();
  
  // Use the centralized status polling hook instead of creating a duplicate query
  const { data: statusData, isLoading: isLoadingStatus } = useDiscoveryFlowStatus(
    file.status === 'analyzing' ? file.id : null
  );
  
  // Update the file status when status data changes
  useEffect(() => {
    if (!statusData) return;
    
    const status = statusData.status;
    const current_phase = statusData.current_phase;
    
    console.log(`Status update for ${file.id}:`, { status, current_phase, statusData });
    
    // Update the file status based on the workflow status
    if (status === 'completed') {
      // Update the file status to 'processed' when analysis is complete
      queryClient.setQueryData<UploadedFile[]>(['uploadedFiles'], (old = []) =>
        old.map(f => f.id === file.id ? {
          ...f,
          status: 'processed' as const,
          currentStep: 5, // All steps complete
          processingMessages: ['✅ Analysis complete. Ready for next steps.'],
          aiSuggestions: ['File processed successfully'],
          nextSteps: [
            {
              label: 'Proceed to Attribute Mapping',
              route: '/discovery/attribute-mapping',
              description: 'Map your data fields to standard attributes',
              import_session_id: file.id
            }
          ]
        } : f)
      );
    } else if (status === 'failed' || status === 'error') {
      // Update the file status to 'error' if analysis failed
      queryClient.setQueryData<UploadedFile[]>(['uploadedFiles'], (old = []) =>
        old.map(f => f.id === file.id ? {
          ...f,
          status: 'error' as const,
          analysisError: 'Analysis failed. Please try again.',
          processingMessages: ['❌ Analysis failed. Please try again.']
        } : f)
      );
    } else if (status === 'running') {
      // Update the current step and processing messages based on the current phase
      const stepMap: Record<string, number> = {
        'initialization': 0,
        'data_source_analysis': 1,
        'data_validation': 2,
        'field_mapping': 3,
        'asset_classification': 4,
        'dependency_analysis': 5,
        'database_integration': 6
      };
      
      const currentStep = stepMap[current_phase] || 0;
      
      queryClient.setQueryData<UploadedFile[]>(['uploadedFiles'], (old = []) =>
        old.map(f => f.id === file.id ? {
          ...f,
          status: 'analyzing' as const,
          currentStep,
          processingMessages: [
            ...(f.processingMessages || []).filter(m => !m.startsWith('🤖')),
            `🤖 ${current_phase ? `Processing: ${current_phase.replace(/_/g, ' ')}` : 'Analyzing...'}`
          ].slice(-5) // Keep only the last 5 messages
        } : f)
      );
    }
  }, [statusData, file.id, queryClient]);
  const getStatusIcon = (status: UploadedFile['status']) => {
    switch (status) {
      case 'uploaded':
        return <FileSpreadsheet className="h-5 w-5 text-gray-500" />;
      case 'analyzing':
        return <RefreshCw className="h-5 w-5 text-blue-500 animate-spin" />;
      case 'processed':
        return <CheckCircle className="h-5 w-5 text-green-500" />;
      case 'error':
        return <AlertTriangle className="h-5 w-5 text-red-500" />;
      default:
        return <FileSpreadsheet className="h-5 w-5 text-gray-500" />;
    }
  };

  const handleNavigation = (step: any) => {
    if (step.route === '/discovery/data-cleansing' && step.dataQualityIssues) {
      onNavigate(step.route, {
        state: {
          dataQualityIssues: step.dataQualityIssues,
          fromDataImport: true
        }
      });
    } else if (step.route === '/discovery/attribute-mapping' && (step.importedData || step.import_session_id)) {
      onNavigate(step.route, {
        state: {
          importedData: step.importedData,
          import_session_id: step.import_session_id,
          fromDataImport: true
        }
      });
    } else if (step.route) {
      onNavigate(step.route);
    }
  };

  return (
    <div className="border border-gray-200 rounded-lg p-6 transition-all duration-300 hover:shadow-md">
      {/* File Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-3">
          {getStatusIcon(file.status)}
          <div>
            <h3 className="font-medium text-gray-900">{file.file.name}</h3>
            <div className="flex items-center space-x-2 text-sm text-gray-500">
              <span>{(file.file.size / 1024 / 1024).toFixed(2)} MB</span>
              {file.detectedFileType && (
                <>
                  <span>•</span>
                  <span className="text-blue-600 font-medium">{file.detectedFileType}</span>
                </>
              )}
            </div>
          </div>
        </div>
        {file.confidence && (
          <div className="text-right">
            <div className="text-lg font-semibold text-green-600">{file.confidence}%</div>
            <div className="text-xs text-gray-500">AI Confidence</div>
          </div>
        )}
      </div>

      {/* Processing Animation */}
      {(file.status === 'analyzing' || file.status === 'uploaded') && (
        <div className="space-y-4">
          <div className="bg-gradient-to-r from-blue-50 to-purple-50 border border-blue-200 rounded-lg p-4">
            <div className="flex items-center space-x-2 mb-3">
              <Bot className="h-5 w-5 text-blue-600 animate-bounce" />
              <h4 className="font-medium text-blue-900">AI Crew Processing</h4>
              <Loader2 className="h-4 w-4 text-blue-600 animate-spin" />
            </div>
            
            {/* Processing Steps */}
            <div className="space-y-2 mb-4">
              {file.analysisSteps?.map((step, idx) => (
                <div 
                  key={idx} 
                  className={`flex items-center space-x-2 text-sm transition-all duration-300 ${
                    idx <= (file.currentStep || 0) ? 'text-blue-800' : 'text-gray-500'
                  }`}
                >
                  {idx < (file.currentStep || 0) ? (
                    <CheckCircle className="h-4 w-4 text-green-500" />
                  ) : idx === (file.currentStep || 0) ? (
                    <Loader2 className="h-4 w-4 text-blue-600 animate-spin" />
                  ) : (
                    <Clock className="h-4 w-4 text-gray-400" />
                  )}
                  <span className={idx <= (file.currentStep || 0) ? 'font-medium' : ''}>
                    {step}
                  </span>
                </div>
              ))}
            </div>
            
            {/* Live Processing Messages */}
            {file.processingMessages && file.processingMessages.length > 0 && (
              <div className="bg-white rounded p-3 max-h-32 overflow-y-auto">
                <div className="text-xs text-gray-600 mb-1">Live Analysis Feed:</div>
                {file.processingMessages.map((message, idx) => (
                  <div key={idx} className="text-sm text-gray-800 animate-fade-in flex items-center space-x-1">
                    <span className="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></span>
                    <span>{message}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Analysis Results */}
      {file.status === 'processed' && file.aiSuggestions && (
        <div className="space-y-4">
          {/* File Type Detection */}
          <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
            <div className="flex items-center space-x-2 mb-2">
              <CheckCircle className="h-5 w-5 text-gray-600" />
              <h4 className="font-medium text-gray-900">File Analysis Summary</h4>
            </div>
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-gray-600">Detected Type:</span>
                <span className="ml-2 font-medium text-blue-600">
                  {file.detectedFileType || 'Unknown'}
                </span>
              </div>
              <div>
                <span className="text-gray-600">Confidence:</span>
                <span className="ml-2 font-medium text-green-600">
                  {file.confidence}%
                </span>
              </div>
            </div>
          </div>

          {/* AI Insights */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <div className="flex items-center space-x-2 mb-3">
              <Lightbulb className="h-5 w-5 text-blue-600" />
              <h4 className="font-medium text-blue-900">AI Crew Insights</h4>
            </div>
            <ul className="space-y-2">
              {file.aiSuggestions.map((suggestion, idx) => (
                <li key={idx} className="text-sm text-blue-800 flex items-start space-x-2">
                  <CheckCircle className="h-4 w-4 text-blue-600 flex-shrink-0 mt-0.5" />
                  <span>{suggestion}</span>
                </li>
              ))}
            </ul>
          </div>

          {/* Next Steps */}
          {file.nextSteps && file.nextSteps.length > 0 && (
            <div className="bg-green-50 border border-green-200 rounded-lg p-4">
              <div className="flex items-center space-x-2 mb-3">
                <ArrowRight className="h-5 w-5 text-green-600" />
                <h4 className="font-medium text-green-900">Recommended Next Steps</h4>
              </div>
              <div className="space-y-3">
                {file.nextSteps.map((step, idx) => (
                  <div key={idx}>
                    {step.route ? (
                      <button
                        onClick={() => handleNavigation(step)}
                        className="group block w-full text-left p-3 border border-green-200 rounded-lg hover:border-green-400 hover:bg-green-100 transition-all duration-200"
                      >
                        <div className="flex items-center justify-between">
                          <div className="flex items-start space-x-3">
                            <div className="bg-green-600 text-white rounded-full w-6 h-6 flex items-center justify-center text-sm font-bold flex-shrink-0 mt-0.5">
                              {idx + 1}
                            </div>
                            <div className="flex-1">
                              <div className="text-sm font-medium text-green-800 group-hover:text-green-900">
                                {step.label}
                              </div>
                              {step.description && (
                                <div className="text-xs text-green-600 mt-1">
                                  {step.description}
                                </div>
                              )}
                            </div>
                          </div>
                          <ExternalLink className="h-4 w-4 text-green-500 group-hover:text-green-700 flex-shrink-0" />
                        </div>
                      </button>
                    ) : (
                      <div className="flex items-start space-x-3 p-3 bg-green-100 rounded-lg">
                        <div className="bg-green-600 text-white rounded-full w-6 h-6 flex items-center justify-center text-sm font-bold flex-shrink-0 mt-0.5">
                          {idx + 1}
                        </div>
                        <div className="flex-1">
                          <div className="text-sm font-medium text-green-800">
                            {step.label}
                          </div>
                          {step.description && (
                            <div className="text-xs text-green-600 mt-1">
                              {step.description}
                            </div>
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Error State */}
      {file.status === 'error' && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <AlertCircle className="h-5 w-5 text-red-600" />
              <span className="text-red-800">
                {file.analysisError || 'Analysis failed - please try again'}
              </span>
            </div>
            {onRetry && (
              <Button 
                variant="outline" 
                size="sm" 
                onClick={onRetry}
                className="text-red-600 border-red-200 hover:bg-red-50"
              >
                Retry
              </Button>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
