/**
 * Custom hook for Application Selection functionality
 * Extracted from ApplicationSelector.tsx for modularization
 */

import type { Application } from '../types/ApplicationSelectorTypes';

interface UseApplicationSelectionResult {
  handleSelectAll: (filteredApplications: Application[]) => void;
  handleSelectApplication: (appId: number) => void;
  handleStartAnalysis: (queueName?: string) => void;
}

interface UseApplicationSelectionProps {
  selectedApplications: number[];
  onSelectionChange: (selectedIds: number[]) => void;
  onStartAnalysis: (applicationIds: number[], queueName?: string) => void;
  maxSelections: number;
}

export const useApplicationSelection = ({
  selectedApplications,
  onSelectionChange,
  onStartAnalysis,
  maxSelections
}: UseApplicationSelectionProps): UseApplicationSelectionResult => {

  const handleSelectAll = (filteredApplications: Application[]) => {
    const allIds = filteredApplications.map(app => app.id);
    const newSelection = selectedApplications.length === allIds.length ? [] : allIds;
    onSelectionChange(newSelection.slice(0, maxSelections));
  };

  const handleSelectApplication = (appId: number) => {
    const newSelection = selectedApplications.includes(appId)
      ? selectedApplications.filter(id => id !== appId)
      : [...selectedApplications, appId].slice(0, maxSelections);

    onSelectionChange(newSelection);
  };

  const handleStartAnalysis = (queueName?: string) => {
    if (selectedApplications.length === 0) {
      throw new Error('Please select at least one application');
    }

    const finalQueueName = queueName || `Analysis ${new Date().toLocaleString()}`;
    onStartAnalysis(selectedApplications, finalQueueName);
  };

  return {
    handleSelectAll,
    handleSelectApplication,
    handleStartAnalysis
  };
};
