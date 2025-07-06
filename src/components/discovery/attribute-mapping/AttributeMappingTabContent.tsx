import React from 'react';
import FieldMappingsTab from './FieldMappingsTab';
import CriticalAttributesTab from './CriticalAttributesTab';
import ImportedDataTab from './ImportedDataTab';
import { FieldMappingErrorBoundary } from './FieldMappingErrorBoundary';

interface AttributeMappingTabContentProps {
  activeTab: 'mappings' | 'data' | 'critical';
  fieldMappings: any[];
  criticalAttributes: any[];
  agenticData: any;
  onApproveMapping: (mappingId: string) => void;
  onRejectMapping: (mappingId: string, rejectionReason?: string) => void;
  onMappingChange?: (mappingId: string, newTarget: string) => void;
  refetchAgentic?: () => void;
  onAttributeUpdate?: (attributeName: string, updates: Partial<any>) => void;
  isLoading?: boolean;
  sessionInfo?: {
    flowId: string | null;
    availableDataImports: any[];
    selectedDataImportId: string | null;
    hasMultipleSessions: boolean;
  };
}

const AttributeMappingTabContent: React.FC<AttributeMappingTabContentProps> = ({
  activeTab,
  fieldMappings,
  criticalAttributes,
  agenticData,
  onApproveMapping,
  onRejectMapping,
  onMappingChange,
  refetchAgentic,
  onAttributeUpdate,
  isLoading = false,
  sessionInfo
}) => {
  const renderTabContent = () => {
    switch (activeTab) {
      case 'mappings':
        return (
          <FieldMappingErrorBoundary>
            <FieldMappingsTab
              fieldMappings={fieldMappings}
              isAnalyzing={false}
              onMappingAction={(mappingId: string, action: 'approve' | 'reject', rejectionReason?: string) => {
                if (action === 'approve') {
                  onApproveMapping(mappingId);
                } else {
                  onRejectMapping(mappingId, rejectionReason);
                }
              }}
            onMappingChange={onMappingChange}
          />
          </FieldMappingErrorBoundary>
        );
      case 'critical':
        return (
          <CriticalAttributesTab
            criticalAttributes={criticalAttributes}
            onRefreshCriticalData={refetchAgentic}
            onAttributeUpdate={onAttributeUpdate}
            isLoading={false}
            fieldMappings={fieldMappings}
            sessionInfo={sessionInfo}
          />
        );
      case 'data':
        return (
          <ImportedDataTab sessionInfo={sessionInfo} />
        );
      default:
        return (
          <CriticalAttributesTab
            criticalAttributes={criticalAttributes}
            onRefreshCriticalData={refetchAgentic}
            onAttributeUpdate={onAttributeUpdate}
            isLoading={false}
            fieldMappings={fieldMappings}
            sessionInfo={sessionInfo}
          />
        );
    }
  };

  return <>{renderTabContent()}</>;
};

export default AttributeMappingTabContent; 