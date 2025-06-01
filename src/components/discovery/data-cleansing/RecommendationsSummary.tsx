import React from 'react';
import { Zap } from 'lucide-react';

export interface AgentRecommendation {
  id: string;
  operation: string;
  title: string;
  description: string;
  examples: string[];
  affected_assets: number;
  confidence: number;
  priority: 'high' | 'medium' | 'low';
  estimated_improvement: number;
  change_details: {
    operation_type: string;
    fields_affected: string[];
    sample_changes: string[];
  };
}

interface RecommendationsSummaryProps {
  agentRecommendations: AgentRecommendation[];
  selectedRecommendation: string | null;
  onRecommendationSelect: (recommendationId: string | null) => void;
  onApplyRecommendation: (recommendationId: string) => void;
}

const RecommendationsSummary: React.FC<RecommendationsSummaryProps> = ({
  agentRecommendations,
  selectedRecommendation,
  onRecommendationSelect,
  onApplyRecommendation
}) => {
  return (
    <div className="bg-white rounded-lg shadow-md">
      <div className="p-4 border-b border-gray-200">
        <h3 className="text-lg font-semibold text-gray-900 flex items-center">
          <Zap className="h-5 w-5 text-blue-500 mr-2" />
          Agent Recommendations ({agentRecommendations.length})
        </h3>
      </div>
      <div className="max-h-64 overflow-y-auto">
        {agentRecommendations.length > 0 ? (
          <div className="space-y-2 p-4">
            {agentRecommendations.map((rec) => (
              <div
                key={rec.id}
                onClick={() => onRecommendationSelect(selectedRecommendation === rec.id ? null : rec.id)}
                className={`p-3 rounded-lg border cursor-pointer transition-colors ${
                  selectedRecommendation === rec.id
                    ? 'border-blue-300 bg-blue-50'
                    : 'border-gray-200 hover:border-blue-200 hover:bg-blue-25'
                }`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <p className="text-sm font-medium text-gray-900">{rec.title}</p>
                    <p className="text-xs text-gray-600">{rec.affected_assets} assets</p>
                    <p className="text-xs text-gray-500">{rec.change_details.fields_affected.join(', ')}</p>
                  </div>
                  <span className={`text-xs px-2 py-1 rounded-full ${
                    rec.priority === 'high' ? 'bg-red-100 text-red-800' :
                    rec.priority === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                    'bg-green-100 text-green-800'
                  }`}>
                    {rec.priority}
                  </span>
                </div>
                {selectedRecommendation === rec.id && (
                  <div className="mt-2 pt-2 border-t border-blue-200">
                    <p className="text-xs text-gray-600 mb-2">{rec.description}</p>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onApplyRecommendation(rec.id);
                      }}
                      className="text-xs bg-blue-600 text-white px-2 py-1 rounded hover:bg-blue-700"
                    >
                      Apply Recommendation
                    </button>
                  </div>
                )}
              </div>
            ))}
          </div>
        ) : (
          <div className="p-4 text-center text-gray-500">
            <p className="text-sm">No recommendations available</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default RecommendationsSummary; 