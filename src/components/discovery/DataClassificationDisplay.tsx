import React from 'react'
import { useState } from 'react'
import { useEffect } from 'react'
import { CheckCircle, XCircle, Eye, Brain, ChevronDown, ChevronUp, FileText, RefreshCw, ThumbsUp, ThumbsDown, Edit3 } from 'lucide-react'
import { AlertTriangle, Loader2, BarChart3 } from 'lucide-react'
import { API_CONFIG } from '../../config/api'
import { apiCall } from '../../config/api'
import { useAuth } from '@/contexts/AuthContext';

interface DataItem {
  id: string;
  data_type: string;
  classification: 'good_data' | 'needs_clarification' | 'unusable';
  content: unknown;
  agent_analysis: unknown;
  confidence: 'high' | 'medium' | 'low' | 'uncertain';
  issues: string[];
  recommendations: string[];
  page: string;
}

interface DataClassificationDisplayProps {
  pageContext: string;
  onClassificationUpdate?: (itemId: string, newClassification: string) => void;
  className?: string;
  refreshTrigger?: number; // Increment this to trigger a refresh
  isProcessing?: boolean; // Set to true when background processing is happening
}

const DataClassificationDisplay: React.FC<DataClassificationDisplayProps> = ({
  pageContext,
  onClassificationUpdate,
  className = "",
  refreshTrigger,
  isProcessing = false
}) => {
  const { session } = useAuth();

  const [classifications, setClassifications] = useState<{
    good_data: DataItem[];
    needs_clarification: DataItem[];
    unusable: DataItem[];
  }>({
    good_data: [],
    needs_clarification: [],
    unusable: []
  });
  const [isLoading, setIsLoading] = useState(true);
  const [expandedItems, setExpandedItems] = useState<Set<string>>(new Set());
  const [selectedTab, setSelectedTab] = useState<'good_data' | 'needs_clarification' | 'unusable'>('good_data');
  const [error, setError] = useState<string | null>(null);

  // Memoize the fetch function to prevent unnecessary re-renders
  const fetchClassifications = React.useCallback(async () => {
    if (!pageContext) return;

    setIsLoading(true);
    setError(null);

    try {
      const result = await apiCall(`/api/v1/agents/discovery/data-classifications?page=${pageContext}`);

      // Process the result
      if (result.success && result.classifications) {
        setClassifications({
          good_data: result.classifications.good_data || [],
          needs_clarification: result.classifications.needs_clarification || [],
          unusable: result.classifications.unusable || []
        });
      }
    } catch (err: unknown) {
      // Handle 404 errors gracefully - these endpoints may not exist yet
      if (err.status === 404 || err.response?.status === 404) {
        console.log('Data classifications endpoint not available yet');
        setClassifications({
          good_data: [],
          needs_clarification: [],
          unusable: []
        });
        setError(null);
      } else {
        console.error('Error fetching data classifications:', err);
        setError(err instanceof Error ? err.message : 'Failed to fetch data classifications');
      }
    } finally {
      setIsLoading(false);
    }
  }, [pageContext, session?.id]);

  // Initial fetch and refresh when dependencies change
  useEffect(() => {
    fetchClassifications();
  }, [fetchClassifications]);

  // Set up polling only when processing is active
  useEffect(() => {
    if (!isProcessing) return;

    const interval = setInterval(fetchClassifications, 30000); // Poll every 30 seconds when processing
    return () => clearInterval(interval);
  }, [isProcessing, fetchClassifications]);

  // Handle refresh trigger
  useEffect(() => {
    if (refreshTrigger === undefined) return;
    fetchClassifications();
  }, [refreshTrigger, fetchClassifications]);

  const updateClassification = async (itemId: string, newClassification: 'good_data' | 'needs_clarification' | 'unusable') => {
    try {
      const result = await apiCall('/api/v1/agents/discovery/learning/agent-learning', {
        method: 'POST',
        body: JSON.stringify({
          learning_type: 'data_classification',
          original_prediction: { item_id: itemId },
          user_correction: { classification: newClassification },
          context: { page_context: pageContext },
          page_context: pageContext
        })
      });

      if (result.success) {
        // Update local state
        const updatedClassifications = { ...classifications };

        // Find and remove the item from all categories
        Object.keys(updatedClassifications).forEach(category => {
          updatedClassifications[category as keyof typeof updatedClassifications] =
            updatedClassifications[category as keyof typeof updatedClassifications].filter(item => item.id !== itemId);
        });

        // Find the item to move
        const allItems = [...classifications.good_data, ...classifications.needs_clarification, ...classifications.unusable];
        const itemToMove = allItems.find(item => item.id === itemId);

        if (itemToMove) {
          itemToMove.classification = newClassification;
          updatedClassifications[newClassification].push(itemToMove);
        }

        setClassifications(updatedClassifications);
        onClassificationUpdate?.(itemId, newClassification);
      }
    } catch (err) {
      console.error('Error updating classification:', err);
      setError('Failed to update classification');
    }
  };

  const toggleItemExpansion = (itemId: string) => {
    const newExpanded = new Set(expandedItems);
    if (newExpanded.has(itemId)) {
      newExpanded.delete(itemId);
    } else {
      newExpanded.add(itemId);
    }
    setExpandedItems(newExpanded);
  };

  const getClassificationConfig = (classification: string) => {
    switch (classification) {
      case 'good_data':
        return {
          title: 'Good Data',
          icon: CheckCircle,
          color: 'text-green-600',
          bgColor: 'bg-green-50',
          borderColor: 'border-green-200',
          description: 'High-quality data ready for migration analysis'
        };
      case 'needs_clarification':
        return {
          title: 'Needs Clarification',
          icon: AlertTriangle,
          color: 'text-yellow-600',
          bgColor: 'bg-yellow-50',
          borderColor: 'border-yellow-200',
          description: 'Data with ambiguities requiring user input'
        };
      case 'unusable':
        return {
          title: 'Unusable',
          icon: XCircle,
          color: 'text-red-600',
          bgColor: 'bg-red-50',
          borderColor: 'border-red-200',
          description: 'Data that cannot support migration decisions'
        };
      default:
        return {
          title: 'Unknown',
          icon: FileText,
          color: 'text-gray-600',
          bgColor: 'bg-gray-50',
          borderColor: 'border-gray-200',
          description: 'Classification pending'
        };
    }
  };

  const getConfidenceColor = (confidence: string) => {
    switch (confidence) {
      case 'high': return 'text-green-600';
      case 'medium': return 'text-yellow-600';
      case 'low': return 'text-orange-600';
      case 'uncertain': return 'text-red-600';
      default: return 'text-gray-600';
    }
  };

  const getTotalCount = React.useCallback(() => {
    return classifications.good_data.length +
           classifications.needs_clarification.length +
           classifications.unusable.length;
  }, [classifications]);

  const getCompletionPercentage = React.useCallback(() => {
    const total = getTotalCount();
    return total > 0 ? Math.round((classifications.good_data.length / total) * 100) : 0;
  }, [classifications, getTotalCount]);

  // Get the current classification config based on the selected tab
  const currentClassificationConfig = React.useMemo(() => {
    return getClassificationConfig(selectedTab);
  }, [selectedTab]);

  // Get the current items based on the selected tab
  const currentItems = React.useMemo(() => {
    return classifications[selectedTab] || [];
  }, [classifications, selectedTab]);

  if (isLoading) {
    return (
      <div className={`bg-white rounded-lg border shadow-sm p-4 ${className}`}>
        <div className="flex items-center space-x-2 mb-4">
          <BarChart3 className="w-5 h-5 text-blue-500" />
          <h3 className="font-medium text-gray-900">Data Classification</h3>
        </div>
        <div className="flex items-center justify-center py-8">
          <Loader2 className="w-6 h-6 animate-spin text-blue-500" />
          <span className="ml-2 text-gray-600">Loading classifications...</span>
        </div>
      </div>
    );
  }

  return (
    <div className={`bg-white rounded-lg border shadow-sm ${className}`}>
      <div className="p-4 border-b">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-2">
            <BarChart3 className="w-5 h-5 text-blue-500" />
            <h3 className="font-medium text-gray-900">Data Classification</h3>
            <span className="text-sm text-gray-500">by AI Agents</span>
          </div>
          {isProcessing && (
            <Loader2 className="w-4 h-4 animate-spin text-blue-500" />
          )}
        </div>

        {getTotalCount() > 0 && (
          <div className="mb-4">
            <div className="flex items-center justify-between text-sm mb-2">
              <span className="text-gray-600">Data Quality Progress</span>
              <span className="font-medium text-gray-900">{getCompletionPercentage()}% Ready</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className="bg-green-500 h-2 rounded-full transition-all duration-300"
                style={{ width: `${getCompletionPercentage()}%` }}
              />
            </div>
          </div>
        )}

        {/* Classification Tabs - Horizontal 3-Column Layout */}
        <div className="grid grid-cols-3 gap-2">
          {(['good_data', 'needs_clarification', 'unusable'] as const).map((classification) => {
            const config = getClassificationConfig(classification);
            const count = classifications[classification].length;
            const Icon = config.icon;

            return (
              <button
                key={classification}
                onClick={() => setSelectedTab(classification)}
                className={`p-3 rounded-md border transition-all duration-200 hover:shadow-md ${
                  selectedTab === classification
                    ? `${config.bgColor} ${config.borderColor} ${config.color} shadow-md`
                    : 'bg-gray-50 border-gray-200 text-gray-600 hover:bg-gray-100'
                }`}
              >
                <div className="text-center">
                  <Icon className="w-5 h-5 mx-auto mb-1" />
                  <div className="text-lg font-bold">{count}</div>
                  <div className="text-xs font-medium">{config.title}</div>
                </div>
              </button>
            );
          })}
        </div>
      </div>

      {/* Expanded Details Section - Shows Below When Tab is Selected */}
      {selectedTab && currentItems.length > 0 && (
        <div className="border-t bg-gray-50">
          <div className="p-4">
            <div className="flex items-center space-x-2 mb-3">
              <currentClassificationConfig.icon className={`w-4 h-4 ${currentClassificationConfig.color}`} />
              <h4 className="font-medium text-gray-900">{currentClassificationConfig.title}</h4>
              <span className="text-sm text-gray-500">({currentItems.length} items)</span>
            </div>

            <div className="space-y-2 max-h-48 overflow-y-auto">
              {currentItems.map((item, index) => (
                <div key={item.id} className="bg-white border rounded p-3 hover:bg-gray-50 transition-colors">
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <div className="text-sm font-medium text-gray-900">
                        {item.content?.Hostname || item.content?.hostname ||
                         item.content?.Name || item.content?.name ||
                         item.content?.['Asset Name'] || `Asset ${index + 1}`}
                      </div>
                      <div className="text-xs text-gray-500 mt-1">
                        {item.data_type} • <span className={getConfidenceColor(item.confidence)}>{item.confidence} confidence</span>
                      </div>

                      {/* Show key details for the asset */}
                      {item.content && (
                        <div className="text-xs text-gray-600 mt-1">
                          {item.content['CPU (Cores)'] && `CPU: ${item.content['CPU (Cores)']} cores`}
                          {item.content['CPU (Cores)'] && item.content['RAM (GB)'] && ' • '}
                          {item.content['RAM (GB)'] && `RAM: ${item.content['RAM (GB)']} GB`}
                          {(item.content['CPU (Cores)'] || item.content['RAM (GB)']) && item.content['Environment'] && ' • '}
                          {item.content['Environment'] && `Env: ${item.content['Environment']}`}
                        </div>
                      )}
                    </div>

                    {/* Classification Actions */}
                    <div className="flex space-x-1 ml-2">
                      {(['good_data', 'needs_clarification', 'unusable'] as const)
                        .filter(c => c !== item.classification)
                        .map((newClassification) => {
                          const actionConfig = getClassificationConfig(newClassification);
                          return (
                            <button
                              key={newClassification}
                              onClick={(e) => {
                                e.stopPropagation();
                                updateClassification(item.id, newClassification);
                              }}
                              className={`p-1 rounded hover:${actionConfig.bgColor} ${actionConfig.color} transition-colors`}
                              title={`Mark as ${actionConfig.title}`}
                            >
                              <actionConfig.icon className="w-3 h-3" />
                            </button>
                          );
                        })}
                    </div>
                  </div>

                  {/* Show issues if any for needs_clarification or unusable */}
                  {(item.classification === 'needs_clarification' || item.classification === 'unusable') &&
                   item.issues && item.issues.length > 0 && (
                    <div className="mt-2 p-2 bg-red-50 rounded text-xs">
                      <strong className="text-red-700">Issues:</strong>
                      <div className="text-red-600 mt-1">
                        {item.issues.slice(0, 2).map((issue, idx) => (
                          <div key={idx}>• {issue}</div>
                        ))}
                        {item.issues.length > 2 && (
                          <div className="text-red-500">... and {item.issues.length - 2} more</div>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Empty State */}
      {getTotalCount() === 0 && (
        <div className="p-6 text-center text-gray-500">
          <BarChart3 className="w-8 h-8 mx-auto mb-2 opacity-50" />
          <p className="text-sm">No data classifications yet</p>
          <p className="text-xs">Agents will classify data as it's processed</p>
        </div>
      )}

      {error && (
        <div className="p-4 border-t">
          <div className="text-sm text-red-600 flex items-center space-x-2">
            <AlertTriangle className="w-4 h-4" />
            <span>{error}</span>
          </div>
        </div>
      )}
    </div>
  );
};

export default DataClassificationDisplay;
