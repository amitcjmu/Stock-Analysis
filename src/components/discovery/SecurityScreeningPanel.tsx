import React from 'react'
import { useState } from 'react'
import { useEffect } from 'react'
import { Info } from 'lucide-react'
import { Shield, AlertTriangle, CheckCircle, Eye, EyeOff, Lock } from 'lucide-react'
import { useAuth } from '../../contexts/AuthContext';
import { API_CONFIG } from '../../config/api';

interface SecurityScreeningPanelProps {
  dataImportId?: string;
  flowId?: string;
  refreshTrigger?: number;
}

interface SecurityScreeningData {
  file_validation: {
    confidence: number;
    issues: string[];
    warnings: string[];
    file_size_mb: number;
    row_count: number;
    column_count: number;
  };
  pii_detection: {
    confidence: number;
    detected_pii: Record<string, Record<string, number>>;
    high_risk_columns: string[];
    medium_risk_columns: string[];
    total_pii_records: number;
  };
  security_assessment: {
    confidence: number;
    security_risks: Record<string, Record<string, string | number | boolean | null>>;
    risk_level: 'low' | 'medium' | 'high';
    flagged_columns: string[];
  };
  compliance_check: {
    confidence: number;
    gdpr_compliance: boolean;
    hipaa_compliance: boolean;
    pci_compliance: boolean;
    issues: string[];
  };
  data_quality: {
    confidence: number;
    quality_score: number;
    issues: string[];
    warnings: string[];
  };
}

