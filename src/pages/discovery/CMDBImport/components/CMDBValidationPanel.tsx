import React from 'react';
import { 
  FileCheck, 
  Shield, 
  UserCheck, 
  CheckCircle, 
  XCircle, 
  AlertTriangle, 
  Clock 
} from 'lucide-react';
import { Progress } from '@/components/ui/progress';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { UploadFile } from '../CMDBImport.types';
import { getStatusStyling } from '../utils/statusUtils';
import { useComprehensiveRealTimeMonitoring } from '@/hooks/useRealTimeProcessing';

interface CMDBValidationPanelProps {
  file: UploadFile;
  onValidationUpdate: (validationData: any) => void;
}

export const CMDBValidationPanel: React.FC<CMDBValidationPanelProps> = ({ 
  file, 
  onValidationUpdate 
}) => {
  const monitoring = file.flow_id ? useComprehensiveRealTimeMonitoring(file.flow_id, 'data_import') : null;
  
  // Get validation data from real-time monitoring or fallback to defaults
  const validationData = monitoring?.data?.validationResult || {};
  const hasRealTimeData = !!monitoring?.data;
  
  // Call update callback when we have new validation data
  React.useEffect(() => {
    if (hasRealTimeData && validationData) {
      onValidationUpdate(validationData);
    }
  }, [hasRealTimeData, validationData, onValidationUpdate]);
  
  // Progress calculation
  const agentsCompleted = file.agents_completed || 0;
  const totalAgents = file.total_agents || 4;
  const validationProgress = hasRealTimeData 
    ? (validationData.validation_progress || 0) 
    : Math.round((agentsCompleted / totalAgents) * 100);
  
  // Status determination from real-time data or file state
  const formatStatus = hasRealTimeData 
    ? (validationData.format_validation?.status || 'pending')
    : (file.format_validation ? 'passed' : 'pending');
    
  const securityStatus = hasRealTimeData
    ? (validationData.security_scan?.status || 'pending')
    : (file.security_clearance ? 'passed' : 'pending');
    
  const privacyStatus = hasRealTimeData
    ? (validationData.privacy_issues && validationData.privacy_issues.length > 0 ? 'warning' : 'passed')
    : (file.privacy_clearance ? 'passed' : 'pending');
  
  const formatStyling = getStatusStyling(formatStatus);
  const securityStyling = getStatusStyling(securityStatus);
  const privacyStyling = getStatusStyling(privacyStatus);
  
  return (
    <div className="space-y-4">
      <div className="space-y-2">
        <div className="flex items-center justify-between text-sm">
          <span>Validation Progress</span>
          <span>{agentsCompleted}/{totalAgents} agents completed</span>
        </div>
        <Progress value={validationProgress} className="h-2" />
        {hasRealTimeData && (
          <div className="text-xs text-gray-500">
            Real-time validation status • Last updated: {new Date().toLocaleTimeString()}
          </div>
        )}
      </div>

      {/* Security Clearances with Real-time Status */}
      <div className="grid grid-cols-3 gap-4">
        <div className={`p-3 rounded-lg border ${formatStyling.bg}`}>
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <FileCheck className={`h-4 w-4 ${formatStyling.icon}`} />
              <span className={`text-sm font-medium ${formatStyling.text}`}>Format Valid</span>
            </div>
            {formatStatus === 'failed' && (
              <XCircle className="h-4 w-4 text-red-500" />
            )}
            {formatStatus === 'passed' && (
              <CheckCircle className="h-4 w-4 text-green-500" />
            )}
            {formatStatus === 'pending' && (
              <Clock className="h-4 w-4 text-gray-400" />
            )}
          </div>
          {hasRealTimeData && validationData.format_validation?.errors && validationData.format_validation.errors.length > 0 && (
            <div className="mt-1 text-xs text-red-600">
              {validationData.format_validation.errors.length} error(s) found
            </div>
          )}
        </div>
        
        <div className={`p-3 rounded-lg border ${securityStyling.bg}`}>
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <Shield className={`h-4 w-4 ${securityStyling.icon}`} />
              <span className={`text-sm font-medium ${securityStyling.text}`}>Security Clear</span>
            </div>
            {securityStatus === 'failed' && (
              <XCircle className="h-4 w-4 text-red-500" />
            )}
            {securityStatus === 'passed' && (
              <CheckCircle className="h-4 w-4 text-green-500" />
            )}
            {securityStatus === 'pending' && (
              <Clock className="h-4 w-4 text-gray-400" />
            )}
          </div>
          {hasRealTimeData && validationData.security_scan?.issues && validationData.security_scan.issues.length > 0 && (
            <div className="mt-1 text-xs text-red-600">
              {validationData.security_scan.issues.length} issue(s) found
            </div>
          )}
        </div>
        
        <div className={`p-3 rounded-lg border ${privacyStyling.bg}`}>
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <UserCheck className={`h-4 w-4 ${privacyStyling.icon}`} />
              <span className={`text-sm font-medium ${privacyStyling.text}`}>Privacy Clear</span>
            </div>
            {privacyStatus === 'failed' && (
              <XCircle className="h-4 w-4 text-red-500" />
            )}
            {privacyStatus === 'passed' && (
              <CheckCircle className="h-4 w-4 text-green-500" />
            )}
            {privacyStatus === 'warning' && (
              <AlertTriangle className="h-4 w-4 text-yellow-500" />
            )}
            {privacyStatus === 'pending' && (
              <Clock className="h-4 w-4 text-gray-400" />
            )}
          </div>
          {hasRealTimeData && validationData.data_quality?.score && (
            <div className="mt-1 text-xs text-gray-600">
              Quality: {Math.round(validationData.data_quality.score * 100)}%
            </div>
          )}
        </div>
      </div>
      
      {/* Validation Error Details */}
      {hasRealTimeData && (
        <div className="space-y-2">
          {validationData.format_validation?.errors && validationData.format_validation.errors.map((error: string, index: number) => (
            <Alert key={index} variant="destructive" className="py-2">
              <AlertTriangle className="h-4 w-4" />
              <AlertDescription className="text-sm">
                <strong>Format Error:</strong> {error}
              </AlertDescription>
            </Alert>
          ))}
          {validationData.security_scan?.issues && validationData.security_scan.issues.map((issue: string, index: number) => (
            <Alert key={index} variant="destructive" className="py-2">
              <Shield className="h-4 w-4" />
              <AlertDescription className="text-sm">
                <strong>Security Issue:</strong> {issue}
              </AlertDescription>
            </Alert>
          ))}
        </div>
      )}
    </div>
  );
};