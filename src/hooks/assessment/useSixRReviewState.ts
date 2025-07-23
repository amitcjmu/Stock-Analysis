import type { useState } from 'react'
import { useEffect } from 'react'
import type { SixRDecision, ComponentTreatment } from '@/hooks/useAssessmentFlow';

interface UseSixRReviewStateProps {
  selectedApplicationIds: string[];
  sixrDecisions: Record<string, SixRDecision>;
  updateSixRDecision: (appId: string, decision: Partial<SixRDecision>) => void;
}

interface SixRReviewState {
  selectedApp: string;
  editingComponent: string | null;
  bulkEditMode: boolean;
  selectedComponents: string[];
}

export const useSixRReviewState = ({
  selectedApplicationIds,
  sixrDecisions,
  updateSixRDecision
}: UseSixRReviewStateProps) => {
  const [selectedApp, setSelectedApp] = useState<string>('');
  const [editingComponent, setEditingComponent] = useState<string | null>(null);
  const [bulkEditMode, setBulkEditMode] = useState(false);
  const [selectedComponents, setSelectedComponents] = useState<string[]>([]);

  // Set first application as selected by default
  useEffect(() => {
    if (selectedApplicationIds.length > 0 && !selectedApp) {
      setSelectedApp(selectedApplicationIds[0]);
    }
  }, [selectedApplicationIds, selectedApp]);

  // Get current application data
  const currentAppDecision = selectedApp ? sixrDecisions[selectedApp] : null;

  // Helper functions for updating decisions and treatments
  const updateAppDecision = (updates: Partial<SixRDecision>) => {
    if (!selectedApp) return;
    updateSixRDecision(selectedApp, updates);
  };

  const updateComponentTreatment = (componentName: string, treatment: Partial<ComponentTreatment>) => {
    if (!selectedApp || !currentAppDecision) return;

    const updatedTreatments = currentAppDecision.component_treatments.map(ct =>
      ct.component_name === componentName ? { ...ct, ...treatment } : ct
    );

    updateSixRDecision(selectedApp, {
      ...currentAppDecision,
      component_treatments: updatedTreatments
    });
  };

  // Reset selections when switching apps
  const handleAppSelect = (appId: string) => {
    setSelectedApp(appId);
    setEditingComponent(null);
    setBulkEditMode(false);
    setSelectedComponents([]);
  };

  // Handle bulk component updates
  const handleBulkComponentUpdate = (updates: Partial<ComponentTreatment>) => {
    selectedComponents.forEach(componentName => {
      updateComponentTreatment(componentName, updates);
    });
    setSelectedComponents([]);
  };

  return {
    // State
    selectedApp,
    editingComponent,
    bulkEditMode,
    selectedComponents,
    currentAppDecision,
    
    // Actions
    setSelectedApp: handleAppSelect,
    setEditingComponent,
    setBulkEditMode,
    setSelectedComponents,
    updateAppDecision,
    updateComponentTreatment,
    handleBulkComponentUpdate
  };
};