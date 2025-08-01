/**
 * Observability context hooks
 * Custom hooks for accessing specific parts of the observability context
 */

import { useContext } from 'react';
import { ObservabilityContext } from './context';
import type { ObservabilityContextValue } from './ObservabilityContext';

export const useObservability = (): ObservabilityContextValue => {
  const context = useContext(ObservabilityContext);
  if (!context) {
    throw new Error('useObservability must be used within ObservabilityProvider');
  }
  return context;
};

export const useAgentSelection = (): {
  selectedAgents: string[];
  selectAgent: (agentId: string) => void;
  deselectAgent: (agentId: string) => void;
  toggleAgentSelection: (agentId: string) => void;
  clearSelection: () => void;
} => {
  const context = useObservability();
  return {
    selectedAgents: context.selectedAgents,
    selectAgent: context.selectAgent,
    deselectAgent: context.deselectAgent,
    toggleAgentSelection: context.toggleAgentSelection,
    clearSelection: context.clearSelection
  };
};

export const useViewPreferences = (): {
  viewMode: 'grid' | 'list';
  setViewMode: (mode: 'grid' | 'list') => void;
  compactView: boolean;
  setCompactView: (compact: boolean) => void;
} => {
  const context = useObservability();
  return {
    viewMode: context.viewMode,
    setViewMode: context.setViewMode,
    compactView: context.compactView,
    setCompactView: context.setCompactView
  };
};
