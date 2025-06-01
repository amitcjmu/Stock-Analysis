import React, { useState, useEffect } from 'react';
import { 
  MessageCircle, 
  Bot, 
  User, 
  Send, 
  ThumbsUp, 
  ThumbsDown, 
  AlertCircle, 
  CheckCircle, 
  Clock,
  Brain,
  Loader2,
  ChevronDown,
  ChevronUp,
  HelpCircle,
  RefreshCw
} from 'lucide-react';
import { apiCall, API_CONFIG } from '../../config/api';

interface AgentQuestion {
  id: string;
  agent_id: string;
  agent_name: string;
  question_type: string;
  page: string;
  title: string;
  question: string;
  context: any;
  options?: string[];
  confidence: string;
  priority: string;
  created_at: string;
  answered_at?: string;
  user_response?: any;
  is_resolved: boolean;
}

interface AgentClarificationPanelProps {
  pageContext: string;
  onQuestionAnswered?: (questionId: string, response: any) => void;
  className?: string;
}

const AgentClarificationPanel: React.FC<AgentClarificationPanelProps> = ({
  pageContext,
  onQuestionAnswered,
  className = ""
}) => {
  const [questions, setQuestions] = useState<AgentQuestion[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [expandedQuestion, setExpandedQuestion] = useState<string | null>(null);
  const [responses, setResponses] = useState<Record<string, string>>({});
  const [isSubmitting, setIsSubmitting] = useState<Record<string, boolean>>({});
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchQuestions();
    // Set up polling for new questions
    const interval = setInterval(fetchQuestions, 10000); // Poll every 10 seconds
    return () => clearInterval(interval);
  }, [pageContext]);

  const fetchQuestions = async () => {
    try {
              const result = await apiCall(`${API_CONFIG.ENDPOINTS.DISCOVERY.AGENT_STATUS}?page_context=${pageContext}`, {
        method: 'GET'
      });
      if (result.status === 'success' && result.page_data?.pending_questions) {
        setQuestions(result.page_data.pending_questions);
      }
      setError(null);
    } catch (err) {
      console.error('Error fetching agent questions:', err);
      setError('Failed to load agent questions');
    } finally {
      setIsLoading(false);
    }
  };

  const handleResponseSubmit = async (questionId: string) => {
    const response = responses[questionId];
    if (!response?.trim()) return;

    setIsSubmitting(prev => ({ ...prev, [questionId]: true }));

    try {
      const result = await apiCall(API_CONFIG.ENDPOINTS.DISCOVERY.AGENT_CLARIFICATION, {
        method: 'POST',
        body: JSON.stringify({
          question_id: questionId,
          response: response,
          response_type: 'text',
          page_context: pageContext
        })
      });

      if (result.status === 'success') {
        // Update the question as resolved
        setQuestions(prev => prev.map(q => 
          q.id === questionId 
            ? { ...q, is_resolved: true, user_response: response, answered_at: new Date().toISOString() }
            : q
        ));
        
        // Clear the response input
        setResponses(prev => ({ ...prev, [questionId]: '' }));
        
        // Notify parent component
        onQuestionAnswered?.(questionId, response);
      }
    } catch (err) {
      console.error('Error submitting response:', err);
      setError('Failed to submit response');
    } finally {
      setIsSubmitting(prev => ({ ...prev, [questionId]: false }));
    }
  };

  const handleMultipleChoiceResponse = async (questionId: string, selectedOption: string) => {
    setIsSubmitting(prev => ({ ...prev, [questionId]: true }));

    try {
      const result = await apiCall(API_CONFIG.ENDPOINTS.DISCOVERY.AGENT_CLARIFICATION, {
        method: 'POST',
        body: JSON.stringify({
          question_id: questionId,
          response: selectedOption,
          response_type: 'selection',
          page_context: pageContext
        })
      });

      if (result.status === 'success') {
        setQuestions(prev => prev.map(q => 
          q.id === questionId 
            ? { ...q, is_resolved: true, user_response: selectedOption, answered_at: new Date().toISOString() }
            : q
        ));
        
        onQuestionAnswered?.(questionId, selectedOption);
      }
    } catch (err) {
      console.error('Error submitting response:', err);
      setError('Failed to submit response');
    } finally {
      setIsSubmitting(prev => ({ ...prev, [questionId]: false }));
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high': return 'border-red-500 bg-red-50';
      case 'medium': return 'border-yellow-500 bg-yellow-50';
      case 'low': return 'border-green-500 bg-green-50';
      default: return 'border-gray-300 bg-gray-50';
    }
  };

  const getConfidenceIcon = (confidence: string) => {
    switch (confidence) {
      case 'high': return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'medium': return <AlertCircle className="w-4 h-4 text-yellow-500" />;
      case 'low': return <HelpCircle className="w-4 h-4 text-orange-500" />;
      case 'uncertain': return <AlertCircle className="w-4 h-4 text-red-500" />;
      default: return <HelpCircle className="w-4 h-4 text-gray-500" />;
    }
  };

  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  if (isLoading) {
    return (
      <div className={`bg-white rounded-lg border shadow-sm p-4 ${className}`}>
        <div className="flex items-center space-x-2 mb-4">
          <Bot className="w-5 h-5 text-blue-500" />
          <h3 className="font-medium text-gray-900">Agent Clarifications</h3>
        </div>
        <div className="flex items-center justify-center py-8">
          <Loader2 className="w-6 h-6 animate-spin text-blue-500" />
          <span className="ml-2 text-gray-600">Loading agent questions...</span>
        </div>
      </div>
    );
  }

  const pendingQuestions = questions.filter(q => !q.is_resolved);
  const resolvedQuestions = questions.filter(q => q.is_resolved);

  return (
    <div className={`bg-white rounded-lg border shadow-sm ${className}`}>
      <div className="p-4 border-b">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Bot className="w-5 h-5 text-blue-500" />
            <h3 className="font-medium text-gray-900">Agent Clarifications</h3>
            {pendingQuestions.length > 0 && (
              <span className="bg-red-100 text-red-800 text-xs font-medium px-2 py-1 rounded-full">
                {pendingQuestions.length} pending
              </span>
            )}
          </div>
          <button
            onClick={fetchQuestions}
            className="p-1 hover:bg-gray-100 rounded-full transition-colors"
            title="Refresh questions"
          >
            <RefreshCw className="w-4 h-4 text-gray-500" />
          </button>
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

        {pendingQuestions.length === 0 && resolvedQuestions.length === 0 && !error && (
          <div className="p-6 text-center text-gray-500">
            <Brain className="w-8 h-8 mx-auto mb-2 text-gray-400" />
            <p>No agent questions yet</p>
            <p className="text-sm mt-1">Agents will ask clarifications as they analyze your data</p>
          </div>
        )}

        {/* Pending Questions */}
        {pendingQuestions.map((question) => (
          <div
            key={question.id}
            className={`border-l-4 p-4 ${getPriorityColor(question.priority)}`}
          >
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <div className="flex items-center space-x-2 mb-2">
                  <span className="font-medium text-gray-900">{question.agent_name}</span>
                  {getConfidenceIcon(question.confidence)}
                  <span className="text-xs text-gray-500">
                    {formatTimestamp(question.created_at)}
                  </span>
                  <span className={`text-xs px-2 py-1 rounded-full ${
                    question.priority === 'high' ? 'bg-red-100 text-red-800' :
                    question.priority === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                    'bg-green-100 text-green-800'
                  }`}>
                    {question.priority} priority
                  </span>
                </div>
                
                <h4 className="font-medium text-gray-900 mb-2">{question.title}</h4>
                <p className="text-gray-700 mb-3">{question.question}</p>

                {/* Multiple Choice Options */}
                {question.options && question.options.length > 0 && (
                  <div className="space-y-2 mb-3">
                    {question.options.map((option, index) => (
                      <button
                        key={index}
                        onClick={() => handleMultipleChoiceResponse(question.id, option)}
                        disabled={isSubmitting[question.id]}
                        className="w-full text-left p-3 border border-gray-200 rounded-lg hover:bg-blue-50 hover:border-blue-300 transition-colors disabled:opacity-50"
                      >
                        {option}
                      </button>
                    ))}
                  </div>
                )}

                {/* Text Response Input */}
                {(!question.options || question.options.length === 0) && (
                  <div className="flex space-x-2">
                    <input
                      type="text"
                      value={responses[question.id] || ''}
                      onChange={(e) => setResponses(prev => ({ ...prev, [question.id]: e.target.value }))}
                      placeholder="Type your response..."
                      className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      onKeyPress={(e) => {
                        if (e.key === 'Enter') {
                          handleResponseSubmit(question.id);
                        }
                      }}
                    />
                    <button
                      onClick={() => handleResponseSubmit(question.id)}
                      disabled={isSubmitting[question.id] || !responses[question.id]?.trim()}
                      className="px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                    >
                      {isSubmitting[question.id] ? (
                        <Loader2 className="w-4 h-4 animate-spin" />
                      ) : (
                        <Send className="w-4 h-4" />
                      )}
                    </button>
                  </div>
                )}

                {/* Context Information */}
                {question.context && Object.keys(question.context).length > 0 && (
                  <button
                    onClick={() => setExpandedQuestion(
                      expandedQuestion === question.id ? null : question.id
                    )}
                    className="mt-3 flex items-center text-sm text-gray-600 hover:text-gray-800"
                  >
                    {expandedQuestion === question.id ? (
                      <ChevronUp className="w-4 h-4 mr-1" />
                    ) : (
                      <ChevronDown className="w-4 h-4 mr-1" />
                    )}
                    Show context
                  </button>
                )}

                {expandedQuestion === question.id && question.context && (
                  <div className="mt-2 p-3 bg-gray-50 rounded-md">
                    <pre className="text-xs text-gray-600 whitespace-pre-wrap">
                      {JSON.stringify(question.context, null, 2)}
                    </pre>
                  </div>
                )}
              </div>
            </div>
          </div>
        ))}

        {/* Resolved Questions */}
        {resolvedQuestions.length > 0 && (
          <div className="border-t border-gray-200">
            <div className="p-3 bg-gray-50">
              <h4 className="text-sm font-medium text-gray-700">Recently Resolved</h4>
            </div>
            {resolvedQuestions.slice(-3).map((question) => (
              <div key={question.id} className="p-4 border-b border-gray-100 bg-green-50">
                <div className="flex items-center space-x-2 mb-2">
                  <CheckCircle className="w-4 h-4 text-green-500" />
                  <span className="font-medium text-gray-700">{question.title}</span>
                  <span className="text-xs text-gray-500">
                    Resolved at {formatTimestamp(question.answered_at || '')}
                  </span>
                </div>
                <p className="text-sm text-gray-600 mb-1">{question.question}</p>
                <p className="text-sm font-medium text-green-700">
                  Response: {question.user_response}
                </p>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default AgentClarificationPanel; 