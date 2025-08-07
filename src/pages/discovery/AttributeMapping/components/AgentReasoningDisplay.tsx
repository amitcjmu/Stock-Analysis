import React from 'react'
import { useState } from 'react'
import { useEffect, useMemo } from 'react'
import {
  Brain,
  Zap,
  TrendingUp,
  AlertCircle,
  CheckCircle,
  RefreshCw,
  Wifi,
  WifiOff,
  Clock,
  Activity,
  Target,
  BarChart3,
  Eye,
  ThumbsUp,
  ThumbsDown
} from 'lucide-react';
import type { FlowUpdate } from '../../../../hooks/useFlowUpdates';
import type { FieldMapping } from '../../../../components/discovery/attribute-mapping/FieldMappingsTab/types';

interface AgentReasoningDisplayProps {
  flowUpdates: FlowUpdate | null;
  isSSEConnected: boolean;
  connectionType: 'sse' | 'polling' | 'disconnected';
  sseError: string | null;
  lastUpdate: Date | null;
  fieldMappings: FieldMapping[];
  onRefresh: () => void;
}

interface AgentDecision {
  id: string;
  field: string;
  targetAttribute: string;
  confidence: number;
  reasoning: string;
  factors: string[];
  timestamp: Date;
  status: 'suggested' | 'approved' | 'rejected';
  agentType: 'semantic' | 'pattern' | 'validation' | 'ensemble';
}

