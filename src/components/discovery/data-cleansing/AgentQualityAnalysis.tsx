import React from 'react'
import { useState } from 'react'
import { Brain, AlertCircle } from 'lucide-react'
import { Lightbulb, Target, TrendingUp, ChevronDown, ChevronUp, Zap, Edit3, Check, X } from 'lucide-react'

interface QualityIssue {
  id: string;
  asset_id: string;
  asset_name: string;
  issue_type: string;
  severity: 'critical' | 'high' | 'medium' | 'low';
  description: string;
  suggested_fix: string;
  confidence: number;
  impact: string;
  current_value?: string;
  field_name?: string;
}

interface AgentRecommendation {
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

interface AgentQualityAnalysisProps {
  qualityIssues: QualityIssue[];
  recommendations: AgentRecommendation[];
  agentConfidence: number;
  analysisType: 'agent_driven' | 'fallback_rules' | 'error';
  onApplyRecommendation: (recommendationId: string) => void;
  onFixIssue: (issueId: string, customValue?: string) => void;
  isLoading?: boolean;
}

const AgentQualityAnalysis: React.FC<AgentQualityAnalysisProps> = ({
  qualityIssues,
  recommendations,
  agentConfidence,
  analysisType,
  onApplyRecommendation,
  onFixIssue,
  isLoading = false
}) => {
  const [expandedIssues, setExpandedIssues] = useState<Set<string>>(new Set());
  const [expandedRecommendations, setExpandedRecommendations] = useState<Set<string>>(new Set());
  const [editingIssue, setEditingIssue] = useState<string | null>(null);
  const [editValues, setEditValues] = useState<Record<string, string>>({});

  const toggleIssueExpansion = (issueId: string): unknown => {
    const newExpanded = new Set(expandedIssues);
    if (newExpanded.has(issueId)) {
      newExpanded.delete(issueId);
    } else {
      newExpanded.add(issueId);
    }
    setExpandedIssues(newExpanded);
  };

  const toggleRecommendationExpansion = (recId: string): unknown => {
    const newExpanded = new Set(expandedRecommendations);
    if (newExpanded.has(recId)) {
      newExpanded.delete(recId);
    } else {
      newExpanded.add(recId);
    }
    setExpandedRecommendations(newExpanded);
  };

  const startEditing = (issueId: string, currentValue: string): unknown => {
    setEditingIssue(issueId);
    setEditValues({ ...editValues, [issueId]: currentValue });
  };

  const cancelEditing = (): unknown => {
    setEditingIssue(null);
    setEditValues({});
  };

  const saveEdit = (issueId: string): unknown => {
    const newValue = editValues[issueId];
    if (newValue !== undefined) {
      onFixIssue(issueId, newValue);
      setEditingIssue(null);
      setEditValues({});
    }
  };

  const getSeverityColor = (severity: string): unknown => {
    switch (severity) {
      case 'critical': return 'text-red-600 bg-red-100 border-red-200';
      case 'high': return 'text-orange-600 bg-orange-100 border-orange-200';
      case 'medium': return 'text-yellow-600 bg-yellow-100 border-yellow-200';
      case 'low': return 'text-blue-600 bg-blue-100 border-blue-200';
      default: return 'text-gray-600 bg-gray-100 border-gray-200';
    }
  };

  const getPriorityColor = (priority: string): unknown => {
    switch (priority) {
      case 'high': return 'text-red-600 bg-red-100';
      case 'medium': return 'text-yellow-600 bg-yellow-100';
      case 'low': return 'text-green-600 bg-green-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const getConfidenceColor = (confidence: number): unknown => {
    if (confidence >= 0.8) return 'text-green-600 bg-green-100';
    if (confidence >= 0.6) return 'text-yellow-600 bg-yellow-100';
    return 'text-red-600 bg-red-100';
  };

  if (isLoading) {
    return (
      <div className="space-y-6 animate-pulse">
        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="h-6 bg-gray-200 rounded mb-4"></div>
          <div className="h-16 bg-gray-200 rounded"></div>
        </div>
      </div>
    );
  }

  const analysisDisplay = ((): unknown => {
    switch (analysisType) {
      case 'agent_driven':
        return { text: 'Agent Intelligence Active', color: 'text-green-600 bg-green-100', icon: Brain };
      case 'fallback_rules':
        return { text: 'Rule-Based Analysis', color: 'text-yellow-600 bg-yellow-100', icon: Target };
      case 'error':
        return { text: 'Analysis Error', color: 'text-red-600 bg-red-100', icon: AlertCircle };
      default:
        return { text: 'Unknown', color: 'text-gray-600 bg-gray-100', icon: AlertCircle };
    }
  })();

  const AnalysisIcon = analysisDisplay.icon;

  return (
    <div className="space-y-6">
      {/* Analysis Header */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-3">
            <AnalysisIcon className="h-6 w-6 text-blue-500" />
            <h2 className="text-xl font-semibold text-gray-900">Quality Intelligence</h2>
          </div>
          <div className="flex items-center space-x-3">
            <span className={`px-3 py-1 text-sm rounded-full ${analysisDisplay.color}`}>
              {analysisDisplay.text}
            </span>
            <span className={`px-3 py-1 text-sm rounded-full ${getConfidenceColor(agentConfidence)}`}>
              {Math.round(agentConfidence * 100)}% Confidence
            </span>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4 text-center">
          <div className="p-3 bg-red-50 rounded-lg">
            <div className="text-2xl font-bold text-red-600">{qualityIssues.length}</div>
            <div className="text-sm text-red-700">Quality Issues Identified</div>
          </div>
          <div className="p-3 bg-blue-50 rounded-lg">
            <div className="text-2xl font-bold text-blue-600">{recommendations.length}</div>
            <div className="text-sm text-blue-700">Improvement Recommendations</div>
          </div>
        </div>
      </div>

      {/* Quality Issues with Inline Editing */}
      {qualityIssues.length > 0 && (
        <div className="bg-white rounded-lg shadow-md">
          <div className="p-6 border-b border-gray-200">
            <div className="flex items-center space-x-3">
              <Target className="h-6 w-6 text-red-500" />
              <h3 className="text-lg font-semibold text-gray-900">Priority Quality Issues</h3>
            </div>
          </div>
          <div className="max-h-96 overflow-y-auto">
            {qualityIssues.slice(0, 10).map((issue) => (
              <div
                key={issue.id}
                className={`border-l-4 p-4 border-b border-gray-100 ${getSeverityColor(issue.severity)}`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-2 mb-2">
                      <span className="font-medium text-gray-900">{issue.asset_name}</span>
                      <span className={`text-xs px-2 py-1 rounded-full ${getSeverityColor(issue.severity)}`}>
                        {issue.severity}
                      </span>
                      <span className={`text-xs px-2 py-1 rounded-full ${getConfidenceColor(issue.confidence)}`}>
                        {Math.round(issue.confidence * 100)}% confidence
                      </span>
                    </div>

                    <h4 className="font-medium text-gray-900 mb-1">{issue.issue_type}</h4>
                    <p className="text-sm text-gray-600 mb-2">{issue.description}</p>

                    {issue.current_value !== undefined && (
                      <div className="mb-2 p-2 bg-gray-50 rounded-md">
                        <div className="text-xs font-medium text-gray-700 mb-1">Current Value:</div>
                        {editingIssue === issue.id ? (
                          <div className="flex items-center space-x-2">
                            <input
                              type="text"
                              value={editValues[issue.id] || issue.current_value}
                              onChange={(e) => setEditValues({ ...editValues, [issue.id]: e.target.value })}
                              className="flex-1 text-sm border border-gray-300 rounded px-2 py-1"
                              placeholder="Enter corrected value"
                            />
                            <button
                              onClick={() => saveEdit(issue.id)}
                              className="p-1 text-green-600 hover:bg-green-100 rounded"
                            >
                              <Check className="w-4 h-4" />
                            </button>
                            <button
                              onClick={cancelEditing}
                              className="p-1 text-red-600 hover:bg-red-100 rounded"
                            >
                              <X className="w-4 h-4" />
                            </button>
                          </div>
                        ) : (
                          <div className="flex items-center space-x-2">
                            <span className="text-sm text-gray-800 font-mono">"{issue.current_value || 'Empty'}"</span>
                            <button
                              onClick={() => startEditing(issue.id, issue.current_value || '')}
                              className="p-1 text-blue-600 hover:bg-blue-100 rounded"
                              title="Edit value"
                            >
                              <Edit3 className="w-4 h-4" />
                            </button>
                          </div>
                        )}
                      </div>
                    )}

                    {expandedIssues.has(issue.id) && (
                      <div className="mt-3 p-3 bg-gray-50 rounded-md">
                        <h5 className="text-sm font-medium text-gray-700 mb-1">Suggested Fix:</h5>
                        <p className="text-sm text-gray-600 mb-2">{issue.suggested_fix}</p>
                        <p className="text-xs text-gray-500">Impact: {issue.impact}</p>
                        {issue.field_name && (
                          <p className="text-xs text-gray-500">Field: {issue.field_name}</p>
                        )}
                      </div>
                    )}

                    <div className="flex items-center space-x-3 mt-3">
                      <button
                        onClick={() => toggleIssueExpansion(issue.id)}
                        className="flex items-center text-sm text-gray-600 hover:text-gray-800"
                      >
                        {expandedIssues.has(issue.id) ? (
                          <ChevronUp className="w-4 h-4 mr-1" />
                        ) : (
                          <ChevronDown className="w-4 h-4 mr-1" />
                        )}
                        {expandedIssues.has(issue.id) ? 'Hide details' : 'Show details'}
                      </button>

                      <button
                        onClick={() => onFixIssue(issue.id)}
                        className="px-3 py-1 bg-blue-600 text-white text-sm rounded hover:bg-blue-700 transition-colors"
                      >
                        Apply Suggested Fix
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Enhanced Agent Recommendations */}
      {recommendations.length > 0 && (
        <div className="bg-white rounded-lg shadow-md">
          <div className="p-6 border-b border-gray-200">
            <div className="flex items-center space-x-3">
              <Lightbulb className="h-6 w-6 text-yellow-500" />
              <h3 className="text-lg font-semibold text-gray-900">Agent Recommendations</h3>
            </div>
          </div>
          <div className="max-h-96 overflow-y-auto">
            {recommendations.map((rec) => (
              <div
                key={rec.id}
                className="border-l-4 border-blue-200 p-4 border-b border-gray-100 bg-blue-50"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-2 mb-2">
                      <span className="font-medium text-gray-900">{rec.title}</span>
                      <span className={`text-xs px-2 py-1 rounded-full ${getPriorityColor(rec.priority)}`}>
                        {rec.priority} priority
                      </span>
                      <span className={`text-xs px-2 py-1 rounded-full ${getConfidenceColor(rec.confidence)}`}>
                        {Math.round(rec.confidence * 100)}% confidence
                      </span>
                    </div>

                    <p className="text-sm text-gray-600 mb-2">{rec.description}</p>
                    <p className="text-xs text-gray-500 mb-2">
                      Affects {rec.affected_assets} assets • {rec.estimated_improvement}% improvement expected
                    </p>

                    {rec.examples && rec.examples.length > 0 && (
                      <div className="mb-3 p-2 bg-blue-100 rounded-md">
                        <h5 className="text-xs font-medium text-blue-800 mb-1">Examples of Changes:</h5>
                        <ul className="text-xs text-blue-700 space-y-1">
                          {rec.examples.slice(0, 3).map((example, idx) => (
                            <li key={idx} className="flex items-center">
                              <span className="w-2 h-2 bg-blue-400 rounded-full mr-2"></span>
                              {example}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {expandedRecommendations.has(rec.id) && (
                      <div className="mt-3 p-3 bg-white rounded-md border">
                        <h5 className="text-sm font-medium text-gray-700 mb-2">Technical Details</h5>
                        <div className="text-xs space-y-1">
                          <p><span className="font-medium">Operation:</span> {rec.change_details.operation_type}</p>
                          <p><span className="font-medium">Fields Affected:</span> {rec.change_details.fields_affected.join(', ')}</p>
                          <p><span className="font-medium">Assets to Change:</span> {rec.affected_assets}</p>
                        </div>
                      </div>
                    )}

                    <div className="flex items-center space-x-3 mt-3">
                      <button
                        onClick={() => toggleRecommendationExpansion(rec.id)}
                        className="flex items-center text-sm text-gray-600 hover:text-gray-800"
                      >
                        {expandedRecommendations.has(rec.id) ? (
                          <ChevronUp className="w-4 h-4 mr-1" />
                        ) : (
                          <ChevronDown className="w-4 h-4 mr-1" />
                        )}
                        {expandedRecommendations.has(rec.id) ? 'Hide details' : 'Show details'}
                      </button>

                      <button
                        onClick={() => onApplyRecommendation(rec.id)}
                        className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white text-sm rounded hover:bg-blue-700 transition-colors"
                      >
                        <Zap className="w-4 h-4" />
                        <span>Apply Recommendation</span>
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Empty States */}
      {qualityIssues.length === 0 && recommendations.length === 0 && (
        <div className="bg-white rounded-lg shadow-md p-8 text-center">
          <TrendingUp className="w-12 h-12 text-green-500 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-gray-900 mb-2">Excellent Data Quality!</h3>
          <p className="text-gray-600">No quality issues or recommendations found. Your data is ready for migration.</p>
        </div>
      )}
    </div>
  );
};

export default AgentQualityAnalysis;
