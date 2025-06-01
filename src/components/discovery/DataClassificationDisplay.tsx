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
}

const DataClassificationDisplay: React.FC<DataClassificationDisplayProps> = ({
  pageContext,
  onClassificationUpdate,
  className = ""
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
    // Set up polling for classification updates
    const interval = setInterval(fetchClassifications, 15000); // Poll every 15 seconds
    return () => clearInterval(interval);
  }, [pageContext]);

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
          <button
            onClick={fetchClassifications}
            className="p-1 hover:bg-gray-100 rounded-full transition-colors"
            title="Refresh classifications"
          >
            <RefreshCw className="w-4 h-4 text-gray-500" />
          </button>
        </div>

        {/* Progress Summary */}
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

        {/* Classification Tabs */}
        <div className="flex space-x-2">
          {(['good_data', 'needs_clarification', 'unusable'] as const).map((classification) => {
            const config = getClassificationConfig(classification);
            const count = classifications[classification].length;
            const Icon = config.icon;
            
            return (
              <button
                key={classification}
                onClick={() => setSelectedTab(classification)}
                className={`flex items-center space-x-2 px-3 py-2 rounded-md border transition-colors ${
                  selectedTab === classification
                    ? `${config.bgColor} ${config.borderColor} ${config.color}`
                    : 'bg-gray-50 border-gray-200 text-gray-600 hover:bg-gray-100'
                }`}
              >
                <Icon className="w-4 h-4" />
                <span className="text-sm font-medium">{config.title}</span>
                <span className="text-xs bg-white px-2 py-1 rounded-full">
                  {count}
                </span>
              </button>
            );
          })}
        </div>
      </div>

      <div className="max-h-96 overflow-y-auto">
        {error && (
          <div className="p-4 bg-red-50 border-l-4 border-red-500">
            <div className="flex items-center">
              <XCircle className="w-5 h-5 text-red-500 mr-2" />
              <span className="text-red-700">{error}</span>
            </div>
          </div>
        )}

        {getTotalCount() === 0 && !error && (
          <div className="p-6 text-center text-gray-500">
            <Brain className="w-8 h-8 mx-auto mb-2 text-gray-400" />
            <p>No data classifications yet</p>
            <p className="text-sm mt-1">Agents will classify data as it's processed</p>
          </div>
        )}

        {currentItems.length === 0 && getTotalCount() > 0 && (
          <div className="p-6 text-center text-gray-500">
            <currentClassificationConfig.icon className="w-8 h-8 mx-auto mb-2 text-gray-400" />
            <p>No {currentClassificationConfig.title.toLowerCase()} items</p>
            <p className="text-sm mt-1">{currentClassificationConfig.description}</p>
          </div>
        )}

        {/* Current Classification Items */}
        {currentItems.map((item) => (
          <div
            key={item.id}
            className={`border-l-4 p-4 border-b border-gray-100 ${currentClassificationConfig.borderColor}`}
          >
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <div className="flex items-center space-x-2 mb-2">
                  <span className="font-medium text-gray-900">{item.data_type}</span>
                  <span className={`text-sm ${getConfidenceColor(item.confidence)}`}>
                    {item.confidence} confidence
                  </span>
                  <button
                    onClick={() => toggleItemExpansion(item.id)}
                    className="p-1 hover:bg-gray-100 rounded"
                  >
                    {expandedItems.has(item.id) ? (
                      <ChevronUp className="w-4 h-4 text-gray-500" />
                    ) : (
                      <ChevronDown className="w-4 h-4 text-gray-500" />
                    )}
                  </button>
                </div>

                {/* Agent Analysis Summary */}
                {item.agent_analysis && (
                  <p className="text-sm text-gray-600 mb-2">
                    {item.agent_analysis.reasoning || item.agent_analysis.summary || 'Analyzed by AI agent'}
                  </p>
                )}

                {/* Issues */}
                {item.issues && item.issues.length > 0 && (
                  <div className="mb-2">
                    <span className="text-xs font-medium text-red-600">Issues:</span>
                    <ul className="text-xs text-gray-600 ml-2">
                      {item.issues.map((issue, index) => (
                        <li key={index} className="list-disc list-inside">{issue}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Recommendations */}
                {item.recommendations && item.recommendations.length > 0 && (
                  <div className="mb-2">
                    <span className="text-xs font-medium text-blue-600">Recommendations:</span>
                    <ul className="text-xs text-gray-600 ml-2">
                      {item.recommendations.map((rec, index) => (
                        <li key={index} className="list-disc list-inside">{rec}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Expanded Details */}
                {expandedItems.has(item.id) && (
                  <div className="mt-3 p-3 bg-gray-50 rounded-md">
                    <h5 className="text-sm font-medium text-gray-700 mb-2">Agent Analysis Details</h5>
                    <pre className="text-xs text-gray-600 whitespace-pre-wrap">
                      {JSON.stringify(item.agent_analysis, null, 2)}
                    </pre>
                    
                    {item.content && (
                      <>
                        <h5 className="text-sm font-medium text-gray-700 mb-2 mt-3">Content Sample</h5>
                        <pre className="text-xs text-gray-600 whitespace-pre-wrap">
                          {JSON.stringify(item.content, null, 2)}
                        </pre>
                      </>
                    )}
                  </div>
                )}

                {/* Classification Update Actions */}
                <div className="flex items-center space-x-2 mt-3">
                  <span className="text-xs text-gray-500">Correct classification:</span>
                  {(['good_data', 'needs_clarification', 'unusable'] as const)
                    .filter(classification => classification !== item.classification)
                    .map((classification) => {
                      const config = getClassificationConfig(classification);
                      const Icon = config.icon;
                      return (
                        <button
                          key={classification}
                          onClick={() => updateClassification(item.id, classification)}
                          className={`flex items-center space-x-1 px-2 py-1 text-xs rounded ${config.bgColor} ${config.color} hover:opacity-80 transition-opacity`}
                          title={`Mark as ${config.title}`}
                        >
                          <Icon className="w-3 h-3" />
                          <span>{config.title}</span>
                        </button>
                      );
                    })}
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default DataClassificationDisplay; 