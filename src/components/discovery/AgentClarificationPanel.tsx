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
  RefreshCw,
  Server,
  Database,
  Globe,
  MapPin,
  User as UserIcon,
  Building,
  Shield,
  Cpu,
  HardDrive,
  Monitor,
  Info
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

interface AssetDetails {
  id?: string;
  name: string;
  asset_type: string;
  hostname?: string;
  ip_address?: string;
  operating_system?: string;
  environment?: string;
  business_criticality?: string;
  department?: string;
  business_owner?: string;
  technical_owner?: string;
  description?: string;
  cpu_cores?: number;
  memory_gb?: number;
  storage_gb?: number;
  location?: string;
  datacenter?: string;
}

interface AgentClarificationPanelProps {
  pageContext: string;
  onQuestionAnswered?: (questionId: string, response: any) => void;
  className?: string;
  refreshTrigger?: number; // Increment this to trigger a refresh
  isProcessing?: boolean; // Set to true when background processing is happening
}

const AgentClarificationPanel: React.FC<AgentClarificationPanelProps> = ({
  pageContext,
  onQuestionAnswered,
  className = "",
  refreshTrigger,
  isProcessing = false
}) => {
  const [questions, setQuestions] = useState<AgentQuestion[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [expandedQuestion, setExpandedQuestion] = useState<string | null>(null);
  const [expandedAssetDetails, setExpandedAssetDetails] = useState<Set<string>>(new Set());
  const [responses, setResponses] = useState<Record<string, string>>({});
  const [isSubmitting, setIsSubmitting] = useState<Record<string, boolean>>({});
  const [error, setError] = useState<string | null>(null);
  const [assetDetails, setAssetDetails] = useState<Record<string, AssetDetails>>({});

  useEffect(() => {
    fetchQuestions();
  }, [pageContext]);

  // Refresh when refreshTrigger changes
  useEffect(() => {
    if (refreshTrigger !== undefined) {
      fetchQuestions();
    }
  }, [refreshTrigger]);

  // Set up polling only when processing is active
  useEffect(() => {
    let interval: NodeJS.Timeout | null = null;
    
    if (isProcessing) {
      interval = setInterval(fetchQuestions, 30000); // Poll every 30 seconds only when processing
    }
    
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [isProcessing]);

  const fetchQuestions = async () => {
    try {
      const result = await apiCall(API_CONFIG.ENDPOINTS.DISCOVERY.AGENT_STATUS, {
        method: 'GET',
        params: { page_context: pageContext }
      });
      if (result.status === 'success' && result.page_data?.pending_questions) {
        const questions = result.page_data.pending_questions;
        setQuestions(questions);
        
        // Fetch asset details for application boundary questions
        await fetchAssetDetailsForQuestions(questions);
      }
      setError(null);
    } catch (err: any) {
      // Handle 404 errors gracefully - these endpoints may not exist yet
      if (err.status === 404 || err.response?.status === 404) {
        console.log('Agent questions endpoint not available yet');
        setQuestions([]);
        setError(null);
      } else {
        console.error('Error fetching agent questions:', err);
        setError('Failed to load agent questions');
      }
    } finally {
      setIsLoading(false);
    }
  };

  const fetchAssetDetailsForQuestions = async (questions: AgentQuestion[]) => {
    const assetDetailsMap: Record<string, AssetDetails> = {};
    
    for (const question of questions) {
      if (question.question_type === 'application_boundary' && question.context?.components) {
        for (const componentName of question.context.components) {
          if (!assetDetailsMap[componentName]) {
            try {
              // Try to fetch asset details by name
              const assetResponse = await apiCall(`${API_CONFIG.ENDPOINTS.DISCOVERY.ASSETS}?search=${encodeURIComponent(componentName)}&page_size=1`, {
                method: 'GET'
              });
              
              if (assetResponse.assets && assetResponse.assets.length > 0) {
                const asset = assetResponse.assets[0];
                assetDetailsMap[componentName] = {
                  id: asset.id,
                  name: asset.name || asset.asset_name || componentName,
                  asset_type: asset.asset_type || asset.intelligent_asset_type || 'Unknown',
                  hostname: asset.hostname,
                  ip_address: asset.ip_address,
                  operating_system: asset.operating_system,
                  environment: asset.environment,
                  business_criticality: asset.business_criticality,
                  department: asset.department,
                  business_owner: asset.business_owner,
                  technical_owner: asset.technical_owner,
                  description: asset.description,
                  cpu_cores: asset.cpu_cores,
                  memory_gb: asset.memory_gb,
                  storage_gb: asset.storage_gb,
                  location: asset.location || asset.datacenter,
                  datacenter: asset.datacenter
                };
              } else {
                // Create a placeholder with the component name
                assetDetailsMap[componentName] = {
                  name: componentName,
                  asset_type: 'Unknown',
                  description: 'Asset details not found in inventory'
                };
              }
            } catch (err) {
              console.warn(`Failed to fetch details for asset ${componentName}:`, err);
              assetDetailsMap[componentName] = {
                name: componentName,
                asset_type: 'Unknown',
                description: 'Unable to fetch asset details'
              };
            }
          }
        }
      }
    }
    
    setAssetDetails(assetDetailsMap);
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

  const toggleAssetDetails = (componentName: string) => {
    setExpandedAssetDetails(prev => {
      const next = new Set(prev);
      if (next.has(componentName)) {
        next.delete(componentName);
      } else {
        next.add(componentName);
      }
      return next;
    });
  };

  const renderAssetCard = (componentName: string) => {
    const asset = assetDetails[componentName];
    if (!asset) return null;

    const isExpanded = expandedAssetDetails.has(componentName);

    return (
      <div key={componentName} className="border rounded-lg bg-gray-50 overflow-hidden">
        <div 
          className="p-3 cursor-pointer hover:bg-gray-100 transition-colors"
          onClick={() => toggleAssetDetails(componentName)}
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="flex items-center space-x-2">
                {asset.asset_type?.toLowerCase() === 'server' && <Server className="w-4 h-4 text-blue-600" />}
                {asset.asset_type?.toLowerCase() === 'database' && <Database className="w-4 h-4 text-green-600" />}
                {asset.asset_type?.toLowerCase() === 'application' && <Globe className="w-4 h-4 text-purple-600" />}
                {!['server', 'database', 'application'].includes(asset.asset_type?.toLowerCase() || '') && <Monitor className="w-4 h-4 text-gray-600" />}
                <span className="font-medium text-gray-900">{asset.name}</span>
              </div>
              <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded-full">
                {asset.asset_type}
              </span>
              {asset.environment && (
                <span className="text-xs bg-green-100 text-green-800 px-2 py-1 rounded-full">
                  {asset.environment}
                </span>
              )}
            </div>
            {isExpanded ? (
              <ChevronUp className="w-4 h-4 text-gray-500" />
            ) : (
              <ChevronDown className="w-4 h-4 text-gray-500" />
            )}
          </div>
          
          {/* Brief summary when collapsed */}
          {!isExpanded && (
            <div className="mt-2 text-sm text-gray-600 space-y-1">
              {asset.hostname && (
                <div>🖥️ <span className="font-medium">Hostname:</span> {asset.hostname}</div>
              )}
              {asset.ip_address && (
                <div>🌐 <span className="font-medium">IP:</span> {asset.ip_address}</div>
              )}
              {asset.operating_system && (
                <div>💾 <span className="font-medium">OS:</span> {asset.operating_system}</div>
              )}
            </div>
          )}
        </div>

        {/* Expanded details */}
        {isExpanded && (
          <div className="border-t bg-white p-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Technical Details */}
              <div>
                <h5 className="font-medium text-gray-900 mb-3 flex items-center">
                  <Cpu className="w-4 h-4 mr-2 text-blue-600" />
                  Technical Details
                </h5>
                <div className="space-y-2 text-sm">
                  {asset.hostname && (
                    <div className="flex items-start">
                      <span className="w-20 text-gray-600">Hostname:</span>
                      <span className="font-medium">{asset.hostname}</span>
                    </div>
                  )}
                  {asset.ip_address && (
                    <div className="flex items-start">
                      <span className="w-20 text-gray-600">IP Address:</span>
                      <span className="font-medium">{asset.ip_address}</span>
                    </div>
                  )}
                  {asset.operating_system && (
                    <div className="flex items-start">
                      <span className="w-20 text-gray-600">OS:</span>
                      <span className="font-medium">{asset.operating_system}</span>
                    </div>
                  )}
                  {asset.cpu_cores && (
                    <div className="flex items-start">
                      <span className="w-20 text-gray-600">CPU Cores:</span>
                      <span className="font-medium">{asset.cpu_cores}</span>
                    </div>
                  )}
                  {asset.memory_gb && (
                    <div className="flex items-start">
                      <span className="w-20 text-gray-600">Memory:</span>
                      <span className="font-medium">{asset.memory_gb} GB</span>
                    </div>
                  )}
                  {asset.storage_gb && (
                    <div className="flex items-start">
                      <span className="w-20 text-gray-600">Storage:</span>
                      <span className="font-medium">{asset.storage_gb} GB</span>
                    </div>
                  )}
                </div>
              </div>

              {/* Business Details */}
              <div>
                <h5 className="font-medium text-gray-900 mb-3 flex items-center">
                  <Building className="w-4 h-4 mr-2 text-green-600" />
                  Business Details
                </h5>
                <div className="space-y-2 text-sm">
                  {asset.department && (
                    <div className="flex items-start">
                      <span className="w-24 text-gray-600">Department:</span>
                      <span className="font-medium">{asset.department}</span>
                    </div>
                  )}
                  {asset.business_criticality && (
                    <div className="flex items-start">
                      <span className="w-24 text-gray-600">Criticality:</span>
                      <span className={`font-medium ${
                        asset.business_criticality?.toLowerCase() === 'critical' ? 'text-red-600' :
                        asset.business_criticality?.toLowerCase() === 'high' ? 'text-orange-600' :
                        asset.business_criticality?.toLowerCase() === 'medium' ? 'text-yellow-600' :
                        'text-green-600'
                      }`}>
                        {asset.business_criticality}
                      </span>
                    </div>
                  )}
                  {asset.business_owner && (
                    <div className="flex items-start">
                      <span className="w-24 text-gray-600">Bus. Owner:</span>
                      <span className="font-medium">{asset.business_owner}</span>
                    </div>
                  )}
                  {asset.technical_owner && (
                    <div className="flex items-start">
                      <span className="w-24 text-gray-600">Tech Owner:</span>
                      <span className="font-medium">{asset.technical_owner}</span>
                    </div>
                  )}
                  {asset.location && (
                    <div className="flex items-start">
                      <span className="w-24 text-gray-600">Location:</span>
                      <span className="font-medium">{asset.location}</span>
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* Description */}
            {asset.description && (
              <div className="mt-4 pt-4 border-t">
                <h5 className="font-medium text-gray-900 mb-2 flex items-center">
                  <Info className="w-4 h-4 mr-2 text-gray-600" />
                  Description
                </h5>
                <p className="text-sm text-gray-600">{asset.description}</p>
              </div>
            )}
          </div>
        )}
      </div>
    );
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

                {/* Enhanced Asset Context for Application Boundary Questions */}
                {question.question_type === 'application_boundary' && question.context?.components && (
                  <div className="mb-4">
                    <h5 className="font-medium text-gray-900 mb-3 flex items-center">
                      <Server className="w-4 h-4 mr-2 text-blue-600" />
                      Asset Details ({question.context.components.length} component{question.context.components.length !== 1 ? 's' : ''})
                    </h5>
                    <div className="space-y-3">
                      {question.context.components.map((componentName: string) => renderAssetCard(componentName))}
                    </div>
                    {question.context.reason && (
                      <div className="mt-3 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
                        <div className="flex items-start space-x-2">
                          <AlertCircle className="w-5 h-5 text-yellow-600 mt-0.5" />
                          <div>
                            <span className="font-medium text-yellow-800">Agent Analysis: </span>
                            <span className="text-yellow-700">{question.context.reason}</span>
                            {question.context.confidence && (
                              <span className="block text-sm text-yellow-600 mt-1">
                                Confidence: {Math.round(question.context.confidence * 100)}%
                              </span>
                            )}
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                )}

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
                {question.context && Object.keys(question.context).length > 0 && question.question_type !== 'application_boundary' && (
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

                {expandedQuestion === question.id && question.context && question.question_type !== 'application_boundary' && (
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