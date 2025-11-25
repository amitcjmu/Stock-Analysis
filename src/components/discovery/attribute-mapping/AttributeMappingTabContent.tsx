import React from 'react';
import FieldMappingsTab from './FieldMappingsTab/index';
import CriticalAttributesTab from './CriticalAttributesTab';
import ImportedDataTab from './ImportedDataTab';
import { FieldMappingErrorBoundary } from './FieldMappingErrorBoundary';
import type { FieldMapping } from '../../../types/api/discovery/field-mapping-types';
import type { CriticalAttribute } from '../../../types/hooks/discovery/attribute-mapping-hooks';
import type {
  AgenticData,
  SessionInfo
} from '../../../pages/discovery/AttributeMapping/types';
import type {
  FieldMappingLearningApprovalRequest,
  FieldMappingLearningRejectionRequest,
  BulkFieldMappingLearningRequest
} from '../../../services/api/discoveryFlowService';

interface AttributeMappingTabContentProps {
  activeTab: 'mappings' | 'data' | 'critical';
  fieldMappings: FieldMapping[];
  criticalAttributes: CriticalAttribute[];
  agenticData: AgenticData | null;
  onApproveMapping: (mappingId: string) => void;
  onRejectMapping: (mappingId: string, rejectionReason?: string) => void;
  onRemoveMapping?: (mappingId: string) => Promise<void>;
  onMappingChange?: (mappingId: string, newTarget: string) => void;
  refetchAgentic?: () => void;
  refetchCriticalAttributes?: () => void;
  onAttributeUpdate?: (attributeName: string, updates: Partial<CriticalAttribute>) => void;
  isLoading?: boolean;
  sessionInfo?: SessionInfo;
  // New learning-related props
  onApproveMappingWithLearning?: (mappingId: string, request: FieldMappingLearningApprovalRequest) => Promise<void>;
  onRejectMappingWithLearning?: (mappingId: string, request: FieldMappingLearningRejectionRequest) => Promise<void>;
  onBulkLearnMappings?: (request: BulkFieldMappingLearningRequest) => Promise<void>;
  learnedMappings?: Set<string>;
  clientAccountId?: string;
  engagementId?: string;
  flowId?: string | null;
  importCategory?: string;
  canContinueToDataCleansing?: boolean;
  onContinueToDataCleansing?: () => void;
}

const AttributeMappingTabContent: React.FC<AttributeMappingTabContentProps> = ({
  activeTab,
  fieldMappings,
  criticalAttributes,
  agenticData,
  onApproveMapping,
  onRejectMapping,
  onRemoveMapping,
  onMappingChange,
  refetchAgentic,
  refetchCriticalAttributes,
  onAttributeUpdate,
  isLoading = false,
  sessionInfo,
  onApproveMappingWithLearning,
  onRejectMappingWithLearning,
  onBulkLearnMappings,
  learnedMappings,
  clientAccountId,
  engagementId,
  flowId,
  importCategory,
  engagementId,
  canContinueToDataCleansing,
  onContinueToDataCleansing
}) => {
  const renderTabContent = (): JSX.Element => {
    switch (activeTab) {
      case 'mappings':
        return (
          <FieldMappingErrorBoundary>
            <FieldMappingsTab
              fieldMappings={fieldMappings}
              isAnalyzing={false}
              flowId={flowId || sessionInfo?.flowId}
              importCategory={importCategory || sessionInfo?.importCategory || null}
              onMappingAction={(mappingId: string, action: 'approve' | 'reject', rejectionReason?: string) => {
                if (action === 'approve') {
                  onApproveMapping(mappingId);
                } else {
                  onRejectMapping(mappingId, rejectionReason);
                }
              }}
              onRemoveMapping={onRemoveMapping}
              onMappingChange={onMappingChange}
              onRefresh={refetchAgentic}
              // New learning-related props
              onApproveMappingWithLearning={onApproveMappingWithLearning}
              onRejectMappingWithLearning={onRejectMappingWithLearning}
              onBulkLearnMappings={onBulkLearnMappings}
              learnedMappings={learnedMappings}
              clientAccountId={clientAccountId}
              engagementId={engagementId}
              sessionInfo={sessionInfo}
              // Continue to data cleansing props
              canContinueToDataCleansing={canContinueToDataCleansing}
              onContinueToDataCleansing={onContinueToDataCleansing}
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
            flowId={flowId}
            importCategory={importCategory}
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
            flowId={flowId}
            importCategory={importCategory}
          />
        );
    }
  };

  return <>{renderTabContent()}</>;
};

export default AttributeMappingTabContent;
