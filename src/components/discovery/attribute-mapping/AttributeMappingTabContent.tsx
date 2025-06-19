import React from 'react';
import FieldMappingsTab from './FieldMappingsTab';
import CriticalAttributesTab from './CriticalAttributesTab';
import ImportedDataTab from './ImportedDataTab';

interface AttributeMappingTabContentProps {
  activeTab: 'mappings' | 'data' | 'critical';
  fieldMappings: any[];
  criticalAttributes: any[];
  agenticData: any;
  onApproveMapping: (mappingId: string) => void;
  onRejectMapping: (mappingId: string) => void;
  refetchAgentic: () => void;
}

const AttributeMappingTabContent: React.FC<AttributeMappingTabContentProps> = ({
  activeTab,
  fieldMappings,
  criticalAttributes,
  agenticData,
  onApproveMapping,
  onRejectMapping,
  refetchAgentic
}) => {
  const renderTabContent = () => {
    switch (activeTab) {
      case 'mappings':
        return (
          <FieldMappingsTab
            fieldMappings={fieldMappings}
            onApproveMapping={onApproveMapping}
            onRejectMapping={onRejectMapping}
            isLoading={false}
          />
        );
      case 'critical':
        return (
          <CriticalAttributesTab
            criticalAttributes={criticalAttributes}
            onRefreshCriticalData={refetchAgentic}
            isLoading={false}
          />
        );
      case 'data':
        return (
          <ImportedDataTab
            rawData={agenticData?.raw_data || []}
            isLoading={false}
          />
        );
      default:
        return (
          <CriticalAttributesTab
            criticalAttributes={criticalAttributes}
            onRefreshCriticalData={refetchAgentic}
            isLoading={false}
          />
        );
    }
  };

  return <>{renderTabContent()}</>;
};

export default AttributeMappingTabContent; 