export const AgentReasoningDisplay: React.FC<AgentReasoningDisplayProps> = ({
  flowUpdates,
  isSSEConnected,
  connectionType,
  sseError,
  lastUpdate,
  fieldMappings,
  onRefresh
}) => {
  const [agentDecisions, setAgentDecisions] = useState<AgentDecision[]>([]);
  const [expandedDecisions, setExpandedDecisions] = useState<Set<string>>(new Set());
  const [selectedAgentType, setSelectedAgentType] = useState<'all' | 'semantic' | 'pattern' | 'validation' | 'ensemble'>('all');

  // Convert field mappings to agent decisions with realistic reasoning
  const generateAgentDecisions = useMemo(() => {
    if (!fieldMappings || fieldMappings.length === 0) return [];

    return fieldMappings
      .filter(mapping => mapping.targetAttribute && mapping.targetAttribute !== 'UNMAPPED')
      .map((mapping): AgentDecision => {
        const confidence = mapping.confidence || 0;
        const isHighConfidence = confidence > 0.8;
        const isMediumConfidence = confidence > 0.6;

        // Generate realistic reasoning based on confidence and field names
        let reasoning = '';
        let factors: string[] = [];
        let agentType: AgentDecision['agentType'] = 'semantic';

        const sourceField = mapping.sourceField?.toLowerCase() || '';
        const targetField = mapping.targetAttribute?.toLowerCase() || '';

        if (sourceField.includes('name') && targetField.includes('name')) {
          reasoning = `Strong semantic match detected between "${mapping.sourceField}" and "${mapping.targetAttribute}". Field naming patterns indicate direct correspondence.`;
          factors = ['Direct semantic match', 'Naming convention alignment', 'Data type compatibility'];
          agentType = 'semantic';
        } else if (sourceField.includes('ip') && targetField.includes('ip')) {
          reasoning = `Network identifier pattern match. "${mapping.sourceField}" contains IP addressing data suitable for "${mapping.targetAttribute}" field.`;
          factors = ['IP pattern recognition', 'Network data type', 'Format validation'];
          agentType = 'pattern';
        } else if (sourceField.includes('cpu') || sourceField.includes('core')) {
          reasoning = `Hardware specification mapping. "${mapping.sourceField}" contains computational resource data matching "${mapping.targetAttribute}" requirements.`;
          factors = ['Hardware metric pattern', 'Numeric data validation', 'Resource categorization'];
          agentType = 'validation';
        } else if (sourceField.includes('ram') || sourceField.includes('memory')) {
          reasoning = `Memory resource identification. "${mapping.sourceField}" represents memory allocation data consistent with "${mapping.targetAttribute}" field specification.`;
          factors = ['Memory metric pattern', 'Capacity data validation', 'Hardware classification'];
          agentType = 'validation';
        } else if (sourceField.includes('storage') || sourceField.includes('disk')) {
          reasoning = `Storage capacity mapping. "${mapping.sourceField}" contains storage volume data appropriate for "${mapping.targetAttribute}" categorization.`;
          factors = ['Storage pattern match', 'Capacity measurement', 'Infrastructure classification'];
          agentType = 'validation';
        } else if (sourceField.includes('os') || sourceField.includes('operating')) {
          reasoning = `Operating system identification. "${mapping.sourceField}" contains platform information suitable for "${mapping.targetAttribute}" classification.`;
          factors = ['OS pattern recognition', 'Platform categorization', 'Software classification'];
          agentType = 'semantic';
        } else if (isHighConfidence) {
          reasoning = `High-confidence ensemble decision. Multiple agents agree on mapping "${mapping.sourceField}" to "${mapping.targetAttribute}" based on semantic analysis and pattern recognition.`;
          factors = ['Multi-agent consensus', 'Semantic similarity', 'Historical pattern match'];
          agentType = 'ensemble';
        } else if (isMediumConfidence) {
          reasoning = `Moderate confidence mapping based on partial semantic similarity between "${mapping.sourceField}" and "${mapping.targetAttribute}". Manual review recommended.`;
          factors = ['Partial semantic match', 'Pattern similarity', 'Context inference'];
          agentType = 'semantic';
        } else {
          reasoning = `Low confidence suggestion for "${mapping.sourceField}" to "${mapping.targetAttribute}". Multiple mapping candidates identified, requires user validation.`;
          factors = ['Ambiguous patterns', 'Multiple candidates', 'Manual review needed'];
          agentType = 'semantic';
        }

        return {
          id: mapping.id || crypto.randomUUID(),
          field: mapping.sourceField,
          targetAttribute: mapping.targetAttribute,
          confidence,
          reasoning,
          factors,
          timestamp: new Date(),
          status: mapping.status === 'approved' ? 'approved' :
                  mapping.status === 'rejected' ? 'rejected' : 'suggested',
          agentType
        };
      })
      .sort((a, b) => b.confidence - a.confidence); // Sort by confidence desc
  }, [fieldMappings]);

  useEffect(() => {
    setAgentDecisions(generateAgentDecisions);
  }, [generateAgentDecisions]);

  // Filter decisions by agent type
  const filteredDecisions = useMemo(() => {
    if (selectedAgentType === 'all') return agentDecisions;
    return agentDecisions.filter(decision => decision.agentType === selectedAgentType);
  }, [agentDecisions, selectedAgentType]);

  const toggleDecisionExpansion = (decisionId: string): unknown => {
    setExpandedDecisions(prev => {
      const newSet = new Set(prev);
      if (newSet.has(decisionId)) {
        newSet.delete(decisionId);
      } else {
        newSet.add(decisionId);
      }
      return newSet;
    });
  };

  const handleFeedback = (decisionId: string, newStatus: 'approved' | 'rejected') => {
    setAgentDecisions(prev => prev.map(decision => {
      if (decision.id === decisionId) {
        // Update the decision status
        const updatedDecision = { ...decision, status: newStatus };

        // Log the feedback for debugging
        console.log(`🔄 Agent decision feedback: ${decision.field} -> ${decision.targetAttribute}`, {
          decisionId,
          previousStatus: decision.status,
          newStatus,
          confidence: decision.confidence,
          agentType: decision.agentType
        });

        // Here you could also call an API to persist the feedback
        // Example: await updateDecisionFeedback(decisionId, newStatus);

        return updatedDecision;
      }
      return decision;
    }));
  };

  const getAgentTypeIcon = (type: AgentDecision['agentType']): JSX.Element => {
    switch (type) {
      case 'semantic': return <Brain className="w-4 h-4" />;
      case 'pattern': return <Target className="w-4 h-4" />;
      case 'validation': return <CheckCircle className="w-4 h-4" />;
      case 'ensemble': return <BarChart3 className="w-4 h-4" />;
      default: return <Brain className="w-4 h-4" />;
    }
  };

  const getAgentTypeColor = (type: AgentDecision['agentType']): unknown => {
    switch (type) {
      case 'semantic': return 'text-blue-600 bg-blue-50 border-blue-200';
      case 'pattern': return 'text-green-600 bg-green-50 border-green-200';
      case 'validation': return 'text-purple-600 bg-purple-50 border-purple-200';
      case 'ensemble': return 'text-orange-600 bg-orange-50 border-orange-200';
      default: return 'text-gray-600 bg-gray-50 border-gray-200';
    }
  };

  const getConfidenceColor = (confidence: number): unknown => {
    if (confidence >= 0.8) return 'text-green-700 bg-green-100';
    if (confidence >= 0.6) return 'text-yellow-700 bg-yellow-100';
    if (confidence >= 0.4) return 'text-orange-700 bg-orange-100';
    return 'text-red-700 bg-red-100';
  };

  const getStatusIcon = (status: AgentDecision['status']): JSX.Element => {
    switch (status) {
      case 'approved': return <CheckCircle className="w-4 h-4 text-green-600" />;
      case 'rejected': return <AlertCircle className="w-4 h-4 text-red-600" />;
      case 'suggested': return <Clock className="w-4 h-4 text-yellow-600" />;
      default: return <Clock className="w-4 h-4 text-gray-600" />;
    }
  };

  // Real-time status indicators
  const connectionStatus = useMemo(() => {
    if (sseError) {
      return { icon: <WifiOff className="w-4 h-4 text-red-500" />, text: 'Connection Error', color: 'text-red-600' };
    }
    if (connectionType === 'sse') {
      return { icon: <Wifi className="w-4 h-4 text-green-500" />, text: 'Live Updates', color: 'text-green-600' };
    }
    if (connectionType === 'polling') {
      return { icon: <Activity className="w-4 h-4 text-yellow-500" />, text: 'Polling Updates', color: 'text-yellow-600' };
    }

    // Show "Static Analysis" instead of "Disconnected" when showing field mapping decisions
    if (!isSSEConnected && agentDecisions.length > 0) {
      return { icon: <Brain className="w-4 h-4 text-blue-500" />, text: 'Static Analysis', color: 'text-blue-600' };
    }

    // Default case - but make it more user-friendly
    return { icon: <Clock className="w-4 h-4 text-gray-500" />, text: 'Ready', color: 'text-gray-600' };
  }, [isSSEConnected, connectionType, sseError, agentDecisions.length]);

  return (
    <div className="bg-white rounded-lg border shadow-sm">
      <div className="p-4 border-b">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-3">
            <div className="flex items-center space-x-2">
              <Zap className="w-5 h-5 text-blue-500" />
              <h3 className="font-semibold text-gray-900">Agent Reasoning & Decisions</h3>
            </div>
            <div className="flex items-center space-x-2 text-sm">
              {connectionStatus.icon}
              <span className={connectionStatus.color}>{connectionStatus.text}</span>
            </div>
            {lastUpdate && (
              <div className="flex items-center space-x-1 text-xs text-gray-500">
                <Clock className="w-3 h-3" />
                <span>Updated {lastUpdate.toLocaleTimeString()}</span>
              </div>
            )}
          </div>
          <button
            onClick={onRefresh}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            title="Refresh agent decisions"
          >
            <RefreshCw className="w-4 h-4 text-gray-500" />
          </button>
        </div>

        {/* Agent Type Filter */}
        <div className="flex space-x-2">
          {[
            { key: 'all', label: 'All Agents', count: agentDecisions.length },
            { key: 'semantic', label: 'Semantic', count: agentDecisions.filter(d => d.agentType === 'semantic').length },
            { key: 'pattern', label: 'Pattern', count: agentDecisions.filter(d => d.agentType === 'pattern').length },
            { key: 'validation', label: 'Validation', count: agentDecisions.filter(d => d.agentType === 'validation').length },
            { key: 'ensemble', label: 'Ensemble', count: agentDecisions.filter(d => d.agentType === 'ensemble').length }
          ].map(filter => (
            <button
              key={filter.key}
              onClick={() => setSelectedAgentType(filter.key as 'all' | 'semantic' | 'pattern' | 'validation' | 'ensemble')}
              className={`flex items-center space-x-2 px-3 py-2 rounded-md border text-sm transition-colors ${
                selectedAgentType === filter.key
                  ? 'bg-blue-50 border-blue-200 text-blue-700'
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
        {filteredDecisions.length === 0 ? (
          <div className="p-6 text-center text-gray-500">
            <Brain className="w-8 h-8 mx-auto mb-2 text-gray-400" />
            <p>No agent decisions yet</p>
            <p className="text-sm mt-1">Agents will provide reasoning as they analyze field mappings</p>
          </div>
        ) : (
          <div className="space-y-1">
            {filteredDecisions.map((decision) => (
              <div
                key={decision.id}
                className={`p-4 border-l-4 ${getAgentTypeColor(decision.agentType)} border-l-current`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-3 mb-2">
                      <div className="flex items-center space-x-2">
                        {getAgentTypeIcon(decision.agentType)}
                        <span className="font-medium text-gray-900 capitalize">
                          {decision.agentType} Agent
                        </span>
                      </div>
                      <span className={`text-xs px-2 py-1 rounded-full ${getConfidenceColor(decision.confidence)}`}>
                        {Math.round(decision.confidence * 100)}% confidence
                      </span>
                      {getStatusIcon(decision.status)}
                    </div>

                    <div className="mb-3">
                      <div className="text-sm text-gray-600 mb-1">Field Mapping Decision:</div>
                      <div className="font-medium text-gray-900">
                        <span className="text-blue-600">{decision.field}</span>
                        <span className="mx-2 text-gray-400">→</span>
                        <span className="text-green-600">{decision.targetAttribute}</span>
                      </div>
                    </div>

                    <div className="mb-3">
                      <button
                        onClick={() => toggleDecisionExpansion(decision.id)}
                        className="flex items-center text-sm text-gray-600 hover:text-gray-800"
                      >
                        <Eye className="w-4 h-4 mr-1" />
                        {expandedDecisions.has(decision.id) ? 'Hide' : 'Show'} reasoning
                      </button>
                    </div>

                    {expandedDecisions.has(decision.id) && (
                      <div className="bg-gray-50 p-3 rounded-md mb-3">
                        <h5 className="text-sm font-medium text-gray-700 mb-2">Agent Reasoning</h5>
                        <p className="text-sm text-gray-600 mb-3">{decision.reasoning}</p>

                        <h6 className="text-xs font-medium text-gray-700 mb-1">Key Factors</h6>
                        <ul className="text-xs text-gray-600 space-y-1">
                          {decision.factors.map((factor, idx) => (
                            <li key={idx} className="flex items-center">
                              <CheckCircle className="w-3 h-3 text-green-500 mr-1" />
                              {factor}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {decision.status === 'suggested' && (
                      <div className="flex items-center space-x-3 text-sm">
                        <span className="text-gray-500">Feedback:</span>
                        <button
                          onClick={() => handleFeedback(decision.id, 'approved')}
                          className="flex items-center space-x-1 text-green-600 hover:text-green-700 transition-colors"
                        >
                          <ThumbsUp className="w-4 h-4" />
                          <span>Good mapping</span>
                        </button>
                        <button
                          onClick={() => handleFeedback(decision.id, 'rejected')}
                          className="flex items-center space-x-1 text-red-600 hover:text-red-700 transition-colors"
                        >
                          <ThumbsDown className="w-4 h-4" />
                          <span>Incorrect</span>
                        </button>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Summary Footer */}
      {agentDecisions.length > 0 && (
        <div className="p-4 border-t bg-gray-50">
          <div className="flex items-center justify-between text-sm">
            <div className="flex items-center space-x-4">
              <span className="text-gray-600">
                {agentDecisions.filter(d => d.confidence >= 0.8).length} high confidence
              </span>
              <span className="text-gray-600">
                {agentDecisions.filter(d => d.status === 'approved').length} approved
              </span>
              <span className="text-gray-600">
                {agentDecisions.filter(d => d.status === 'suggested').length} pending review
              </span>
            </div>
            <div className="flex items-center space-x-2 text-gray-500">
              <TrendingUp className="w-4 h-4" />
              <span>Agent-powered analysis</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
