import React, { createContext, useContext, useState, useCallback, ReactNode } from 'react';
import { useNavigate } from 'react-router-dom';
import { FlowState } from '../types/discovery';

interface DiscoveryFlowContextType {
  flowState: FlowState | null;
  updateFlowState: (state: Partial<FlowState>) => void;
  navigateToNextPhase: (currentPhase: string) => void;
  navigateToPreviousPhase: (currentPhase: string) => void;
  getPhaseCompletion: (phase: string) => boolean;
}

const DiscoveryFlowContext = createContext<DiscoveryFlowContextType | null>(null);

export const useDiscoveryFlowState = () => {
  const context = useContext(DiscoveryFlowContext);
  if (!context) {
    throw new Error('useDiscoveryFlowState must be used within a DiscoveryFlowProvider');
  }
  return context;
};

interface DiscoveryFlowProviderProps {
  children: ReactNode;
}

export const DiscoveryFlowProvider: React.FC<DiscoveryFlowProviderProps> = ({ children }) => {
  const navigate = useNavigate();
  const [flowState, setFlowState] = useState<FlowState | null>({
    session_id: '',
    current_phase: 'inventory',
    next_phase: 'dependencies',
    previous_phase: '',
    phase_completion: {
      inventory: false,
      dependencies: false,
      data_cleansing: false,
      attribute_mapping: false
    },
    phase_data: {},
    crew_completion_status: {},
    agent_insights: {},
    agent_learning: {},
    agent_feedback: {},
    agent_clarifications: {},
    agent_recommendations: {},
    agent_warnings: {},
    agent_errors: {},
    agent_progress: {},
    agent_status: {},
    agent_memory: {},
    agent_context: {},
    agent_configuration: {},
    agent_orchestration: {},
    agent_monitoring: {},
    agent_metrics: {}
  });

  const updateFlowState = useCallback((state: Partial<FlowState>) => {
    setFlowState(prev => prev ? { ...prev, ...state } : null);
  }, []);

  const getPhaseCompletion = useCallback((phase: string) => {
    return flowState?.phase_completion[phase] || false;
  }, [flowState]);

  const getNextPhase = useCallback((currentPhase: string) => {
    switch (currentPhase) {
      case 'inventory':
        return 'dependencies';
      case 'dependencies':
        return 'data_cleansing';
      case 'data_cleansing':
        return 'attribute_mapping';
      case 'attribute_mapping':
        return '';
      default:
        return '';
    }
  }, []);

  const getPreviousPhase = useCallback((currentPhase: string) => {
    switch (currentPhase) {
      case 'dependencies':
        return 'inventory';
      case 'data_cleansing':
        return 'dependencies';
      case 'attribute_mapping':
        return 'data_cleansing';
      default:
        return '';
    }
  }, []);

  const navigateToNextPhase = useCallback((currentPhase: string) => {
    const nextPhase = getNextPhase(currentPhase);
    if (nextPhase) {
      updateFlowState({
        current_phase: nextPhase,
        next_phase: getNextPhase(nextPhase),
        previous_phase: currentPhase
      });
      navigate(`/discovery/${nextPhase.replace('_', '-')}`);
    }
  }, [getNextPhase, navigate, updateFlowState]);

  const navigateToPreviousPhase = useCallback((currentPhase: string) => {
    const previousPhase = getPreviousPhase(currentPhase);
    if (previousPhase) {
      updateFlowState({
        current_phase: previousPhase,
        next_phase: currentPhase,
        previous_phase: getPreviousPhase(previousPhase)
      });
      navigate(`/discovery/${previousPhase.replace('_', '-')}`);
    }
  }, [getPreviousPhase, navigate, updateFlowState]);

  const value = {
    flowState,
    updateFlowState,
    navigateToNextPhase,
    navigateToPreviousPhase,
    getPhaseCompletion
  };

  return (
    <DiscoveryFlowContext.Provider value={value}>
      {children}
    </DiscoveryFlowContext.Provider>
  );
}; 