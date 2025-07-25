import React from 'react'
import { useState } from 'react'
import { useEffect } from 'react'
import { TrendingUp, CheckCircle, Zap, Target, Star, Eye } from 'lucide-react'
import { Lightbulb, Brain, AlertCircle, RefreshCw, ChevronDown, ChevronUp, ArrowRight, Loader2, ThumbsUp, ThumbsDown } from 'lucide-react'
import { API_CONFIG } from '../../config/api'
import { apiCall } from '../../config/api'

interface AgentInsight {
  id: string;
  agent_id: string;
  agent_name: string;
  insight_type: string;
  title: string;
  description: string;
  confidence: 'high' | 'medium' | 'low' | 'uncertain';
  supporting_data: Record<string, string | number | boolean | null> | unknown[];
  actionable: boolean;
  page: string;
  created_at: string;
}

interface AgentInsightsSectionProps {
  pageContext: string;
  onInsightAction?: (insightId: string, action: string) => void;
  className?: string;
  refreshTrigger?: number; // Increment this to trigger a refresh
  isProcessing?: boolean; // Set to true when background processing is happening
}

const AgentInsightsSection: React.FC<AgentInsightsSectionProps> = ({
  pageContext,
  onInsightAction,
  className = "",
  refreshTrigger,
  isProcessing = false
}) => {
  const [insights, setInsights] = useState<AgentInsight[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [expandedInsights, setExpandedInsights] = useState<Set<string>>(new Set());
  const [selectedFilter, setSelectedFilter] = useState<'all' | 'actionable' | 'high_confidence'>('all');
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchInsights();
  }, [pageContext]);

  // Refresh when refreshTrigger changes
  useEffect(() => {
    if (refreshTrigger !== undefined) {
      fetchInsights();
    }
  }, [refreshTrigger]);

  // Set up polling only when processing is active
  useEffect(() => {
    let interval: NodeJS.Timeout | null = null;

    if (isProcessing) {
      interval = setInterval(fetchInsights, 30000); // Poll every 30 seconds only when processing
    }

    return () => {
      if (interval) clearInterval(interval);
    };
  }, [isProcessing]);

  const fetchInsights = async () => {
    try {
      const result = await apiCall(`/api/v1/agents/discovery/agent-insights?page=${pageContext}`);
      if (result.success && result.insights) {
        setInsights(result.insights);
      }
      setError(null);
    } catch (err) {
      // Handle 404 errors gracefully - these endpoints may not exist yet
      if (err.status === 404 || err.response?.status === 404) {
        console.log('Agent insights endpoint not available yet');
        setInsights([]);
        setError(null);
      } else {
        console.error('Error fetching agent insights:', err);
        setError('Failed to load agent insights');
      }
    } finally {
      setIsLoading(false);
    }
  };

  const toggleInsightExpansion = (insightId: string) => {
    const newExpanded = new Set(expandedInsights);
    if (newExpanded.has(insightId)) {
      newExpanded.delete(insightId);
    } else {
      newExpanded.add(insightId);
    }
    setExpandedInsights(newExpanded);
  };

  const getInsightTypeConfig = (type: string) => {
    switch (type) {
      case 'data_volume':
        return {
          icon: TrendingUp,
          color: 'text-blue-600',
          bgColor: 'bg-blue-50',
          borderColor: 'border-blue-200'
        };
      case 'data_richness':
        return {
          icon: Star,
          color: 'text-purple-600',
          bgColor: 'bg-purple-50',
          borderColor: 'border-purple-200'
        };
      case 'organizational_patterns':
        return {
          icon: Target,
          color: 'text-green-600',
          bgColor: 'bg-green-50',
          borderColor: 'border-green-200'
        };
      case 'data_availability':
        return {
          icon: AlertCircle,
          color: 'text-orange-600',
          bgColor: 'bg-orange-50',
          borderColor: 'border-orange-200'
        };
      case 'quality_assessment':
        return {
          icon: CheckCircle,
          color: 'text-emerald-600',
          bgColor: 'bg-emerald-50',
          borderColor: 'border-emerald-200'
        };
      case 'migration_readiness':
        return {
          icon: Zap,
          color: 'text-yellow-600',
          bgColor: 'bg-yellow-50',
          borderColor: 'border-yellow-200'
        };
      default:
        return {
          icon: Lightbulb,
          color: 'text-gray-600',
          bgColor: 'bg-gray-50',
          borderColor: 'border-gray-200'
        };
    }
  };

  const getConfidenceColor = (confidence: string) => {
    switch (confidence) {
      case 'high': return 'text-green-600 bg-green-100';
      case 'medium': return 'text-yellow-600 bg-yellow-100';
      case 'low': return 'text-orange-600 bg-orange-100';
      case 'uncertain': return 'text-red-600 bg-red-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  const getFilteredInsights = () => {
    switch (selectedFilter) {
      case 'actionable':
        return insights.filter(insight => insight.actionable);
      case 'high_confidence':
        return insights.filter(insight => insight.confidence === 'high');
      default:
        return insights;
    }
  };

  const [feedbackExplanations, setFeedbackExplanations] = useState<Map<string, string>>(new Map());
  const [showFeedbackInput, setShowFeedbackInput] = useState<Set<string>>(new Set());

  const handleInsightFeedback = async (insightId: string, helpful: boolean, explanation?: string) => {
    try {
      const insight = insights.find(i => i.id === insightId);

      // Enhanced feedback with explanation and accuracy validation
      const feedbackData = {
        learning_type: 'insight_feedback',
        original_prediction: {
          insight_id: insightId,
          title: insight?.title,
          description: insight?.description,
          supporting_data: insight?.supporting_data
        },
        user_correction: {
          helpful,
          explanation: explanation || feedbackExplanations.get(insightId) || '',
          accuracy_issues: helpful ? [] : await analyzeAccuracyIssues(insight)
        },
        context: { page_context: pageContext },
        page_context: pageContext
      };

      await apiCall('/api/v1/agents/discovery/learning/agent-learning', {
        method: 'POST',
        body: JSON.stringify(feedbackData)
      });

      onInsightAction?.(insightId, helpful ? 'helpful' : 'not_helpful');

      // Clear feedback input after submission
      setShowFeedbackInput(prev => {
        const next = new Set(prev);
        next.delete(insightId);
        return next;
      });
      setFeedbackExplanations(prev => {
        const next = new Map(prev);
        next.delete(insightId);
        return next;
      });

    } catch (err) {
      console.error('Error submitting insight feedback:', err);
    }
  };

  const analyzeAccuracyIssues = async (insight: AgentInsight | undefined): Promise<string[]> => {
    const issues: string[] = [];

    if (!insight) return issues;

    const description = insight?.description || '';
    const supportingData = insight?.supporting_data || {};

    // Check for number mismatches
    const applicationMatch = description.match(/(\d+)\s+applications/i);
    if (applicationMatch && typeof supportingData === 'object') {
      const statedCount = parseInt(applicationMatch[1]);
      const actualCount = supportingData.Application || 0;
      if (Math.abs(statedCount - actualCount) > 2) {
        issues.push(`Claims ${statedCount} applications but data shows ${actualCount}`);
      }
    }

    // Check for terminology issues
    if (description.toLowerCase().includes('technologies') && Array.isArray(supportingData)) {
      const hasAssetTypes = supportingData.some(item =>
        typeof item === 'string' &&
        ['server', 'database', 'application', 'storage', 'network'].includes(item.toLowerCase())
      );
      if (hasAssetTypes) {
        issues.push('Incorrectly refers to asset types as "technologies"');
      }
    }

    return issues;
  };

  const toggleFeedbackInput = (insightId: string) => {
    setShowFeedbackInput(prev => {
      const next = new Set(prev);
      if (next.has(insightId)) {
        next.delete(insightId);
      } else {
        next.add(insightId);
      }
      return next;
    });
  };

  const updateFeedbackExplanation = (insightId: string, explanation: string) => {
    setFeedbackExplanations(prev => {
      const next = new Map(prev);
      next.set(insightId, explanation);
      return next;
    });
  };

  if (isLoading) {
    return (
      <div className={`bg-white rounded-lg border shadow-sm p-4 ${className}`}>
        <div className="flex items-center space-x-2 mb-4">
          <Lightbulb className="w-5 h-5 text-yellow-500" />
          <h3 className="font-medium text-gray-900">Agent Insights</h3>
        </div>
        <div className="flex items-center justify-center py-8">
          <Loader2 className="w-6 h-6 animate-spin text-yellow-500" />
          <span className="ml-2 text-gray-600">Loading insights...</span>
        </div>
      </div>
    );
  }

  const filteredInsights = getFilteredInsights();

  return (
    <div className={`bg-white rounded-lg border shadow-sm ${className}`}>
      <div className="p-4 border-b">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-2">
            <Lightbulb className="w-5 h-5 text-yellow-500" />
            <h3 className="font-medium text-gray-900">Agent Insights</h3>
            <span className="text-sm text-gray-500">
              {insights.length} discoveries
            </span>
          </div>
          <button
            onClick={fetchInsights}
            className="p-1 hover:bg-gray-100 rounded-full transition-colors"
            title="Refresh insights"
          >
            <RefreshCw className="w-4 h-4 text-gray-500" />
          </button>
        </div>

        {/* Filter Tabs */}
        <div className="flex space-x-2">
          {[
            { key: 'all', label: 'All Insights', count: insights.length },
            { key: 'actionable', label: 'Actionable', count: insights.filter(i => i.actionable).length },
            { key: 'high_confidence', label: 'High Confidence', count: insights.filter(i => i.confidence === 'high').length }
          ].map((filter) => (
            <button
              key={filter.key}
              onClick={() => setSelectedFilter(filter.key as 'all' | 'actionable' | 'high_confidence')}
              className={`flex items-center space-x-2 px-3 py-2 rounded-md border text-sm transition-colors ${
                selectedFilter === filter.key
                  ? 'bg-yellow-50 border-yellow-200 text-yellow-700'
                  : 'bg-gray-50 border-gray-200 text-gray-600 hover:bg-gray-100'
              }`}
            >
              <span>{filter.label}</span>
              <span className="text-xs bg-white px-2 py-1 rounded-full">
                {filter.count}
              </span>
            </button>
          ))}
        </div>
      </div>

      <div className="max-h-96 overflow-y-auto">
        {error && (
          <div className="p-4 bg-red-50 border-l-4 border-red-500">
            <div className="flex items-center">
              <AlertCircle className="w-5 h-5 text-red-500 mr-2" />
              <span className="text-red-700">{error}</span>
            </div>
          </div>
        )}

        {filteredInsights.length === 0 && !error && (
          <div className="p-6 text-center text-gray-500">
            <Brain className="w-8 h-8 mx-auto mb-2 text-gray-400" />
            <p>
              {selectedFilter === 'all'
                ? 'No agent insights yet'
                : `No ${selectedFilter.replace('_', ' ')} insights`
              }
            </p>
            <p className="text-sm mt-1">
              Agents will provide insights as they analyze your data
            </p>
          </div>
        )}

        {/* Insights List */}
        {filteredInsights.map((insight) => {
          const typeConfig = getInsightTypeConfig(insight.insight_type);
          const TypeIcon = typeConfig.icon;

          return (
            <div
              key={insight.id}
              className={`border-l-4 p-4 border-b border-gray-100 ${typeConfig.borderColor} ${typeConfig.bgColor}`}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center space-x-2 mb-2">
                    <TypeIcon className={`w-4 h-4 ${typeConfig.color}`} />
                    <span className="font-medium text-gray-900">{insight.agent_name}</span>
                    <span className={`text-xs px-2 py-1 rounded-full ${getConfidenceColor(insight.confidence)}`}>
                      {insight.confidence} confidence
                    </span>
                    <span className="text-xs text-gray-500">
                      {formatTimestamp(insight.created_at)}
                    </span>
                    {insight.actionable && (
                      <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded-full">
                        Actionable
                      </span>
                    )}
                  </div>

                  <h4 className="font-medium text-gray-900 mb-2">{insight.title}</h4>
                  <p className="text-gray-700 mb-3">{insight.description}</p>

                  {/* Supporting Data Preview */}
                  {insight.supporting_data && Object.keys(insight.supporting_data).length > 0 && (
                    <div className="mb-3">
                      <button
                        onClick={() => toggleInsightExpansion(insight.id)}
                        className="flex items-center text-sm text-gray-600 hover:text-gray-800"
                      >
                        {expandedInsights.has(insight.id) ? (
                          <ChevronUp className="w-4 h-4 mr-1" />
                        ) : (
                          <ChevronDown className="w-4 h-4 mr-1" />
                        )}
                        View supporting data
                      </button>

                      {expandedInsights.has(insight.id) && (
                        <div className="mt-2 p-3 bg-white rounded-md border">
                          <h5 className="text-sm font-medium text-gray-700 mb-2">Supporting Data</h5>
                          <pre className="text-xs text-gray-600 whitespace-pre-wrap">
                            {JSON.stringify(insight.supporting_data, null, 2)}
                          </pre>
                        </div>
                      )}
                    </div>
                  )}

                  {/* Action Buttons */}
                  <div className="space-y-3 mt-3">
                    <div className="flex items-center space-x-3">
                      <div className="flex items-center space-x-2">
                        <span className="text-xs text-gray-500">Was this helpful?</span>
                        <button
                          onClick={() => handleInsightFeedback(insight.id, true)}
                          className="p-1 hover:bg-green-100 rounded-full transition-colors"
                          title="Mark as helpful"
                        >
                          <ThumbsUp className="w-4 h-4 text-green-600" />
                        </button>
                        <button
                          onClick={() => toggleFeedbackInput(insight.id)}
                          className="p-1 hover:bg-red-100 rounded-full transition-colors"
                          title="Mark as not helpful and explain"
                        >
                          <ThumbsDown className="w-4 h-4 text-red-600" />
                        </button>
                      </div>

                      {insight.actionable && (
                        <div className="flex items-center space-x-2">
                          <ArrowRight className="w-4 h-4 text-blue-500" />
                          <span className="text-sm text-blue-600 font-medium">
                            Consider for next steps
                          </span>
                        </div>
                      )}
                    </div>

                    {/* Feedback Input */}
                    {showFeedbackInput.has(insight.id) && (
                      <div className="bg-gray-50 p-3 rounded border">
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          What was incorrect or unhelpful about this insight?
                        </label>
                        <textarea
                          value={feedbackExplanations.get(insight.id) || ''}
                          onChange={(e) => updateFeedbackExplanation(insight.id, e.target.value)}
                          placeholder="e.g., The numbers don't match the data, terminology is wrong, not actionable..."
                          className="w-full p-2 border border-gray-300 rounded text-sm"
                          rows={3}
                        />
                        <div className="flex items-center space-x-2 mt-2">
                          <button
                            onClick={() => handleInsightFeedback(
                              insight.id,
                              false,
                              feedbackExplanations.get(insight.id)
                            )}
                            className="px-3 py-1 bg-red-600 text-white text-sm rounded hover:bg-red-700"
                          >
                            Submit Feedback
                          </button>
                          <button
                            onClick={() => toggleFeedbackInput(insight.id)}
                            className="px-3 py-1 bg-gray-300 text-gray-700 text-sm rounded hover:bg-gray-400"
                          >
                            Cancel
                          </button>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Summary Footer */}
      {insights.length > 0 && (
        <div className="p-4 border-t bg-gray-50">
          <div className="flex items-center justify-between text-sm">
            <div className="flex items-center space-x-4">
              <span className="text-gray-600">
                {insights.filter(i => i.actionable).length} actionable insights
              </span>
              <span className="text-gray-600">
                {insights.filter(i => i.confidence === 'high').length} high confidence
              </span>
            </div>
            <div className="flex items-center space-x-2 text-gray-500">
              <Brain className="w-4 h-4" />
              <span>AI-powered analysis</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AgentInsightsSection;
