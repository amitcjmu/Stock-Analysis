import React from 'react';
import FieldMappingsTab from './FieldMappingsTab/index';
import CriticalAttributesTab from './CriticalAttributesTab';
import ImportedDataTab from './ImportedDataTab';
import { FieldMappingErrorBoundary } from './FieldMappingErrorBoundary';
import type {
  FieldMapping,
  CriticalAttribute
} from '../../../types/hooks/discovery/attribute-mapping-hooks';
import type {
  AgenticData,
  SessionInfo
} from '../../../pages/discovery/AttributeMapping/types';

interface AttributeMappingTabContentProps {
  activeTab: 'mappings' | 'data' | 'critical';
  fieldMappings: FieldMapping[];
  criticalAttributes: CriticalAttribute[];
  agenticData: AgenticData | null;
  onApproveMapping: (mappingId: string) => void;
  onRejectMapping: (mappingId: string, rejectionReason?: string) => void;
  onMappingChange?: (mappingId: string, newTarget: string) => void;
  refetchAgentic?: () => void;
  refetchCriticalAttributes?: () => void;
  onAttributeUpdate?: (attributeName: string, updates: Partial<CriticalAttribute>) => void;
  isLoading?: boolean;
  sessionInfo?: SessionInfo;
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
  const renderTabContent = (): JSX.Element => {
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
