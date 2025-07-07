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
import { UploadFile } from '../CMDBImport.types';
import { getStatusStyling } from '../utils/statusUtils';

interface CMDBValidationPanelProps {
  file: UploadFile;
  onValidationUpdate: (validationData: any) => void;
}

export const CMDBValidationPanel: React.FC<CMDBValidationPanelProps> = ({ 
  file, 
  onValidationUpdate 
}) => {
  // Progress calculation from file state only
  const agentsCompleted = file.agents_completed || 0;
  const totalAgents = file.total_agents || 4;
  const validationProgress = Math.round((agentsCompleted / totalAgents) * 100);
  
  // Status determination from file state only
  const formatStatus = file.format_validation ? 'passed' : 'pending';
  const securityStatus = file.security_clearance ? 'passed' : 'pending';
  const privacyStatus = file.privacy_clearance ? 'passed' : 'pending';
  
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
      </div>

      {/* Security Clearances */}
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
        </div>
      </div>
    </div>
  );
};