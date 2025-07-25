import React from 'react'
import { useState } from 'react'
import {
  Bot,
  Brain,
  Users,
  CheckCircle,
  AlertCircle,
  Clock,
  MessageSquare,
  Lightbulb,
  BarChart3,
  Loader2,
  RefreshCw,
  ChevronDown,
  ChevronUp,
  Send,
  Network
} from 'lucide-react';
import { useAgentQuestions, useAnswerAgentQuestion, useAgentInsights, useConfidenceScores, useAgentThink, useAgentPonderMore, useAgentStatus } from '../../../hooks/useAgentQuestions'

interface AgentUIMonitorProps {
  className?: string;
  pageContext?: string;
}

const AgentUIMonitor: React.FC<AgentUIMonitorProps> = ({
  className = "",
  pageContext = "dependencies"
}) => {
  const [selectedAnswers, setSelectedAnswers] = useState<Record<string, string>>({});
  const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set(['clarifications']));
  const [activeAgent, setActiveAgent] = useState<string>('dependency_analysis_agent');

  // Fetch data using the new hooks
  const { data: questionsData, isLoading: questionsLoading, error: questionsError } = useAgentQuestions(pageContext);
  const { data: insightsData, isLoading: insightsLoading } = useAgentInsights(pageContext);
  const { data: statusData, isLoading: statusLoading } = useAgentStatus();
  const { data: confidenceData, isLoading: confidenceLoading } = useConfidenceScores(pageContext);

  // Mutations for interactions
  const answerQuestionMutation = useAnswerAgentQuestion();
  const thinkMutation = useAgentThink();
  const ponderMutation = useAgentPonderMore();

  const toggleSection = (section: string) => {
    setExpandedSections(prev => {
      const next = new Set(prev);
      if (next.has(section)) {
        next.delete(section);
      } else {
        next.add(section);
      }
      return next;
    });
  };

  const handleAnswerSelect = (questionId: string, answer: string) => {
    setSelectedAnswers(prev => ({
      ...prev,
      [questionId]: answer
    }));
  };

  const handleSubmitAnswer = async (questionId: string) => {
    const answer = selectedAnswers[questionId];
    if (!answer) return;

    try {
      await answerQuestionMutation.mutateAsync({
        question_id: questionId,
        response: answer
      });

      // Clear the selected answer
      setSelectedAnswers(prev => {
        const next = { ...prev };
        delete next[questionId];
        return next;
      });
    } catch (error) {
      console.error('Failed to submit answer:', error);
    }
  };

  const handleThink = async (agentId: string) => {
    try {
      await thinkMutation.mutateAsync({
        agent_id: agentId,
        context: { page: pageContext, action: 'deeper_analysis' },
        complexity_level: 'standard'
      });
    } catch (error) {
      console.error('Failed to trigger thinking:', error);
    }
  };

  const handlePonderMore = async (agentId: string) => {
    try {
      await ponderMutation.mutateAsync({
        agent_id: agentId,
        context: { page: pageContext, action: 'crew_collaboration' },
        collaboration_type: 'cross_agent'
      });
    } catch (error) {
      console.error('Failed to trigger pondering:', error);
    }
  };

  const questions = questionsData?.questions || [];
  const insights = insightsData?.insights || [];
  const agents = statusData?.agents || {};
  const confidence = confidenceData?.confidence_scores || {};

  const pendingQuestions = questions.filter(q => !q.is_resolved);

  return (
    <div className={`bg-white rounded-lg border shadow-sm ${className}`}>
      {/* Header */}
      <div className="p-4 border-b bg-gradient-to-r from-blue-50 to-purple-50">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Bot className="w-5 h-5 text-blue-600" />
            <h3 className="font-semibold text-gray-900">Agent Clarifications</h3>
            {pendingQuestions.length > 0 && (
              <span className="bg-red-100 text-red-800 text-xs font-medium px-2 py-1 rounded-full">
                {pendingQuestions.length} pending
              </span>
            )}
          </div>
          <div className="flex items-center space-x-2">
            {(questionsLoading || insightsLoading || statusLoading) && (
              <Loader2 className="w-4 h-4 animate-spin text-blue-500" />
            )}
            <RefreshCw className="w-4 h-4 text-gray-500 cursor-pointer hover:text-gray-700" />
          </div>
        </div>
      </div>

      {/* Agent Status Summary */}
      {!statusLoading && statusData && (
        <div className="p-4 border-b bg-gray-50">
          <div className="grid grid-cols-3 gap-4 text-center">
            <div>
              <div className="text-2xl font-bold text-green-600">
                {Object.values(agents).filter((a: unknown) => a.status === 'idle').length}
              </div>
              <div className="text-xs text-gray-600">Ready</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-blue-600">
                {confidenceData?.overall ? Math.round(confidenceData.overall) : 0}%
              </div>
              <div className="text-xs text-gray-600">Confidence</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-purple-600">
                {insights.length}
              </div>
              <div className="text-xs text-gray-600">Insights</div>
            </div>
          </div>
        </div>
      )}

      <div className="max-h-96 overflow-y-auto">
        {/* Error State */}
        {questionsError && (
          <div className="p-4 bg-red-50 border-l-4 border-red-500">
            <div className="flex items-center">
              <AlertCircle className="w-5 h-5 text-red-500 mr-2" />
              <span className="text-red-700">Failed to load agent questions</span>
            </div>
          </div>
        )}

        {/* Pending Questions Section */}
        <div className="border-b">
          <button
            onClick={() => toggleSection('clarifications')}
            className="w-full p-4 flex items-center justify-between hover:bg-gray-50 transition-colors"
          >
            <div className="flex items-center space-x-2">
              <MessageSquare className="w-4 h-4 text-orange-500" />
              <span className="font-medium">Agent Clarifications</span>
              {pendingQuestions.length > 0 && (
                <span className="bg-orange-100 text-orange-800 text-xs px-2 py-1 rounded-full">
                  {pendingQuestions.length}
                </span>
              )}
            </div>
            {expandedSections.has('clarifications') ? (
              <ChevronUp className="w-4 h-4" />
            ) : (
              <ChevronDown className="w-4 h-4" />
            )}
          </button>

          {expandedSections.has('clarifications') && (
            <div className="px-4 pb-4">
              {pendingQuestions.length === 0 ? (
                <div className="text-center py-6 text-gray-500">
                  <CheckCircle className="w-8 h-8 mx-auto mb-2 text-green-500" />
                  <p className="text-sm">No pending clarifications</p>
                  <p className="text-xs mt-1">All agent questions resolved</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {pendingQuestions.map((question) => (
                    <div key={question.id} className="border rounded-lg p-4 bg-gray-50">
                      <div className="flex items-start justify-between mb-3">
                        <div className="flex-1">
                          <h4 className="font-medium text-gray-900">{question.title}</h4>
                          <div className="flex items-center space-x-2 mt-1">
                            <span className="text-sm text-gray-600">{question.agent_name}</span>
                            <span className={`text-xs px-2 py-1 rounded ${
                              question.confidence === 'high' ? 'bg-green-100 text-green-700' :
                              question.confidence === 'medium' ? 'bg-yellow-100 text-yellow-700' :
                              'bg-red-100 text-red-700'
                            }`}>
                              {question.confidence} confidence
                            </span>
                            <span className={`text-xs px-2 py-1 rounded ${
                              question.priority === 'high' ? 'bg-red-100 text-red-700' :
                              question.priority === 'normal' ? 'bg-blue-100 text-blue-700' :
                              'bg-gray-100 text-gray-700'
                            }`}>
                              {question.priority}
                            </span>
                          </div>
                        </div>
                        <Clock className="w-4 h-4 text-gray-400 mt-1" />
                      </div>

                      <p className="text-gray-700 mb-4">{question.question}</p>

                      {/* Context for dependency questions */}
                      {question.context && question.question_type === 'dependency_validation' && (
                        <div className="bg-blue-50 rounded-lg p-3 mb-4">
                          <h5 className="text-sm font-medium text-blue-900 mb-2">Analysis Context</h5>
                          <div className="text-sm text-blue-800 space-y-1">
                            {question.context.source_app && (
                              <div>Source: <span className="font-mono">{question.context.source_app}</span></div>
                            )}
                            {question.context.target_app && (
                              <div>Target: <span className="font-mono">{question.context.target_app}</span></div>
                            )}
                            {question.context.confidence && (
                              <div>AI Confidence: {Math.round(question.context.confidence * 100)}%</div>
                            )}
                            {question.context.evidence && (
                              <div>Evidence: {question.context.evidence}</div>
                            )}
                          </div>
                        </div>
                      )}

                      {/* MCQ Options */}
                      <div className="space-y-2 mb-4">
                        {question.options.map((option, index) => (
                          <label key={index} className="flex items-center space-x-3 cursor-pointer">
                            <input
                              type="radio"
                              name={`question-${question.id}`}
                              value={option}
                              checked={selectedAnswers[question.id] === option}
                              onChange={(e) => handleAnswerSelect(question.id, e.target.value)}
                              className="w-4 h-4 text-blue-600 border-gray-300 focus:ring-blue-500"
                            />
                            <span className="text-sm text-gray-700">{option}</span>
                          </label>
                        ))}
                      </div>

                      {/* Submit Button */}
                      <div className="flex justify-end">
                        <button
                          onClick={() => handleSubmitAnswer(question.id)}
                          disabled={!selectedAnswers[question.id] || answerQuestionMutation.isPending}
                          className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center space-x-2"
                        >
                          {answerQuestionMutation.isPending ? (
                            <Loader2 className="w-4 h-4 animate-spin" />
                          ) : (
                            <Send className="w-4 h-4" />
                          )}
                          <span>Submit</span>
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Data Classifications Section */}
        <div className="border-b">
          <button
            onClick={() => toggleSection('classifications')}
            className="w-full p-4 flex items-center justify-between hover:bg-gray-50 transition-colors"
          >
            <div className="flex items-center space-x-2">
              <BarChart3 className="w-4 h-4 text-green-500" />
              <span className="font-medium">Data Classification</span>
              <span className="text-sm text-gray-500">by AI Agents</span>
            </div>
            {expandedSections.has('classifications') ? (
              <ChevronUp className="w-4 h-4" />
            ) : (
              <ChevronDown className="w-4 h-4" />
            )}
          </button>

          {expandedSections.has('classifications') && (
            <div className="px-4 pb-4">
              <div className="grid grid-cols-3 gap-4 text-center py-4">
                <div className="flex flex-col items-center">
                  <CheckCircle className="w-8 h-8 text-green-500 mb-1" />
                  <span className="text-sm font-medium text-green-700">Good Data</span>
                  <span className="text-xs text-gray-500">0 unusable</span>
                </div>
                <div className="flex flex-col items-center">
                  <AlertCircle className="w-8 h-8 text-yellow-500 mb-1" />
                  <span className="text-sm font-medium text-yellow-700">Needs Clarification</span>
                  <span className="text-xs text-gray-500">0</span>
                </div>
                <div className="flex flex-col items-center">
                  <Clock className="w-8 h-8 text-blue-500 mb-1" />
                  <span className="text-sm font-medium text-blue-700">Unusable</span>
                  <span className="text-xs text-gray-500">0</span>
                </div>
              </div>

              <div className="text-center text-gray-500 py-4">
                <Network className="w-12 h-12 mx-auto mb-2 text-gray-400" />
                <p className="text-sm">No data classifications yet</p>
                <p className="text-xs">Agents will classify data as it's processed</p>
              </div>
            </div>
          )}
        </div>

        {/* Agent Insights Section */}
        <div className="border-b">
          <button
            onClick={() => toggleSection('insights')}
            className="w-full p-4 flex items-center justify-between hover:bg-gray-50 transition-colors"
          >
            <div className="flex items-center space-x-2">
              <Lightbulb className="w-4 h-4 text-yellow-500" />
              <span className="font-medium">Agent Insights</span>
              {insights.length > 0 && (
                <span className="bg-yellow-100 text-yellow-800 text-xs px-2 py-1 rounded-full">
                  {insights.length}
                </span>
              )}
            </div>
            {expandedSections.has('insights') ? (
              <ChevronUp className="w-4 h-4" />
            ) : (
              <ChevronDown className="w-4 h-4" />
            )}
          </button>

          {expandedSections.has('insights') && (
            <div className="px-4 pb-4">
              {insights.length === 0 ? (
                <div className="text-center py-6 text-gray-500">
                  <Lightbulb className="w-8 h-8 mx-auto mb-2 text-gray-400" />
                  <p className="text-sm">AI agents are analyzing your dependencies and will provide insights here.</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {insights.map((insight: unknown, index: number) => (
                    <div key={index} className="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
                      <div className="flex items-start space-x-2">
                        <Lightbulb className="w-4 h-4 text-yellow-600 mt-0.5" />
                        <div className="flex-1">
                          <h5 className="font-medium text-yellow-900">{insight.title}</h5>
                          <p className="text-sm text-yellow-800 mt-1">{insight.description}</p>
                          {insight.confidence && (
                            <span className="text-xs text-yellow-600 mt-2 block">
                              Confidence: {insight.confidence}
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Progressive Intelligence Controls */}
        <div className="p-4">
          <div className="flex items-center justify-between mb-3">
            <h4 className="font-medium text-gray-900">Progressive Intelligence</h4>
            <select
              value={activeAgent}
              onChange={(e) => setActiveAgent(e.target.value)}
              className="text-sm border border-gray-300 rounded px-2 py-1"
            >
              <option value="dependency_analysis_agent">Dependency Analysis</option>
              <option value="asset_inventory_agent">Asset Inventory</option>
              <option value="tech_debt_analysis_agent">Tech Debt Analysis</option>
            </select>
          </div>

          <div className="grid grid-cols-2 gap-2">
            <button
              onClick={() => handleThink(activeAgent)}
              disabled={thinkMutation.isPending}
              className="flex items-center justify-center space-x-2 px-3 py-2 bg-blue-100 hover:bg-blue-200 text-blue-700 rounded-md transition-colors disabled:opacity-50"
            >
              {thinkMutation.isPending ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Brain className="w-4 h-4" />
              )}
              <span className="text-sm">Think</span>
            </button>

            <button
              onClick={() => handlePonderMore(activeAgent)}
              disabled={ponderMutation.isPending}
              className="flex items-center justify-center space-x-2 px-3 py-2 bg-purple-100 hover:bg-purple-200 text-purple-700 rounded-md transition-colors disabled:opacity-50"
            >
              {ponderMutation.isPending ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Users className="w-4 h-4" />
              )}
              <span className="text-sm">Ponder More</span>
            </button>
          </div>

          <p className="text-xs text-gray-500 mt-2 text-center">
            Use "Think" for deeper analysis or "Ponder More" for crew collaboration
          </p>
        </div>
      </div>
    </div>
  );
};

export default AgentUIMonitor;
