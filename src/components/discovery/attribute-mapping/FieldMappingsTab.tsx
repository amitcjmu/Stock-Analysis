import React from 'react';
import { FieldMappingsTab } from './field-mappings';
import type { FieldMappingsTabProps } from './field-mappings/types';

// Main FieldMappingsTab component that uses the modular field mappings system
const MainFieldMappingsTab: React.FC<FieldMappingsTabProps> = (props) => {
  return <FieldMappingsTab {...props} />;
};

export default MainFieldMappingsTab; 