import React, { createContext, useContext, ReactNode } from 'react';
import { useDependencyLogic } from '../hooks/discovery/useDependencyLogic';
import { useDependencyNavigation } from '../hooks/discovery/useDependencyNavigation';
import { DependencyData, DependencyNavigationOptions } from '../types/dependency';

interface DependencyContextType {
  dependencyData: DependencyData | null;
  flowState: any;
  isLoading: boolean;
  isAnalyzing: boolean;
  error: string | null;
  handleTriggerAnalysis: (type: 'app-server' | 'app-app') => void;
  handleCreateDependency: (dependency: any, type: 'app-server' | 'app-app') => void;
  handleUpdateDependency: (dependency: any, type: 'app-server' | 'app-app') => void;
  refetchDependencies: () => void;
  canContinueToNextPhase: () => boolean;
  handleContinueToNextPhase: (options?: DependencyNavigationOptions) => void;
  handleNavigateToInventory: () => void;
  handleNavigateToDataCleansing: () => void;
  handleNavigateToAttributeMapping: () => void;
}

const DependencyContext = createContext<DependencyContextType | null>(null);

export const useDependency = () => {
  const context = useContext(DependencyContext);
  if (!context) {
    throw new Error('useDependency must be used within a DependencyProvider');
  }
  return context;
};

interface DependencyProviderProps {
  children: ReactNode;
}

export const DependencyProvider: React.FC<DependencyProviderProps> = ({ children }) => {
  const {
    dependencyData,
    flowState,
    isLoading,
    isAnalyzing,
    error,
    handleTriggerAnalysis,
    handleCreateDependency,
    handleUpdateDependency,
    refetchDependencies,
    canContinueToNextPhase
  } = useDependencyLogic();

  const {
    handleContinueToNextPhase,
    handleNavigateToInventory,
    handleNavigateToDataCleansing,
    handleNavigateToAttributeMapping
  } = useDependencyNavigation(flowState, dependencyData);

  const value = {
    dependencyData,
    flowState,
    isLoading,
    isAnalyzing,
    error,
    handleTriggerAnalysis,
    handleCreateDependency,
    handleUpdateDependency,
    refetchDependencies,
    canContinueToNextPhase,
    handleContinueToNextPhase,
    handleNavigateToInventory,
    handleNavigateToDataCleansing,
    handleNavigateToAttributeMapping
  };

  return (
    <DependencyContext.Provider value={value}>
      {children}
    </DependencyContext.Provider>
  );
}; 