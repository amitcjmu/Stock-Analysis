/**
 * Agent Interaction Context - Global state management for agent interactions
 * 
 * Manages cross-page agent clarification state, data classification preservation,
 * agent learning context, and real-time updates across all discovery pages.
 */

import React, { createContext, useContext, useReducer, useCallback, useEffect, useRef } from 'react';
import { API_CONFIG } from '../config/api';

// Types and Interfaces
interface AgentQuestion {
  id: string;
  agent_name: string;
  question_text: string;
  question_type: string;
  context: Record<string, any>;
  priority: number;
  page_context: string;
  created_at: string;
  requires_response: boolean;
  suggested_answers?: string[];
  asset_context?: any;
}

interface AgentResponse {
  question_id: string;
  response: any;
  confidence: number;
  page_context: string;
  timestamp: string;
  user_notes?: string;
}

interface DataClassification {
  classification_id: string;
  asset_id?: string;
  field_name?: string;
  classification_type: string;
  classification_value: string;
  confidence: number;
  agent_name: string;
  page_context: string;
  evidence: Record<string, any>;
  user_validated: boolean;
  validation_timestamp?: string;
}

interface AgentInsight {
  insight_id: string;
  agent_name: string;
  insight_type: string;
  insight_text: string;
  confidence: number;
  page_context: string;
  supporting_data: Record<string, any>;
  actionable: boolean;
  business_impact: string;
  created_at: string;
  user_feedback?: 'helpful' | 'not_helpful' | 'incorrect';
}

interface CrossPageContext {
  context_id: string;
  context_type: string;
  context_data: Record<string, any>;
  participating_pages: string[];
  created_at: string;
  expires_at?: string;
}

interface AgentLearningContext {
  learning_session_id: string;
  user_corrections: AgentResponse[];
  pattern_recognitions: Record<string, any>;
  improvement_metrics: {
    accuracy_improvement: number;
    response_quality: number;
    user_satisfaction: number;
  };
  learning_domains: string[];
}

interface AgentState {
  questions: AgentQuestion[];
  responses: AgentResponse[];
  classifications: DataClassification[];
  insights: AgentInsight[];
  cross_page_contexts: CrossPageContext[];
  learning_context: AgentLearningContext | null;
  loading: {
    questions: boolean;
    responses: boolean;
    classifications: boolean;
    insights: boolean;
  };
  error: string | null;
  real_time_updates: {
    enabled: boolean;
    last_update: string | null;
    update_count: number;
  };
  page_specific_state: Record<string, any>;
}

// Action Types
type AgentAction =
  | { type: 'SET_LOADING'; payload: { section: keyof AgentState['loading']; loading: boolean } }
  | { type: 'SET_ERROR'; payload: string | null }
  | { type: 'ADD_QUESTION'; payload: AgentQuestion }
  | { type: 'UPDATE_QUESTION'; payload: { questionId: string; updates: Partial<AgentQuestion> } }
  | { type: 'REMOVE_QUESTION'; payload: string }
  | { type: 'ADD_RESPONSE'; payload: AgentResponse }
  | { type: 'ADD_CLASSIFICATION'; payload: DataClassification }
  | { type: 'UPDATE_CLASSIFICATION'; payload: { classificationId: string; updates: Partial<DataClassification> } }
  | { type: 'ADD_INSIGHT'; payload: AgentInsight }
  | { type: 'UPDATE_INSIGHT'; payload: { insightId: string; updates: Partial<AgentInsight> } }
  | { type: 'ADD_CROSS_PAGE_CONTEXT'; payload: CrossPageContext }
  | { type: 'REMOVE_CROSS_PAGE_CONTEXT'; payload: string }
  | { type: 'UPDATE_LEARNING_CONTEXT'; payload: Partial<AgentLearningContext> }
  | { type: 'SET_PAGE_STATE'; payload: { page: string; state: any } }
  | { type: 'CLEAR_PAGE_STATE'; payload: string }
  | { type: 'REAL_TIME_UPDATE'; payload: { type: string; data: any } }
  | { type: 'RESET_STATE' };

