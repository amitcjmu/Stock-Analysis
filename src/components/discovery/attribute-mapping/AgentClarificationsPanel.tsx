import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Brain, CheckCircle, AlertCircle, Clock, MessageSquare } from 'lucide-react';
import { apiCall, API_CONFIG } from '../../../config/api';

interface AgentClarificationsPanelProps {
  className?: string;
}

interface ClarificationQuestion {
  id: string;
  agent_id: string;
  agent_name: string;
  question_type: string;
  page: string;
  title: string;
  question: string;
  options: string[];
  context: {
    source_field?: string;
    target_options?: string[];
    confidence?: number;
    sample_values?: string[];
    field_type?: string;
  };
  confidence: string;
  priority: string;
  created_at: string;
  is_resolved: boolean;
}

const AgentClarificationsPanel: React.FC<AgentClarificationsPanelProps> = ({ className = "" }) => {
  const [selectedAnswers, setSelectedAnswers] = useState<Record<string, string>>({});
  const [submittedQuestions, setSubmittedQuestions] = useState<Set<string>>(new Set());

  // 🤖 Fetch agent clarifications with MCQ format
  const { 
    data: clarificationsData, 
    isLoading, 
    error 
  } = useQuery({
    queryKey: ['agent-clarifications'],
    queryFn: async () => {
      const response = await apiCall(API_CONFIG.ENDPOINTS.DISCOVERY.AGENT_CLARIFICATIONS);
      return response;
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
    refetchInterval: 30 * 1000, // Refresh every 30 seconds for new questions
  });

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
      // Mock submission - in real app would send to backend
      console.log('Submitting answer:', { questionId, answer });
      
      // Mark as submitted
      setSubmittedQuestions(prev => new Set([...prev, questionId]));
      
      // Could trigger a refetch or update local state
      // await apiCall('/data-import/agent-clarifications/submit', {
      //   method: 'POST',
      //   body: JSON.stringify({ questionId, answer })
      // });
      
    } catch (error) {
      console.error('Failed to submit answer:', error);
    }
  };

  const questions = clarificationsData?.page_data?.pending_questions || [];
  const pendingQuestions = questions.filter((q: ClarificationQuestion) => !submittedQuestions.has(q.id));

  if (isLoading) {
    return (
      <div className={`bg-white rounded-lg border shadow-sm p-4 ${className}`}>
        <div className="flex items-center space-x-2 mb-4">
          <Brain className="w-5 h-5 text-purple-500 animate-pulse" />
          <h3 className="font-medium text-gray-900">Agent Clarifications</h3>
          <span className="text-sm text-gray-500">Loading...</span>
        </div>
      </div>
    );
  }

  if (error || !clarificationsData) {
    return (
      <div className={`bg-white rounded-lg border shadow-sm p-4 ${className}`}>
        <div className="flex items-center space-x-2 mb-4">
          <Brain className="w-5 h-5 text-purple-500" />
          <h3 className="font-medium text-gray-900">Agent Clarifications</h3>
          <span className="text-sm text-red-500">Error loading questions</span>
        </div>
      </div>
    );
  }

  return (
    <div className={`bg-white rounded-lg border shadow-sm ${className}`}>
      <div className="p-4 border-b">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Brain className="w-5 h-5 text-purple-500" />
            <h3 className="font-medium text-gray-900">Agent Clarifications</h3>
            <span className="text-sm text-gray-500">
              {pendingQuestions.length} pending
            </span>
          </div>
          {pendingQuestions.length > 0 && (
            <div className="flex items-center space-x-1 text-amber-600">
              <AlertCircle className="w-4 h-4" />
              <span className="text-sm font-medium">Needs attention</span>
            </div>
          )}
        </div>
      </div>

      <div className="p-4">
        {pendingQuestions.length === 0 ? (
          <div className="text-center py-8">
            <CheckCircle className="w-12 h-12 text-green-500 mx-auto mb-3" />
            <p className="text-gray-600">No pending clarifications</p>
            <p className="text-sm text-gray-500">All agent questions have been resolved</p>
          </div>
        ) : (
          <div className="space-y-6">
            {pendingQuestions.map((question: ClarificationQuestion) => (
              <div key={question.id} className="border rounded-lg p-4 bg-gray-50">
                <div className="flex items-start justify-between mb-3">
                  <div>
                    <h4 className="font-medium text-gray-900">{question.title}</h4>
                    <div className="flex items-center space-x-2 mt-1">
                      <span className="text-sm text-gray-500">{question.agent_name}</span>
                      <span className="text-xs px-2 py-1 bg-purple-100 text-purple-700 rounded">
                        {question.confidence} confidence
                      </span>
                      <span className={`text-xs px-2 py-1 rounded ${
                        question.priority === 'high' ? 'bg-red-100 text-red-700' :
                        question.priority === 'normal' ? 'bg-yellow-100 text-yellow-700' :
                        'bg-green-100 text-green-700'
                      }`}>
                        {question.priority} priority
                      </span>
                    </div>
                  </div>
                  <Clock className="w-4 h-4 text-gray-400" />
                </div>

                <p className="text-gray-700 mb-4">{question.question}</p>

                {/* Context Information */}
                {question.context && (
                  <div className="bg-blue-50 rounded-lg p-3 mb-4">
                    <h5 className="text-sm font-medium text-blue-900 mb-2">Context</h5>
                    <div className="text-sm text-blue-800 space-y-1">
                      {question.context.source_field && (
                        <div>Source Field: <span className="font-mono">{question.context.source_field}</span></div>
                      )}
                      {question.context.confidence && (
                        <div>AI Confidence: {Math.round(question.context.confidence * 100)}%</div>
                      )}
                      {question.context.sample_values && (
                        <div>Sample Values: {question.context.sample_values.join(', ')}</div>
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
                        className="w-4 h-4 text-purple-600 border-gray-300 focus:ring-purple-500"
                      />
                      <span className="text-sm text-gray-700">{option}</span>
                    </label>
                  ))}
                </div>

                {/* Submit Button */}
                <button
                  onClick={() => handleSubmitAnswer(question.id)}
                  disabled={!selectedAnswers[question.id]}
                  className={`w-full py-2 px-4 rounded-md text-sm font-medium transition-colors ${
                    selectedAnswers[question.id]
                      ? 'bg-purple-600 text-white hover:bg-purple-700'
                      : 'bg-gray-300 text-gray-500 cursor-not-allowed'
                  }`}
                >
                  Submit Answer
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default AgentClarificationsPanel;