import React from 'react';
import FieldMappingsTab from './FieldMappingsTab/index';
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
  refetchCriticalAttributes?: () => void;
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
  refetchCriticalAttributes,
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
              onRefresh={refetchAgentic}
            />
          </FieldMappingErrorBoundary>
        );
      case 'critical':
        return (
          <CriticalAttributesTab
            fieldMappings={fieldMappings}
            onMappingAction={(mappingId: string, action: 'approve' | 'reject', rejectionReason?: string) => {
              if (action === 'approve') {
                onApproveMapping(mappingId);
              } else {
                onRejectMapping(mappingId, rejectionReason);
              }
            }}
            onMappingChange={onMappingChange}
            onRefresh={refetchAgentic}
            isLoading={isLoading}
            isAnalyzing={false}
          />
        );
      case 'data':
        return (
          <ImportedDataTab sessionInfo={sessionInfo} />
        );
      default:
        return (
          <CriticalAttributesTab
            fieldMappings={fieldMappings}
            onMappingAction={(mappingId: string, action: 'approve' | 'reject', rejectionReason?: string) => {
              if (action === 'approve') {
                onApproveMapping(mappingId);
              } else {
                onRejectMapping(mappingId, rejectionReason);
              }
            }}
            onMappingChange={onMappingChange}
            onRefresh={refetchAgentic}
            isLoading={isLoading}
            isAnalyzing={false}
          />
        );
    }
  };

  return <>{renderTabContent()}</>;
};

export default AttributeMappingTabContent; 