// Initial State
const initialState: AgentState = {
  questions: [],
  responses: [],
  classifications: [],
  insights: [],
  cross_page_contexts: [],
  learning_context: null,
  loading: {
    questions: false,
    responses: false,
    classifications: false,
    insights: false,
  },
  error: null,
  real_time_updates: {
    enabled: false,
    last_update: null,
    update_count: 0,
  },
  page_specific_state: {},
};

// Reducer
function agentReducer(state: AgentState, action: AgentAction): AgentState {
  switch (action.type) {
    case 'SET_LOADING':
      return {
        ...state,
        loading: {
          ...state.loading,
          [action.payload.section]: action.payload.loading,
        },
      };

    case 'SET_ERROR':
      return {
        ...state,
        error: action.payload,
      };

    case 'ADD_QUESTION':
      return {
        ...state,
        questions: [...state.questions, action.payload],
      };

    case 'UPDATE_QUESTION':
      return {
        ...state,
        questions: state.questions.map(q =>
          q.id === action.payload.questionId
            ? { ...q, ...action.payload.updates }
            : q
        ),
      };

    case 'REMOVE_QUESTION':
      return {
        ...state,
        questions: state.questions.filter(q => q.id !== action.payload),
      };

    case 'ADD_RESPONSE':
      return {
        ...state,
        responses: [...state.responses, action.payload],
      };

    case 'ADD_CLASSIFICATION':
      return {
        ...state,
        classifications: [...state.classifications, action.payload],
      };

    case 'UPDATE_CLASSIFICATION':
      return {
        ...state,
        classifications: state.classifications.map(c =>
          c.classification_id === action.payload.classificationId
            ? { ...c, ...action.payload.updates }
            : c
        ),
      };

    case 'ADD_INSIGHT':
      return {
        ...state,
        insights: [...state.insights, action.payload],
      };

    case 'UPDATE_INSIGHT':
      return {
        ...state,
        insights: state.insights.map(i =>
          i.insight_id === action.payload.insightId
            ? { ...i, ...action.payload.updates }
            : i
        ),
      };

    case 'ADD_CROSS_PAGE_CONTEXT':
      return {
        ...state,
        cross_page_contexts: [...state.cross_page_contexts, action.payload],
      };

    case 'REMOVE_CROSS_PAGE_CONTEXT':
      return {
        ...state,
        cross_page_contexts: state.cross_page_contexts.filter(
          c => c.context_id !== action.payload
        ),
      };

    case 'UPDATE_LEARNING_CONTEXT':
      return {
        ...state,
        learning_context: state.learning_context
          ? { ...state.learning_context, ...action.payload }
          : action.payload as AgentLearningContext,
      };

    case 'SET_PAGE_STATE':
      return {
        ...state,
        page_specific_state: {
          ...state.page_specific_state,
          [action.payload.page]: action.payload.state,
        },
      };

    case 'CLEAR_PAGE_STATE':
      const { [action.payload]: removed, ...remainingPageState } = state.page_specific_state;
      return {
        ...state,
        page_specific_state: remainingPageState,
      };

    case 'REAL_TIME_UPDATE':
      return {
        ...state,
        real_time_updates: {
          ...state.real_time_updates,
          last_update: new Date().toISOString(),
          update_count: state.real_time_updates.update_count + 1,
        },
      };

    case 'RESET_STATE':
      return initialState;

    default:
      return state;
  }
}

// Context
interface AgentInteractionContextType {
  state: AgentState;
  
  // Question Management
  addQuestion: (question: Omit<AgentQuestion, 'id' | 'created_at'>) => Promise<string>;
  updateQuestion: (questionId: string, updates: Partial<AgentQuestion>) => void;
  removeQuestion: (questionId: string) => void;
  getQuestionsForPage: (page: string) => AgentQuestion[];
  getPendingQuestions: () => AgentQuestion[];
  
