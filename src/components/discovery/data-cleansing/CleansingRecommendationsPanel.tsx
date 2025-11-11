import React from 'react';
import { Button } from '../../ui/button';
import { Brain } from 'lucide-react';

interface CleansingRecommendation {
  id: string;
  category?: string; // 'standardization' | 'validation' | 'enrichment' | 'deduplication'
  type?: string; // Legacy field for backward compatibility
  title: string;
  description: string;
  confidence?: number; // Optional, may not be provided by backend
  priority: 'high' | 'medium' | 'low';
  fields_affected?: string[]; // Backend field name
  fields?: string[]; // Legacy field for backward compatibility
  agent_source?: string; // Optional, may not be provided by backend
  implementation_steps?: string[]; // Optional, may not be provided by backend
  status?: 'pending' | 'applied' | 'rejected'; // Optional, defaults to 'pending'
}

interface CleansingRecommendationsPanelProps {
  recommendations: CleansingRecommendation[];
  onApplyRecommendation: (recommendationId: string, action: 'apply' | 'reject') => void;
  isLoading?: boolean;
}

const CleansingRecommendationsPanel: React.FC<CleansingRecommendationsPanelProps> = ({
  recommendations,
  onApplyRecommendation,
  isLoading = false
}) => {
  const getPriorityBadgeClass = (priority: 'high' | 'medium' | 'low'): unknown => {
    switch (priority) {
      case 'high':
        return 'bg-red-100 text-red-800';
      case 'medium':
        return 'bg-yellow-100 text-yellow-800';
      case 'low':
        return 'bg-green-100 text-green-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  if (isLoading) {
    return (
      <div className="bg-white rounded-lg shadow-md">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-medium text-gray-900">Cleansing Recommendations</h3>
          <div className="h-4 bg-gray-200 rounded w-72 mt-1"></div>
        </div>
        <div className="p-6">
          <div className="space-y-4">
            {Array.from({ length: 2 }).map((_, i) => (
              <div key={i} className="border border-gray-200 rounded-lg p-4 animate-pulse">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-2 mb-2">
                      <div className="h-5 bg-gray-200 rounded w-16"></div>
                      <div className="h-4 bg-gray-200 rounded w-32"></div>
                      <div className="h-3 bg-gray-200 rounded w-20"></div>
                    </div>
                    <div className="h-4 bg-gray-200 rounded w-full mb-2"></div>
                    <div className="h-3 bg-gray-200 rounded w-3/4 mb-2"></div>
                    <div className="space-y-1">
                      <div className="h-3 bg-gray-200 rounded w-1/2"></div>
                      <div className="h-3 bg-gray-200 rounded w-2/3"></div>
                    </div>
                  </div>
                  <div className="flex space-x-2 ml-4">
                    <div className="h-8 bg-gray-200 rounded w-16"></div>
                    <div className="h-8 bg-gray-200 rounded w-16"></div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-md">
      <div className="px-6 py-4 border-b border-gray-200">
        <h3 className="text-lg font-medium text-gray-900">Cleansing Recommendations</h3>
        <p className="text-sm text-gray-600">
          {recommendations.length} improvement recommendations from the Data Standardization Specialist
        </p>
      </div>
      <div className="p-6">
        {recommendations.length === 0 ? (
          <div className="text-center py-8">
            <Brain className="h-12 w-12 text-blue-600 mx-auto mb-4" />
            <p className="text-gray-600">No recommendations yet. Trigger analysis to get AI-powered suggestions.</p>
          </div>
        ) : (
          <div className="space-y-4">
            {recommendations.map((rec) => (
              <div key={rec.id} className="border border-gray-200 rounded-lg p-4">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-2 mb-2">
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getPriorityBadgeClass(rec.priority)}`}>
                        {rec.priority.toUpperCase()}
                      </span>
                      <span className="text-sm font-medium text-gray-900">{rec.title}</span>
                      <span className="text-xs text-gray-500">
                        ({rec.confidence !== undefined && rec.confidence !== null
                          ? `${Math.round(rec.confidence * 100)}%`
                          : 'N/A'} confidence)
                      </span>
                    </div>
                    <p className="text-sm text-gray-700 mb-2">{rec.description}</p>
                    <div className="text-xs text-gray-600">
                      <p><strong>Fields:</strong> {(rec.fields_affected || rec.fields || []).join(', ') || 'N/A'}</p>
                      {rec.implementation_steps && rec.implementation_steps.length > 0 && (
                        <>
                          <p><strong>Steps:</strong></p>
                          <ul className="list-disc list-inside ml-2 space-y-1">
                            {rec.implementation_steps.map((step, idx) => (
                              <li key={idx}>{step}</li>
                            ))}
                          </ul>
                        </>
                      )}
                    </div>
                    {rec.agent_source && (
                      <p className="text-xs text-blue-600 mt-1">Source: {rec.agent_source}</p>
                    )}
                  </div>
                  <div className="flex space-x-2 ml-4">
                    <Button
                      size="sm"
                      onClick={() => onApplyRecommendation(rec.id, 'apply')}
                      disabled={rec.status === 'applied' || rec.status === 'rejected'}
                      className={rec.status === 'applied' ? 'bg-green-600 hover:bg-green-700' : ''}
                    >
                      {rec.status === 'applied' ? 'Applied' : 'Apply'}
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => onApplyRecommendation(rec.id, 'reject')}
                      disabled={rec.status === 'applied' || rec.status === 'rejected'}
                      className={rec.status === 'rejected' ? 'border-red-300 text-red-700 bg-red-50' : ''}
                    >
                      {rec.status === 'rejected' ? 'Rejected' : 'Reject'}
                    </Button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default CleansingRecommendationsPanel;
