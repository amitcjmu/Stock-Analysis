import React, { useState, useEffect } from 'react';
import { 
  CheckCircle, 
  AlertTriangle, 
  XCircle, 
  Eye, 
  Brain, 
  Loader2,
  ChevronDown,
  ChevronUp,
  BarChart3,
  FileText,
  RefreshCw,
  ThumbsUp,
  ThumbsDown,
  Edit3
} from 'lucide-react';
import { apiCall, API_CONFIG } from '../../config/api';

interface DataItem {
  id: string;
  data_type: string;
  classification: 'good_data' | 'needs_clarification' | 'unusable';
  content: any;
  agent_analysis: any;
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

  useEffect(() => {
    fetchClassifications();
  }, [pageContext]);

  // Refresh when refreshTrigger changes
  useEffect(() => {
    if (refreshTrigger !== undefined) {
      fetchClassifications();
    }
  }, [refreshTrigger]);

  // Set up polling only when processing is active
  useEffect(() => {
    let interval: NodeJS.Timeout | null = null;
    
    if (isProcessing) {
      interval = setInterval(fetchClassifications, 8000); // Poll every 8 seconds only when processing
    }
    
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [isProcessing]);

  const fetchClassifications = async () => {
    try {
              const result = await apiCall(`${API_CONFIG.ENDPOINTS.DISCOVERY.AGENT_STATUS}?page_context=${pageContext}`, { method: 'GET' });
      if (result.status === 'success' && result.page_data?.data_classifications) {
        setClassifications(result.page_data.data_classifications);
      }
      setError(null);
    } catch (err) {
      console.error('Error fetching data classifications:', err);
      setError('Failed to load data classifications');
    } finally {
      setIsLoading(false);
    }
  };

  const updateClassification = async (itemId: string, newClassification: 'good_data' | 'needs_clarification' | 'unusable') => {
    try {
      const result = await apiCall(API_CONFIG.ENDPOINTS.DISCOVERY.AGENT_LEARNING, {
        method: 'POST',
        body: JSON.stringify({
          learning_type: 'data_classification',
          original_prediction: { item_id: itemId },
          user_correction: { classification: newClassification },
          context: { page_context: pageContext },
          page_context: pageContext
        })
      });

      if (result.status === 'success') {
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

  const getTotalCount = () => {
    return classifications.good_data.length + 
           classifications.needs_clarification.length + 
           classifications.unusable.length;
  };

  const getCompletionPercentage = () => {
    const total = getTotalCount();
    if (total === 0) return 0;
    return Math.round((classifications.good_data.length / total) * 100);
  };

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

  const currentClassificationConfig = getClassificationConfig(selectedTab);
  const currentItems = classifications[selectedTab];

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

        {/* Classification Tabs - Simplified to show just counts */}
        <div className="space-y-2">
          {(['good_data', 'needs_clarification', 'unusable'] as const).map((classification) => {
            const config = getClassificationConfig(classification);
            const count = classifications[classification].length;
            const Icon = config.icon;
            
            return (
              <button
                key={classification}
                onClick={() => setSelectedTab(classification)}
                className={`w-full flex items-center justify-between p-3 rounded-md border transition-colors ${
                  selectedTab === classification
                    ? `${config.bgColor} ${config.borderColor} ${config.color}`
                    : 'bg-gray-50 border-gray-200 text-gray-600 hover:bg-gray-100'
                }`}
              >
                <div className="flex items-center space-x-2">
                  <Icon className="w-4 h-4" />
                  <span className="text-sm font-medium">{config.title}</span>
                </div>
                <span className="text-lg font-bold">
                  {count}
                </span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Selected Classification Details - Simplified List */}
      {currentItems.length > 0 && (
        <div className="p-4">
          <div className="flex items-center space-x-2 mb-3">
            <currentClassificationConfig.icon className={`w-4 h-4 ${currentClassificationConfig.color}`} />
            <h4 className="font-medium text-gray-900">{currentClassificationConfig.title}</h4>
            <span className="text-sm text-gray-500">({currentItems.length} items)</span>
          </div>
          
          <div className="space-y-2 max-h-64 overflow-y-auto">
            {currentItems.map((item, index) => (
              <div key={item.id} className="border rounded p-2 hover:bg-gray-50">
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <div className="text-sm font-medium text-gray-900">
                      {item.content?.Hostname || item.content?.hostname || 
                       item.content?.Name || item.content?.name || 
                       item.content?.['Asset Name'] || `Item ${index + 1}`}
                    </div>
                    <div className="text-xs text-gray-500">
                      {item.data_type} • {item.confidence} confidence
                    </div>
                  </div>
                  
                  {/* Classification Actions */}
                  <div className="flex space-x-1">
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
                            className={`p-1 rounded hover:${actionConfig.bgColor} ${actionConfig.color}`}
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
                  <div className="mt-2 text-xs text-gray-600">
                    <strong>Issues:</strong> {item.issues.slice(0, 2).join(', ')}
                    {item.issues.length > 2 && '...'}
                  </div>
                )}
              </div>
            ))}
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