  // Response Management
  submitResponse: (questionId: string, response: any, confidence?: number, notes?: string) => Promise<boolean>;
  getResponsesForQuestion: (questionId: string) => AgentResponse[];
  
  // Classification Management
  addClassification: (classification: Omit<DataClassification, 'classification_id'>) => void;
  updateClassification: (classificationId: string, updates: Partial<DataClassification>) => void;
  validateClassification: (classificationId: string, isValid: boolean) => void;
  getClassificationsForPage: (page: string) => DataClassification[];
  
  // Insight Management
  addInsight: (insight: Omit<AgentInsight, 'insight_id' | 'created_at'>) => void;
  updateInsight: (insightId: string, updates: Partial<AgentInsight>) => void;
  provideFeedback: (insightId: string, feedback: 'helpful' | 'not_helpful' | 'incorrect') => Promise<boolean>;
  getInsightsForPage: (page: string) => AgentInsight[];
  
  // Cross-Page Context Management
  createCrossPageContext: (contextType: string, contextData: any, pages: string[]) => Promise<string>;
  addPageToContext: (contextId: string, page: string) => void;
  removeCrossPageContext: (contextId: string) => void;
  getCrossPageContexts: (page?: string) => CrossPageContext[];
  
  // Learning Context Management
  updateLearningContext: (updates: Partial<AgentLearningContext>) => void;
  recordUserCorrection: (questionId: string, originalAnswer: any, correctedAnswer: any) => Promise<boolean>;
  getLearningProgress: () => AgentLearningContext | null;
  
  // Page State Management
  setPageState: (page: string, state: any) => void;
  getPageState: (page: string) => any;
  clearPageState: (page: string) => void;
  preserveStateForNavigation: (fromPage: string, toPage: string, sharedData: any) => void;
  
  // Real-time Updates
  enableRealTimeUpdates: () => void;
  disableRealTimeUpdates: () => void;
  getUpdateStatus: () => typeof initialState.real_time_updates;
  
  // Utility Functions
  clearError: () => void;
  resetContext: () => void;
  exportState: () => AgentState;
  importState: (state: Partial<AgentState>) => void;
}

const AgentInteractionContext = createContext<AgentInteractionContextType | undefined>(undefined);

// Provider Component
interface AgentInteractionProviderProps {
  children: React.ReactNode;
  clientAccountId?: number;
  engagementId?: string;
}

