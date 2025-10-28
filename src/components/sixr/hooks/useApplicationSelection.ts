/**
 * Custom hook for Application Selection functionality
 * Extracted from ApplicationSelector.tsx for modularization
 */

import type { Application } from '../types/ApplicationSelectorTypes';

// Bug #813 fix: Changed all number to string (UUID)
interface UseApplicationSelectionResult {
  handleSelectAll: (filteredApplications: Application[]) => void;
  handleSelectApplication: (appId: string) => void;
  handleStartAnalysis: (queueName?: string) => void;
}

interface UseApplicationSelectionProps {
  selectedApplications: string[]; // UUID strings
  onSelectionChange: (selectedIds: string[]) => void;
  onStartAnalysis: (applicationIds: string[], queueName?: string) => void;
  maxSelections: number;
}

export const useApplicationSelection = ({
  selectedApplications,
  onSelectionChange,
  onStartAnalysis,
  maxSelections
}: UseApplicationSelectionProps): UseApplicationSelectionResult => {

  const handleSelectAll = (filteredApplications: Application[]): void => {
    const allIds = filteredApplications.map(app => app.id);
    const newSelection = selectedApplications.length === allIds.length ? [] : allIds;
    onSelectionChange(newSelection.slice(0, maxSelections));
  };

  // Bug #813 fix: Changed appId from number to string (UUID)
  const handleSelectApplication = (appId: string): void => {
    const newSelection = selectedApplications.includes(appId)
      ? selectedApplications.filter(id => id !== appId)
      : [...selectedApplications, appId].slice(0, maxSelections);

    onSelectionChange(newSelection);
  };

  const handleStartAnalysis = (queueName?: string): void => {
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
