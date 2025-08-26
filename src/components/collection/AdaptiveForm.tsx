/**
 * Adaptive Form Component
 *
 * Dynamic form generation and rendering based on gap analysis and application context.
 * Supports conditional fields, progressive disclosure, and bulk mode toggle.
 *
 * Agent Team B3 - Task B3.1 Frontend Implementation
 */

import React from 'react'
import { useState } from 'react'
import { useEffect, useCallback, useMemo } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { AlertCircle, Clock, Target, Users } from 'lucide-react';
import { cn } from '@/lib/utils';

// Security: Helper function to validate regex patterns and prevent ReDoS attacks
const isValidRegexPattern = (pattern: string): boolean => {
  try {
    // Check for common dangerous patterns that could lead to ReDoS
    const dangerousPatterns = [
      /\(\?\![^\)]*\+/,    // Negative lookahead with quantifiers
      /\([^\)]*\+[^\)]*\+/,  // Nested quantifiers
      /\([^\)]*\*[^\)]*\*/,  // Nested star quantifiers
      /\{\d+,\}/,         // Open-ended quantifiers
    ];

    for (const dangerous of dangerousPatterns) {
      if (dangerous.test(pattern)) {
        return false;
      }
    }

    // Test if pattern compiles without throwing
    new RegExp(pattern);
    return true;
  } catch {
    return false;
  }
};

import { FormField } from './components/FormField';
import { SectionCard } from './components/SectionCard';
import { BulkDataGrid } from './BulkDataGrid';
import { ValidationDisplay } from './ValidationDisplay';

import type {
  AdaptiveFormProps,
  CollectionFormData,
  FormValidationResult,
  FormSection,
  FieldValidationResult,
  ValidationError,
  FieldValue
} from './types';
import {
  AdaptiveFormData
} from './types';