const SecurityScreeningPanel: React.FC<SecurityScreeningPanelProps> = ({
  dataImportId,
  flowId,
  refreshTrigger = 0
}) => {
  const { getAuthHeaders } = useAuth();
  const [screeningData, setScreeningData] = useState<SecurityScreeningData | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showDetails, setShowDetails] = useState(false);

  useEffect(() => {
    if (dataImportId || flowId) {
      fetchSecurityScreening();
    }
  }, [dataImportId, flowId, refreshTrigger]);

  const fetchSecurityScreening = async (): Promise<any> => {
    try {
      setIsLoading(true);
      setError(null);

      const authHeaders = getAuthHeaders();
      let endpoint = '';

      if (flowId) {
        endpoint = `${API_CONFIG.BASE_URL}/discovery/flow/${flowId}/security-screening`;
      } else if (dataImportId) {
        endpoint = `${API_CONFIG.BASE_URL}/data-import/${dataImportId}/security-screening`;
      } else {
        throw new Error('No flow ID or data import ID provided');
      }

      const response = await fetch(endpoint, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          ...authHeaders
        }
      });

      if (!response.ok) {
        if (response.status === 404) {
          setScreeningData(null);
          return;
        }
        throw new Error(`Failed to fetch security screening: ${response.statusText}`);
      }

      const data = await response.json();
      setScreeningData(data.data_validation_results || data);
    } catch (err) {
      console.error('Failed to fetch security screening:', err);
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setIsLoading(false);
    }
  };

  const getRiskLevelColor = (level: string): unknown => {
    switch (level) {
      case 'low': return 'text-green-600 bg-green-100';
      case 'medium': return 'text-yellow-600 bg-yellow-100';
      case 'high': return 'text-red-600 bg-red-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const getConfidenceColor = (confidence: number): unknown => {
    if (confidence >= 90) return 'text-green-600 bg-green-100';
    if (confidence >= 70) return 'text-yellow-600 bg-yellow-100';
    return 'text-red-600 bg-red-100';
  };

  if (isLoading) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="flex items-center space-x-3 mb-4">
          <Shield className="h-5 w-5 text-blue-600" />
          <h3 className="text-lg font-semibold">Security Screening</h3>
        </div>
        <div className="animate-pulse space-y-3">
          <div className="h-4 bg-gray-200 rounded w-3/4"></div>
          <div className="h-4 bg-gray-200 rounded w-1/2"></div>
          <div className="h-4 bg-gray-200 rounded w-5/6"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="flex items-center space-x-3 mb-4">
          <Shield className="h-5 w-5 text-red-600" />
          <h3 className="text-lg font-semibold">Security Screening</h3>
        </div>
        <div className="text-red-600 text-sm">{error}</div>
      </div>
    );
  }

  if (!screeningData) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="flex items-center space-x-3 mb-4">
          <Shield className="h-5 w-5 text-gray-600" />
          <h3 className="text-lg font-semibold">Security Screening</h3>
        </div>
        <div className="text-gray-500 text-sm">No security screening data available yet.</div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-3">
          <Shield className="h-5 w-5 text-blue-600" />
          <h3 className="text-lg font-semibold">Security Screening</h3>
        </div>
        <button
          onClick={() => setShowDetails(!showDetails)}
          className="flex items-center space-x-2 text-sm text-gray-600 hover:text-gray-800"
        >
          {showDetails ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
          <span>{showDetails ? 'Hide Details' : 'Show Details'}</span>
        </button>
      </div>

      {/* Overall Security Status */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <div className="border rounded-lg p-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-gray-700">Overall Risk</span>
            <span className={`px-2 py-1 rounded-full text-xs font-medium ${getRiskLevelColor(screeningData.security_assessment.risk_level)}`}>
              {screeningData.security_assessment.risk_level.toUpperCase()}
            </span>
          </div>
          <div className="text-xs text-gray-500">
            {screeningData.security_assessment.flagged_columns.length} security flags detected
          </div>
        </div>

        <div className="border rounded-lg p-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-gray-700">PII Detection</span>
            <span className={`px-2 py-1 rounded-full text-xs font-medium ${getConfidenceColor(screeningData.pii_detection.confidence)}`}>
              {Math.round(screeningData.pii_detection.confidence)}%
            </span>
          </div>
          <div className="text-xs text-gray-500">
            {screeningData.pii_detection.high_risk_columns.length + screeningData.pii_detection.medium_risk_columns.length} PII columns found
          </div>
        </div>

        <div className="border rounded-lg p-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-gray-700">Data Quality</span>
            <span className={`px-2 py-1 rounded-full text-xs font-medium ${getConfidenceColor(screeningData.data_quality.confidence)}`}>
              {Math.round(screeningData.data_quality.quality_score || screeningData.data_quality.confidence)}%
            </span>
          </div>
          <div className="text-xs text-gray-500">
            {screeningData.data_quality.issues.length} quality issues found
          </div>
        </div>
      </div>

      {/* PII Detection Summary */}
      {(screeningData.pii_detection.high_risk_columns.length > 0 || screeningData.pii_detection.medium_risk_columns.length > 0) && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-4">
          <div className="flex items-center space-x-2 mb-2">
            <AlertTriangle className="h-4 w-4 text-yellow-600" />
            <span className="font-medium text-yellow-800">PII Data Detected</span>
          </div>
          <div className="text-sm text-yellow-700">
            {screeningData.pii_detection.high_risk_columns.length > 0 && (
              <div className="mb-1">
                <strong>High Risk:</strong> {screeningData.pii_detection.high_risk_columns.join(', ')}
              </div>
            )}
            {screeningData.pii_detection.medium_risk_columns.length > 0 && (
              <div>
                <strong>Medium Risk:</strong> {screeningData.pii_detection.medium_risk_columns.join(', ')}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Compliance Status */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
        <div className="flex items-center space-x-2">
          {screeningData.compliance_check.gdpr_compliance ? (
            <CheckCircle className="h-4 w-4 text-green-600" />
          ) : (
            <AlertTriangle className="h-4 w-4 text-red-600" />
          )}
          <span className="text-sm">GDPR Compliant</span>
        </div>
        <div className="flex items-center space-x-2">
          {screeningData.compliance_check.hipaa_compliance ? (
            <CheckCircle className="h-4 w-4 text-green-600" />
          ) : (
            <AlertTriangle className="h-4 w-4 text-red-600" />
          )}
          <span className="text-sm">HIPAA Compliant</span>
        </div>
        <div className="flex items-center space-x-2">
          {screeningData.compliance_check.pci_compliance ? (
            <CheckCircle className="h-4 w-4 text-green-600" />
          ) : (
            <AlertTriangle className="h-4 w-4 text-red-600" />
          )}
          <span className="text-sm">PCI Compliant</span>
        </div>
      </div>

      {/* Detailed Information */}
      {showDetails && (
        <div className="space-y-4 border-t pt-4">
          {/* File Validation Details */}
          <div>
            <h4 className="font-medium text-gray-900 mb-2">File Validation</h4>
            <div className="text-sm text-gray-600 space-y-1">
              <div>Records: {screeningData.file_validation.row_count}</div>
              <div>Columns: {screeningData.file_validation.column_count}</div>
              <div>File Size: {screeningData.file_validation.file_size_mb} MB</div>
              {screeningData.file_validation.issues.length > 0 && (
                <div className="text-red-600">
                  Issues: {screeningData.file_validation.issues.join(', ')}
                </div>
              )}
              {screeningData.file_validation.warnings.length > 0 && (
                <div className="text-yellow-600">
                  Warnings: {screeningData.file_validation.warnings.join(', ')}
                </div>
              )}
            </div>
          </div>

          {/* Security Risks Details */}
          {Object.keys(screeningData.security_assessment.security_risks).length > 0 && (
            <div>
              <h4 className="font-medium text-gray-900 mb-2">Security Risks</h4>
              <div className="text-sm text-gray-600 space-y-1">
                {Object.entries(screeningData.security_assessment.security_risks).map(([column, risks]) => (
                  <div key={column} className="flex items-center space-x-2">
                    <Lock className="h-3 w-3 text-red-500" />
                    <span><strong>{column}:</strong> {Object.keys(risks).join(', ')}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* PII Details */}
          {Object.keys(screeningData.pii_detection.detected_pii).length > 0 && (
            <div>
              <h4 className="font-medium text-gray-900 mb-2">PII Detection Details</h4>
              <div className="text-sm text-gray-600 space-y-1">
                {Object.entries(screeningData.pii_detection.detected_pii).map(([column, piiTypes]) => (
                  <div key={column} className="flex items-center space-x-2">
                    <Info className="h-3 w-3 text-yellow-500" />
                    <span><strong>{column}:</strong> {Object.entries(piiTypes).map(([type, count]) => `${type} (${count})`).join(', ')}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default SecurityScreeningPanel;
