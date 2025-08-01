/**
 * Observability context hooks
 * Custom hooks for accessing specific parts of the observability context
 */

import { useContext } from 'react';
import { ObservabilityContext, type ObservabilityContextValue } from './ObservabilityContext';

export const useObservability = (): ObservabilityContextValue => {
  const context = useContext(ObservabilityContext);
  if (!context) {
    throw new Error('useObservability must be used within ObservabilityProvider');
  }
  return context;
};

export const useAgentSelection = () => {
  const context = useObservability();
  return {
    selectedAgents: context.selectedAgents,
    selectAgent: context.selectAgent,
    deselectAgent: context.deselectAgent,
    toggleAgentSelection: context.toggleAgentSelection,
    clearSelection: context.clearSelection
  };
};

export const useViewPreferences = () => {
  const context = useObservability();
  return {
    viewMode: context.viewMode,
    setViewMode: context.setViewMode,
    compactView: context.compactView,
    setCompactView: context.setCompactView
  };
};