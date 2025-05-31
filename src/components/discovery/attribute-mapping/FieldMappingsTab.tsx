import React from 'react';
import { ArrowRight, CheckCircle, X, RefreshCw } from 'lucide-react';

interface FieldMapping {
  id: string;
  sourceField: string;
  targetAttribute: string;
  confidence: number;
  mapping_type: 'direct' | 'calculated' | 'manual';
  sample_values: string[];
  status: 'pending' | 'approved' | 'rejected' | 'ignored' | 'deleted';
  ai_reasoning: string;
  action?: 'ignore' | 'delete';
}

interface FieldMappingsTabProps {
  fieldMappings: FieldMapping[];
  isAnalyzing: boolean;
  onMappingAction: (mappingId: string, action: 'approve' | 'reject') => void;
}

const FieldMappingsTab: React.FC<FieldMappingsTabProps> = ({
  fieldMappings,
  isAnalyzing,
  onMappingAction
}) => {
  return (
    <div className="bg-white rounded-lg shadow-md p-6 mb-8">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-semibold text-gray-900">Field Mapping Suggestions</h2>
        {isAnalyzing && (
          <div className="flex items-center space-x-2 text-blue-600">
            <RefreshCw className="h-4 w-4 animate-spin" />
            <span className="text-sm">AI analyzing...</span>
          </div>
        )}
      </div>
      
      <div className="space-y-4">
        {fieldMappings.map((mapping) => (
          <div key={mapping.id} className={`border rounded-lg p-4 ${
            mapping.status === 'approved' ? 'bg-green-50 border-green-200' :
            mapping.status === 'rejected' ? 'bg-red-50 border-red-200' :
            'bg-white border-gray-200'
          }`}>
            <div className="flex items-center justify-between">
              <div className="flex-1">
                <div className="flex items-center space-x-4 mb-2">
                  <h4 className="font-medium text-gray-900">{mapping.sourceField}</h4>
                  <ArrowRight className="h-4 w-4 text-gray-400" />
                  <span className="font-medium text-blue-600">{mapping.targetAttribute}</span>
                  <span className={`px-2 py-1 text-xs rounded-full ${
                    mapping.confidence >= 0.8 ? 'bg-green-100 text-green-800' :
                    mapping.confidence >= 0.6 ? 'bg-yellow-100 text-yellow-800' :
                    'bg-red-100 text-red-800'
                  }`}>
                    {Math.round(mapping.confidence * 100)}% confidence
                  </span>
                </div>
                <p className="text-sm text-gray-600 mb-2">{mapping.ai_reasoning}</p>
                <div className="text-xs text-gray-500">
                  <strong>Sample values:</strong> {mapping.sample_values.join(', ')}
                </div>
              </div>
              
              <div className="flex items-center space-x-2 ml-4">
                {mapping.status === 'pending' && (
                  <>
                    <button
                      onClick={() => onMappingAction(mapping.id, 'approve')}
                      className="px-3 py-1 bg-green-600 text-white text-sm rounded-lg hover:bg-green-700"
                    >
                      Approve
                    </button>
                    <button
                      onClick={() => onMappingAction(mapping.id, 'reject')}
                      className="px-3 py-1 bg-red-600 text-white text-sm rounded-lg hover:bg-red-700"
                    >
                      Reject
                    </button>
                  </>
                )}
                {mapping.status === 'approved' && (
                  <CheckCircle className="h-5 w-5 text-green-600" />
                )}
                {mapping.status === 'rejected' && (
                  <X className="h-5 w-5 text-red-600" />
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default FieldMappingsTab; 