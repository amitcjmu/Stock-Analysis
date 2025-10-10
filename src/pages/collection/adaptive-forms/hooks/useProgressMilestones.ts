/**
 * useProgressMilestones Hook
 * Generates progress milestones dynamically from form sections
 */

import { useMemo } from 'react';
import type { ProgressMilestone } from '@/components/collection/types';
import type { CollectionFormData } from '@/components/collection/types';

interface UseProgressMilestonesProps {
  formData: CollectionFormData | null;
  formValues: Record<string, unknown> | null;
}

/**
 * Hook for generating progress milestones from form data
 */
export const useProgressMilestones = ({
  formData,
  formValues,
}: UseProgressMilestonesProps): ProgressMilestone[] => {
  return useMemo(() => {
    if (!formData?.sections) return [];

    return [
      {
        id: 'form-start',
        title: 'Form Started',
        description: 'Begin adaptive data collection',
        achieved: true,
        achievedAt: new Date().toISOString(),
        weight: 0.1,
        required: true,
      },
      ...formData.sections.map((section) => {
        const sectionFields = section.fields.map(f => f.id);
        const completedFields = sectionFields.filter(fieldId => {
          const value = formValues?.[fieldId];
          return value !== null && value !== undefined && value !== '';
        });
        const isCompleted = section.requiredFieldsCount > 0
          ? completedFields.length >= section.requiredFieldsCount
          : completedFields.length === sectionFields.length;

        return {
          id: section.id,
          title: section.title,
          description: section.description || `Complete ${section.title.toLowerCase()}`,
          achieved: isCompleted,
          achievedAt: isCompleted ? new Date().toISOString() : undefined,
          weight: section.completionWeight,
          required: section.requiredFieldsCount > 0,
        };
      }),
    ];
  }, [formData, formValues]);
};