export const AgentInteractionProvider: React.FC<AgentInteractionProviderProps> = ({
  children,
  clientAccountId,
  engagementId,
}) => {
  const [state, dispatch] = useReducer(agentReducer, initialState);
  const webSocketRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Question Management
  const addQuestion = useCallback(async (questionData: Omit<AgentQuestion, 'id' | 'created_at'>) => {
    const questionId = `q_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    const question: AgentQuestion = {
      ...questionData,
      id: questionId,
      created_at: new Date().toISOString(),
    };

    dispatch({ type: 'ADD_QUESTION', payload: question });

    // Optionally send to backend
    try {
      await fetch(`${API_CONFIG.BASE_URL}/api/v1/discovery/agents/agent-clarification`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          question_id: questionId,
          agent_name: questionData.agent_name,
          question_data: questionData,
          client_account_id: clientAccountId,
          engagement_id: engagementId,
        }),
      });
    } catch (error) {
      console.error('Error sending question to backend:', error);
    }

    return questionId;
  }, [clientAccountId, engagementId]);

  const updateQuestion = useCallback((questionId: string, updates: Partial<AgentQuestion>) => {
    dispatch({ type: 'UPDATE_QUESTION', payload: { questionId, updates } });
  }, []);

  const removeQuestion = useCallback((questionId: string) => {
    dispatch({ type: 'REMOVE_QUESTION', payload: questionId });
  }, []);

  const getQuestionsForPage = useCallback((page: string) => {
    return state.questions.filter(q => q.page_context === page);
  }, [state.questions]);

  const getPendingQuestions = useCallback(() => {
    return state.questions.filter(q => q.requires_response && !state.responses.some(r => r.question_id === q.id));
  }, [state.questions, state.responses]);

  // Response Management
  const submitResponse = useCallback(async (
    questionId: string,
    response: any,
    confidence: number = 0.8,
    notes?: string
  ) => {
    const responseData: AgentResponse = {
      question_id: questionId,
      response,
      confidence,
      page_context: state.questions.find(q => q.id === questionId)?.page_context || '',
      timestamp: new Date().toISOString(),
      user_notes: notes,
    };

    dispatch({ type: 'ADD_RESPONSE', payload: responseData });

    // Send to backend for agent learning
    try {
      await fetch(`${API_CONFIG.BASE_URL}/api/v1/discovery/agents/agent-learning`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          question_id: questionId,
          response_data: responseData,
          client_account_id: clientAccountId,
          engagement_id: engagementId,
        }),
      });
      return true;
    } catch (error) {
      console.error('Error submitting response:', error);
      return false;
    }
  }, [state.questions, clientAccountId, engagementId]);

  const getResponsesForQuestion = useCallback((questionId: string) => {
    return state.responses.filter(r => r.question_id === questionId);
  }, [state.responses]);

  // Classification Management
  const addClassification = useCallback((classificationData: Omit<DataClassification, 'classification_id'>) => {
    const classificationId = `c_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    const classification: DataClassification = {
      ...classificationData,
      classification_id: classificationId,
    };

    dispatch({ type: 'ADD_CLASSIFICATION', payload: classification });
  }, []);

  const updateClassification = useCallback((classificationId: string, updates: Partial<DataClassification>) => {
    dispatch({ type: 'UPDATE_CLASSIFICATION', payload: { classificationId, updates } });
  }, []);

  const validateClassification = useCallback((classificationId: string, isValid: boolean) => {
    updateClassification(classificationId, {
      user_validated: isValid,
      validation_timestamp: new Date().toISOString(),
    });
  }, [updateClassification]);

  const getClassificationsForPage = useCallback((page: string) => {
    return state.classifications.filter(c => c.page_context === page);
  }, [state.classifications]);

  // Insight Management
  const addInsight = useCallback((insightData: Omit<AgentInsight, 'insight_id' | 'created_at'>) => {
    const insightId = `i_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    const insight: AgentInsight = {
      ...insightData,
      insight_id: insightId,
      created_at: new Date().toISOString(),
    };

    dispatch({ type: 'ADD_INSIGHT', payload: insight });
  }, []);

  const updateInsight = useCallback((insightId: string, updates: Partial<AgentInsight>) => {
    dispatch({ type: 'UPDATE_INSIGHT', payload: { insightId, updates } });
  }, []);

  const provideFeedback = useCallback(async (
    insightId: string,
    feedback: 'helpful' | 'not_helpful' | 'incorrect'
  ) => {
    updateInsight(insightId, { user_feedback: feedback });

    // Send feedback to backend for agent improvement
    try {
      await fetch(`${API_CONFIG.BASE_URL}/api/v1/discovery/agents/agent-learning`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          insight_id: insightId,
          feedback,
          client_account_id: clientAccountId,
          engagement_id: engagementId,
        }),
      });
      return true;
    } catch (error) {
      console.error('Error providing feedback:', error);
      return false;
    }
  }, [updateInsight, clientAccountId, engagementId]);

  const getInsightsForPage = useCallback((page: string) => {
    return state.insights.filter(i => i.page_context === page);
  }, [state.insights]);

  // Cross-Page Context Management
  const createCrossPageContext = useCallback(async (
    contextType: string,
    contextData: any,
    pages: string[]
  ) => {
    const contextId = `ctx_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    const context: CrossPageContext = {
      context_id: contextId,
      context_type: contextType,
      context_data: contextData,
      participating_pages: pages,
      created_at: new Date().toISOString(),
      expires_at: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString(), // 24 hours
    };

    dispatch({ type: 'ADD_CROSS_PAGE_CONTEXT', payload: context });
    return contextId;
  }, []);

  const addPageToContext = useCallback((contextId: string, page: string) => {
    const context = state.cross_page_contexts.find(c => c.context_id === contextId);
    if (context && !context.participating_pages.includes(page)) {
      const updatedContext = {
        ...context,
        participating_pages: [...context.participating_pages, page],
      };
      // This would require a more complex update mechanism in real implementation
    }
  }, [state.cross_page_contexts]);

  const removeCrossPageContext = useCallback((contextId: string) => {
    dispatch({ type: 'REMOVE_CROSS_PAGE_CONTEXT', payload: contextId });
  }, []);

  const getCrossPageContexts = useCallback((page?: string) => {
    if (page) {
      return state.cross_page_contexts.filter(c => c.participating_pages.includes(page));
    }
    return state.cross_page_contexts;
  }, [state.cross_page_contexts]);

  // Learning Context Management
  const updateLearningContext = useCallback((updates: Partial<AgentLearningContext>) => {
    dispatch({ type: 'UPDATE_LEARNING_CONTEXT', payload: updates });
  }, []);

  const recordUserCorrection = useCallback(async (
    questionId: string,
    originalAnswer: any,
    correctedAnswer: any
  ) => {
    const correction: AgentResponse = {
      question_id: questionId,
      response: {
        type: 'correction',
        original: originalAnswer,
        corrected: correctedAnswer,
      },
      confidence: 1.0,
      page_context: state.questions.find(q => q.id === questionId)?.page_context || '',
      timestamp: new Date().toISOString(),
    };

    dispatch({ type: 'ADD_RESPONSE', payload: correction });

    // Update learning context
    if (state.learning_context) {
      updateLearningContext({
        user_corrections: [...state.learning_context.user_corrections, correction],
      });
    }

    // Send to backend
    try {
      await fetch(`${API_CONFIG.BASE_URL}/api/v1/discovery/agents/agent-learning`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          type: 'user_correction',
          question_id: questionId,
          correction_data: correction,
          client_account_id: clientAccountId,
          engagement_id: engagementId,
        }),
      });
      return true;
    } catch (error) {
      console.error('Error recording user correction:', error);
      return false;
    }
  }, [state.questions, state.learning_context, updateLearningContext, clientAccountId, engagementId]);

  const getLearningProgress = useCallback(() => {
    return state.learning_context;
  }, [state.learning_context]);

  // Page State Management
  const setPageState = useCallback((page: string, pageState: any) => {
    dispatch({ type: 'SET_PAGE_STATE', payload: { page, state: pageState } });
  }, []);

  const getPageState = useCallback((page: string) => {
    return state.page_specific_state[page];
  }, [state.page_specific_state]);

  const clearPageState = useCallback((page: string) => {
    dispatch({ type: 'CLEAR_PAGE_STATE', payload: page });
  }, []);

  const preserveStateForNavigation = useCallback((fromPage: string, toPage: string, sharedData: any) => {
    const fromState = getPageState(fromPage);
    const preservedData = {
      shared_from: fromPage,
      shared_data: sharedData,
      preserved_at: new Date().toISOString(),
      original_state: fromState,
    };
    setPageState(toPage, { ...getPageState(toPage), preserved_navigation: preservedData });
  }, [getPageState, setPageState]);

  // Real-time Updates
  const enableRealTimeUpdates = useCallback(() => {
    if (!webSocketRef.current || webSocketRef.current.readyState === WebSocket.CLOSED) {
      const wsUrl = `${API_CONFIG.BASE_URL.replace('http', 'ws')}/ws/agent-updates`;
      webSocketRef.current = new WebSocket(wsUrl);

      webSocketRef.current.onopen = () => {
        console.log('Agent updates WebSocket connected');
        dispatch({
          type: 'REAL_TIME_UPDATE',
          payload: { type: 'connection_status', data: { connected: true } },
        });
      };

      webSocketRef.current.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          dispatch({ type: 'REAL_TIME_UPDATE', payload: data });
          
          // Handle specific update types
          if (data.type === 'new_question') {
            dispatch({ type: 'ADD_QUESTION', payload: data.data });
          } else if (data.type === 'new_insight') {
            dispatch({ type: 'ADD_INSIGHT', payload: data.data });
          } else if (data.type === 'classification_update') {
            dispatch({ type: 'ADD_CLASSIFICATION', payload: data.data });
          }
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };

      webSocketRef.current.onclose = () => {
        console.log('Agent updates WebSocket disconnected');
        // Attempt to reconnect after 5 seconds
        reconnectTimeoutRef.current = setTimeout(() => {
          enableRealTimeUpdates();
        }, 5000);
      };

      webSocketRef.current.onerror = (error) => {
        console.error('WebSocket error:', error);
      };
    }
  }, []);

  const disableRealTimeUpdates = useCallback(() => {
    if (webSocketRef.current) {
      webSocketRef.current.close();
      webSocketRef.current = null;
    }
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
  }, []);

  const getUpdateStatus = useCallback(() => {
    return state.real_time_updates;
  }, [state.real_time_updates]);

  // Utility Functions
  const clearError = useCallback(() => {
    dispatch({ type: 'SET_ERROR', payload: null });
  }, []);

  const resetContext = useCallback(() => {
    dispatch({ type: 'RESET_STATE' });
  }, []);

  const exportState = useCallback(() => {
    return state;
  }, [state]);

  const importState = useCallback((importedState: Partial<AgentState>) => {
    // Merge imported state with current state
    Object.entries(importedState).forEach(([key, value]) => {
      if (key === 'questions' && Array.isArray(value)) {
        value.forEach(question => dispatch({ type: 'ADD_QUESTION', payload: question }));
      } else if (key === 'responses' && Array.isArray(value)) {
        value.forEach(response => dispatch({ type: 'ADD_RESPONSE', payload: response }));
      } else if (key === 'classifications' && Array.isArray(value)) {
        value.forEach(classification => dispatch({ type: 'ADD_CLASSIFICATION', payload: classification }));
      } else if (key === 'insights' && Array.isArray(value)) {
        value.forEach(insight => dispatch({ type: 'ADD_INSIGHT', payload: insight }));
      }
      // Add more import logic as needed
    });
  }, []);

  // Cleanup effect
  useEffect(() => {
    return () => {
      disableRealTimeUpdates();
    };
  }, [disableRealTimeUpdates]);

  // Context value
  const contextValue: AgentInteractionContextType = {
    state,
    
    // Question Management
    addQuestion,
    updateQuestion,
    removeQuestion,
    getQuestionsForPage,
    getPendingQuestions,
    
    // Response Management
    submitResponse,
    getResponsesForQuestion,
    
    // Classification Management
    addClassification,
    updateClassification,
    validateClassification,
    getClassificationsForPage,
    
    // Insight Management
    addInsight,
    updateInsight,
    provideFeedback,
    getInsightsForPage,
    
    // Cross-Page Context Management
    createCrossPageContext,
    addPageToContext,
    removeCrossPageContext,
    getCrossPageContexts,
    
    // Learning Context Management
    updateLearningContext,
    recordUserCorrection,
    getLearningProgress,
    
    // Page State Management
    setPageState,
    getPageState,
    clearPageState,
    preserveStateForNavigation,
    
    // Real-time Updates
    enableRealTimeUpdates,
    disableRealTimeUpdates,
    getUpdateStatus,
    
    // Utility Functions
    clearError,
    resetContext,
    exportState,
    importState,
  };

  return (
    <AgentInteractionContext.Provider value={contextValue}>
      {children}
    </AgentInteractionContext.Provider>
  );
};

// Hook for using the context
export const useAgentInteraction = () => {
  const context = useContext(AgentInteractionContext);
  if (context === undefined) {
    throw new Error('useAgentInteraction must be used within an AgentInteractionProvider');
  }
  return context;
};

// Export types for external use
export type {
  AgentQuestion,
  AgentResponse,
  DataClassification,
  AgentInsight,
  CrossPageContext,
  AgentLearningContext,
  AgentState,
  AgentInteractionContextType,
}; 