export const AdaptiveForm: React.FC<AdaptiveFormProps> = ({
  formData,
  initialValues = {},
  onFieldChange,
  onSubmit,
  onValidationChange,
  bulkMode = false,
  onBulkToggle,
  className
}) => {
  const [formValues, setFormValues] = useState<CollectionFormData>(initialValues);
  const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set());
  const [validation, setValidation] = useState<FormValidationResult | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [currentStep, setCurrentStep] = useState(0);
  const [hasInteracted, setHasInteracted] = useState(false); // Track if user has interacted with form

  // Calculate form progress and metrics
  const formMetrics = useMemo(() => {
    const totalFields = formData.totalFields;
    const filledFields = Object.keys(formValues).filter(key =>
      formValues[key] !== undefined && formValues[key] !== null && formValues[key] !== ''
    ).length;

    const completionPercentage = totalFields > 0 ? (filledFields / totalFields) * 100 : 0;

    // Calculate section progress
    const sectionProgress = formData.sections.map(section => {
      const sectionFields = section.fields.map(f => f.id);
      const sectionFilledFields = sectionFields.filter(fieldId =>
        formValues[fieldId] !== undefined && formValues[fieldId] !== null && formValues[fieldId] !== ''
      ).length;
      const sectionCompletion = section.fields.length > 0 ? (sectionFilledFields / section.fields.length) * 100 : 0;

      return {
        sectionId: section.id,
        completion: sectionCompletion,
        validationStatus: validation?.fieldResults ?
          section.fields.every(f => validation.fieldResults[f.id]?.isValid !== false) ? 'valid' : 'invalid'
          : 'pending' as const
      };
    });

    return {
      completionPercentage,
      filledFields,
      totalFields,
      sectionProgress
    };
  }, [formValues, formData, validation]);

  // Auto-expand first incomplete section
  useEffect(() => {
    if (expandedSections.size === 0) {
      const firstIncompleteSection = formMetrics.sectionProgress.find(
        sp => sp.completion < 100
      );
      if (firstIncompleteSection) {
        setExpandedSections(new Set([firstIncompleteSection.sectionId]));
      } else if (formData.sections.length > 0) {
        setExpandedSections(new Set([formData.sections[0].id]));
      }
    }
  }, [formData.sections, formMetrics.sectionProgress, expandedSections.size]);

  // Handle field value changes
  const handleFieldChange = useCallback((fieldId: string, value: FieldValue) => {
    // Mark form as interacted on first field change
    if (!hasInteracted) {
      setHasInteracted(true);
    }

    setFormValues(prev => ({
      ...prev,
      [fieldId]: value
    }));
    onFieldChange(fieldId, value);
  }, [onFieldChange, hasInteracted]);

  // Handle section toggle
  const handleSectionToggle = useCallback((sectionId: string) => {
    setExpandedSections(prev => {
      const newSet = new Set(prev);
      if (newSet.has(sectionId)) {
        newSet.delete(sectionId);
      } else {
        newSet.add(sectionId);
      }
      return newSet;
    });
  }, []);

  // Handle form submission
  const handleSubmit = useCallback(async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validation?.isValid) {
      // Mark form as interacted to show validation errors
      if (!hasInteracted) {
        setHasInteracted(true);
      }

      // Focus first invalid field
      const firstError = Object.values(validation?.fieldResults || {}).find(
        result => !result.isValid
      );
      if (firstError) {
        const element = document.getElementById(firstError.fieldId);
        element?.focus();
        element?.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }
      return;
    }

    setIsSubmitting(true);
    try {
      await onSubmit(formValues);
    } catch (error) {
      console.error('Form submission error:', error);
    } finally {
      setIsSubmitting(false);
    }
  }, [formValues, onSubmit, validation]);

  // Progressive disclosure - determine visible fields
  const getVisibleFields = useCallback((section: FormSection) => {
    return section.fields.filter(field => {
      if (!field.conditionalDisplay) return true;

      const dependentValue = formValues[field.conditionalDisplay.dependentField];
      const { condition, values } = field.conditionalDisplay;

      switch (condition) {
        case 'equals':
          return values.includes(String(dependentValue));
        case 'contains':
          return values.some(val => String(dependentValue).toLowerCase().includes(val.toLowerCase()));
        case 'not_equals':
          return !values.includes(String(dependentValue));
        case 'in':
          return values.includes(String(dependentValue));
        case 'not_in':
          return !values.includes(String(dependentValue));
        default:
          return true;
      }
    });
  }, [formValues]);

  // Validate form whenever values change
  useEffect(() => {
    // Always validate, but only show errors after user interaction
    const isShowingErrors = hasInteracted;

    const validateForm = (): FormValidationResult => {
      const fieldResults: Record<string, FieldValidationResult> = {};
      let totalValid = 0;
      let totalFields = 0;
      let totalConfidence = 0;

      formData.sections.forEach(section => {
        const visibleFields = getVisibleFields(section);

        visibleFields.forEach(field => {
          totalFields++;
          const value = formValues[field.id];
          const isRequired = field.validation?.required || false;
          const hasValue = value !== undefined && value !== null && value !== '';

          let isValid = true;
          const errors: ValidationError[] = [];
          const warnings: ValidationError[] = [];

          // Required field validation
          if (isRequired && !hasValue) {
            isValid = false;
            // Only show error if user has interacted with form
            if (isShowingErrors) {
              errors.push({
                fieldId: field.id,
                fieldLabel: field.label,
                errorCode: 'required',
                errorMessage: `${field.label} is required`,
                severity: 'error'
              });
            }
          }

          // Length validation
          if (hasValue && field.validation?.minLength && String(value).length < field.validation.minLength) {
            isValid = false;
            if (isShowingErrors) {
              errors.push({
                fieldId: field.id,
                fieldLabel: field.label,
                errorCode: 'minLength',
                errorMessage: `${field.label} must be at least ${field.validation.minLength} characters`,
                severity: 'error'
              });
            }
          }

          if (hasValue && field.validation?.maxLength && String(value).length > field.validation.maxLength) {
            isValid = false;
            if (isShowingErrors) {
              errors.push({
                fieldId: field.id,
                fieldLabel: field.label,
                errorCode: 'maxLength',
                errorMessage: `${field.label} must not exceed ${field.validation.maxLength} characters`,
                severity: 'error'
              });
            }
          }

          // Pattern validation
          if (hasValue && field.validation?.pattern) {
            // Validate regex pattern to prevent ReDoS attacks
            if (!isValidRegexPattern(field.validation.pattern)) {
              console.warn('Invalid or potentially dangerous regex pattern detected:', field.validation.pattern);
              isValid = false;
              if (isShowingErrors) {
                errors.push({
                  fieldId: field.id,
                  message: 'Invalid validation pattern configuration'
                });
              }
              return; // Skip further validation for this field
            }
            const regex = new RegExp(field.validation.pattern);
            if (!regex.test(String(value))) {
              isValid = false;
              if (isShowingErrors) {
                errors.push({
                  fieldId: field.id,
                  fieldLabel: field.label,
                  errorCode: 'pattern',
                  errorMessage: `${field.label} format is invalid`,
                  severity: 'error'
                });
              }
            }
          }

          // Email validation
          if (hasValue && field.fieldType === 'email') {
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if (!emailRegex.test(String(value))) {
              isValid = false;
              if (isShowingErrors) {
                errors.push({
                  fieldId: field.id,
                  fieldLabel: field.label,
                  errorCode: 'invalidEmail',
                  errorMessage: 'Please enter a valid email address',
                  severity: 'error'
                });
              }
            }
          }

          // URL validation
          if (hasValue && field.fieldType === 'url') {
            try {
              new URL(String(value));
            } catch {
              isValid = false;
              if (isShowingErrors) {
                errors.push({
                  fieldId: field.id,
                  fieldLabel: field.label,
                  errorCode: 'invalidUrl',
                  errorMessage: 'Please enter a valid URL',
                  severity: 'error'
                });
              }
            }
          }

          if (isValid) totalValid++;

          const confidenceScore = isValid ? 1.0 : hasValue ? 0.5 : 0.0;
          totalConfidence += confidenceScore;

          fieldResults[field.id] = {
            fieldId: field.id,
            isValid,
            resultType: isValid ? 'valid' : 'invalid',
            errors,
            warnings,
            normalizedValue: value,
            confidenceScore
          };
        });
      });

      // Validation state calculated silently (removed debug log)

      const newValidation: FormValidationResult = {
        formId: formData.formId,
        isValid: totalValid === totalFields && totalFields > 0,
        overallConfidenceScore: totalFields > 0 ? totalConfidence / totalFields : 0,
        completionPercentage: formMetrics.completionPercentage,
        fieldResults,
        crossFieldErrors: [],
        businessRuleViolations: []
      };

      setValidation(newValidation);
      return newValidation;
    };

    const newValidation = validateForm();

    // Trigger validation change callback
    if (onValidationChange) {
      onValidationChange(newValidation);
    }
  }, [formValues, formData, getVisibleFields, formMetrics.completionPercentage, onValidationChange, hasInteracted]);

  if (bulkMode) {
    return (
      <div className={cn('space-y-6', className)}>
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold">Bulk Data Entry</h2>
            <p className="text-muted-foreground">
              Enter data for multiple applications simultaneously
            </p>
          </div>
          <div className="flex items-center space-x-2">
            <Label htmlFor="bulk-mode">Individual Form</Label>
            <Switch
              id="bulk-mode"
              checked={bulkMode}
              onCheckedChange={onBulkToggle}
            />
            <Label htmlFor="bulk-mode">Bulk Mode</Label>
          </div>
        </div>

        <BulkDataGrid
          applications={[]} // Would be populated from props
          fields={formData.sections.flatMap(s => s.fields)}
          onDataChange={handleFieldChange}
        />
      </div>
    );
  }

  return (
    <div className={cn('space-y-6', className)}>
      {/* Form Header */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <Target className="h-5 w-5" />
                Application Data Collection
              </CardTitle>
              <CardDescription>
                Complete the form below to provide detailed information about your application.
                Required fields are marked with an asterisk (*).
              </CardDescription>
            </div>

            {onBulkToggle && (
              <div className="flex items-center space-x-2">
                <Label htmlFor="form-mode">Individual</Label>
                <Switch
                  id="form-mode"
                  checked={bulkMode}
                  onCheckedChange={onBulkToggle}
                />
                <Label htmlFor="form-mode">Bulk</Label>
              </div>
            )}
          </div>

          {/* Form Metrics */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mt-4">
            <div className="flex items-center gap-2">
              <Progress value={formMetrics.completionPercentage} className="flex-1" />
              <span className="text-sm font-medium">
                {Math.round(formMetrics.completionPercentage)}%
              </span>
            </div>

            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Clock className="h-4 w-4" />
              ~{formData.estimatedCompletionTime}min
            </div>

            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Users className="h-4 w-4" />
              {formMetrics.filledFields}/{formMetrics.totalFields} fields
            </div>

            <Badge variant="outline" className="w-fit">
              Impact: +{Math.round(formData.confidenceImpactScore * 100)}% confidence
            </Badge>
          </div>
        </CardHeader>
      </Card>

      {/* Validation Display - Only show after interaction and when there are errors */}
      {validation && hasInteracted && Object.values(validation.fieldResults).some(result => result.errors.length > 0) && (
        <ValidationDisplay
          validation={validation}
          onErrorClick={(fieldId) => {
            const element = document.getElementById(fieldId);
            element?.focus();
            element?.scrollIntoView({ behavior: 'smooth', block: 'center' });
          }}
        />
      )}

      {/* Form Sections */}
      <form onSubmit={handleSubmit} className="space-y-4">
        {formData.sections.map((section, index) => {
          const sectionProgress = formMetrics.sectionProgress.find(
            sp => sp.sectionId === section.id
          );
          const visibleFields = getVisibleFields(section);

          return (
            <SectionCard
              key={section.id}
              section={section}
              isExpanded={expandedSections.has(section.id)}
              onToggle={() => handleSectionToggle(section.id)}
              completionPercentage={sectionProgress?.completion || 0}
              validationStatus={sectionProgress?.validationStatus || 'pending'}
            >
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {visibleFields.map(field => (
                  <FormField
                    key={field.id}
                    field={field}
                    value={formValues[field.id]}
                    onChange={(value) => handleFieldChange(field.id, value)}
                    validation={validation?.fieldResults[field.id]}
                    className={field.fieldType === 'textarea' ? 'md:col-span-2' : ''}
                  />
                ))}
              </div>
            </SectionCard>
          );
        })}

        {/* Form Actions */}
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div className="text-sm text-muted-foreground">
                {validation?.isValid ? (
                  <span className="text-green-600 flex items-center gap-1">
                    <Target className="h-4 w-4" />
                    Form is ready for submission
                  </span>
                ) : (
                  <span className="text-amber-600 flex items-center gap-1">
                    <AlertCircle className="h-4 w-4" />
                    Please complete all required fields
                  </span>
                )}
              </div>

              <div className="flex gap-2">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => {
                    // Save as draft functionality
                    console.log('Saving draft...', formValues);
                  }}
                >
                  Save Draft
                </Button>

                <Button
                  type="submit"
                  disabled={isSubmitting}
                  className="min-w-[120px]"
                >
                  {isSubmitting ? 'Submitting...' : 'Submit Form'}
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      </form>
    </div>
  );
};
