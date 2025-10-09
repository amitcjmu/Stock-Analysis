/**
 * Custom hook for calculating progress milestones from form sections
 * Extracted from AdaptiveForms.tsx (lines 630-669)
 */

import React from "react";
import type { ProgressMilestone } from "../types";

interface FormSection {
  id: string;
  title: string;
  description?: string;
  fields: Array<{ id: string }>;
  requiredFieldsCount: number;
  completionWeight: number;
}

interface FormData {
  sections: FormSection[];
}

/**
 * Generate progress milestones dynamically from actual form sections
 * @param formData - The form data containing sections
 * @param formValues - Current form values to calculate completion
 * @returns Array of progress milestones with completion status
 */
export const useProgressCalculation = (
  formData: FormData | null | undefined,
  formValues: Record<string, unknown> | null | undefined
): ProgressMilestone[] => {
  return React.useMemo(() => {
    if (!formData?.sections) return [];

    const milestones: ProgressMilestone[] = [
      {
        id: "form-start",
        title: "Form Started",
        description: "Begin adaptive data collection",
        achieved: true,
        achievedAt: new Date().toISOString(),
        weight: 0.1,
        required: true,
      },
    ];

    // Add milestone for each form section
    formData.sections.forEach((section) => {
      // Calculate if section is completed based on formValues
      const sectionFields = section.fields.map(f => f.id);
      const completedFields = sectionFields.filter(fieldId => {
        const value = formValues?.[fieldId];
        return value !== null && value !== undefined && value !== '';
      });
      const isCompleted = section.requiredFieldsCount > 0
        ? completedFields.length >= section.requiredFieldsCount
        : completedFields.length === sectionFields.length;

      milestones.push({
        id: section.id,
        title: section.title,
        description: section.description || `Complete ${section.title.toLowerCase()}`,
        achieved: isCompleted,
        achievedAt: isCompleted ? new Date().toISOString() : undefined,
        weight: section.completionWeight,
        required: section.requiredFieldsCount > 0,
      });
    });

    return milestones;
  }, [formData, formValues]);
};
