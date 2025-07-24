/**
 * Agent Clarification Panel
 * 
 * Main panel component for displaying and managing agent questions.
 */

import React from 'react'
import { useState } from 'react'
import { useEffect } from 'react'
import type { AssetDetails, AgentClarificationPanelProps } from './types'
import type { AgentQuestion } from './types'
import * as api from './api';
import LoadingState from './LoadingState';
import ErrorState from './ErrorState';
import EmptyState from './EmptyState';
import PanelHeader from './PanelHeader';
import QuestionCard from './QuestionCard';
import ResolvedQuestionsList from './ResolvedQuestionsList';

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
      const fetchedQuestions = await api.fetchAgentQuestions(pageContext);
      setQuestions(fetchedQuestions);
      
      // Fetch asset details for application boundary questions
      await fetchAssetDetailsForQuestions(fetchedQuestions);
      setError(null);
    } catch (err: unknown) {
      setError(err.message);
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
            // For now, just create placeholder entries since the assets API doesn't exist yet
            // In the future, this should fetch from the actual inventory when it's available
            assetDetailsMap[componentName] = {
              name: componentName,
              asset_type: 'Server', // Default type
              description: 'Asset details will be available after inventory phase completion'
            };
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
      const success = await api.submitQuestionResponse(questionId, response, 'text', pageContext);

      if (success) {
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
    } catch (err: unknown) {
      setError(err.message);
    } finally {
      setIsSubmitting(prev => ({ ...prev, [questionId]: false }));
    }
  };

  const handleMultipleChoiceResponse = async (questionId: string, selectedOption: string) => {
    setIsSubmitting(prev => ({ ...prev, [questionId]: true }));

    try {
      const success = await api.submitQuestionResponse(questionId, selectedOption, 'selection', pageContext);

      if (success) {
        setQuestions(prev => prev.map(q => 
          q.id === questionId 
            ? { ...q, is_resolved: true, user_response: selectedOption, answered_at: new Date().toISOString() }
            : q
        ));
        
        onQuestionAnswered?.(questionId, selectedOption);
      }
    } catch (err: unknown) {
      setError(err.message);
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

  const handleToggleExpanded = (questionId: string) => {
    setExpandedQuestion(expandedQuestion === questionId ? null : questionId);
  };

  const handleResponseChange = (questionId: string, value: string) => {
    setResponses(prev => ({ ...prev, [questionId]: value }));
  };

  if (isLoading) {
    return <LoadingState className={className} />;
  }

  const pendingQuestions = questions.filter(q => !q.is_resolved);
  const resolvedQuestions = questions.filter(q => q.is_resolved);

  return (
    <div className={`bg-white rounded-lg border shadow-sm ${className}`}>
      <PanelHeader 
        pendingCount={pendingQuestions.length}
        onRefresh={fetchQuestions}
      />

      <div className="max-h-96 overflow-y-auto">
        {error && <ErrorState error={error} />}

        {pendingQuestions.length === 0 && resolvedQuestions.length === 0 && !error && (
          <EmptyState />
        )}

        {/* Pending Questions */}
        {pendingQuestions.map((question) => (
          <QuestionCard
            key={question.id}
            question={question}
            response={responses[question.id] || ''}
            isSubmitting={isSubmitting[question.id] || false}
            expandedQuestion={expandedQuestion}
            expandedAssetDetails={expandedAssetDetails}
            assetDetails={assetDetails}
            onResponseChange={handleResponseChange}
            onResponseSubmit={handleResponseSubmit}
            onMultipleChoiceResponse={handleMultipleChoiceResponse}
            onToggleExpanded={handleToggleExpanded}
            onToggleAssetDetails={toggleAssetDetails}
          />
        ))}

        <ResolvedQuestionsList resolvedQuestions={resolvedQuestions} />
      </div>
    </div>
  );
};

export default AgentClarificationPanel;