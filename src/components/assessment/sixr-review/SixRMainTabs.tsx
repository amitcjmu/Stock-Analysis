import React from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { SixRStrategyMatrix } from '@/components/assessment/SixRStrategyMatrix';
import { ComponentTreatmentEditor } from '@/components/assessment/ComponentTreatmentEditor';
import { CompatibilityValidator } from '@/components/assessment/CompatibilityValidator';
import { MoveGroupHintsPanel } from '@/components/assessment/MoveGroupHintsPanel';
import { BulkEditingControls } from '@/components/assessment/BulkEditingControls';
import type { SixRDecision, ComponentTreatment } from '@/hooks/useAssessmentFlow';

interface SixRMainTabsProps {
  decision: SixRDecision;
  onDecisionChange: (updates: Partial<SixRDecision>) => void;
  onComponentTreatmentChange: (componentName: string, treatment: Partial<ComponentTreatment>) => void;
  editingComponent: string | null;
  onEditComponent: (componentName: string | null) => void;
  bulkEditMode: boolean;
  onBulkEditToggle: (enabled: boolean) => void;
  selectedComponents: string[];
  onComponentSelectionChange: (components: string[]) => void;
  onBulkComponentUpdate: (updates: Partial<ComponentTreatment>) => void;
}

export const SixRMainTabs: React.FC<SixRMainTabsProps> = ({
  decision,
  onDecisionChange,
  onComponentTreatmentChange,
  editingComponent,
  onEditComponent,
  bulkEditMode,
  onBulkEditToggle,
  selectedComponents,
  onComponentSelectionChange,
  onBulkComponentUpdate
}) => {
  return (
    <Tabs defaultValue="strategy-matrix" className="space-y-4">
      <TabsList className="grid w-full grid-cols-4">
        <TabsTrigger value="strategy-matrix">Strategy Matrix</TabsTrigger>
        <TabsTrigger value="component-treatments">
          Components ({decision.component_treatments.length})
        </TabsTrigger>
        <TabsTrigger value="compatibility">Compatibility</TabsTrigger>
        <TabsTrigger value="move-groups">Move Groups</TabsTrigger>
      </TabsList>

      <TabsContent value="strategy-matrix" className="space-y-4">
        <SixRStrategyMatrix
          decision={decision}
          onDecisionChange={onDecisionChange}
        />
      </TabsContent>

      <TabsContent value="component-treatments" className="space-y-4">
        {/* Bulk Editing Controls */}
        <BulkEditingControls
          enabled={bulkEditMode}
          onToggle={onBulkEditToggle}
          selectedComponents={selectedComponents}
          onSelectionChange={onComponentSelectionChange}
          componentTreatments={decision.component_treatments}
          onBulkUpdate={onBulkComponentUpdate}
        />

        <ComponentTreatmentEditor
          treatments={decision.component_treatments}
          onTreatmentChange={onComponentTreatmentChange}
          editingComponent={editingComponent}
          onEditComponent={onEditComponent}
          bulkEditMode={bulkEditMode}
          selectedComponents={selectedComponents}
          onSelectionChange={onComponentSelectionChange}
        />
      </TabsContent>

      <TabsContent value="compatibility" className="space-y-4">
        <CompatibilityValidator
          treatments={decision.component_treatments}
          onTreatmentChange={onComponentTreatmentChange}
        />
      </TabsContent>

      <TabsContent value="move-groups" className="space-y-4">
        <MoveGroupHintsPanel
          decision={decision}
          onDecisionChange={onDecisionChange}
        />
      </TabsContent>
    </Tabs>
  );
};