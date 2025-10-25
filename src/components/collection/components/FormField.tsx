/**
 * Form Field Component
 *
 * Renders individual form fields with validation, help text, and conditional logic
 * Agent Team B3 - Form field rendering implementation
 */

import React from 'react'
import { useState } from 'react'
import { useCallback } from 'react'
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Checkbox } from '@/components/ui/checkbox';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { HelpCircle, AlertCircle, CheckCircle, X } from 'lucide-react';
import { cn } from '@/lib/utils';

import type { FormFieldProps, FieldValue, VendorProduct } from '../types';
import { FieldType } from '../types';
import { TechnologyPicker } from './TechnologyPicker';
import { AssetSelector } from '../AssetSelector';

export const FormField: React.FC<FormFieldProps> = ({
  field,
  value,
  onChange,
  validation,
  disabled = false,
  className,
  questionNumber
}) => {
  const [isFocused, setIsFocused] = useState(false);
  const [showHelp, setShowHelp] = useState(false);
  const [hasBeenTouched, setHasBeenTouched] = useState(false);

  const handleChange = useCallback((newValue: FieldValue) => {
    onChange(newValue);
  }, [onChange]);

  const renderFieldInput = (): JSX.Element => {
    const commonProps = {
      id: field.id,
      disabled,
      onFocus: () => setIsFocused(true),
      onBlur: () => {
        setIsFocused(false);
        setHasBeenTouched(true);
      },
      className: cn(
        'transition-colors',
        hasBeenTouched && validation?.isValid === false && 'border-red-500 focus:border-red-500',
        hasBeenTouched && validation?.isValid === true && 'border-green-500',
        hasBeenTouched && validation?.warnings?.length && 'border-amber-500'
      )
    };

    switch (field.fieldType) {
      case 'text':
      case 'email':
      case 'url':
        return (
          <Input
            {...commonProps}
            type={field.fieldType === 'email' ? 'email' : field.fieldType === 'url' ? 'url' : 'text'}
            value={value || ''}
            onChange={(e) => handleChange(e.target.value)}
            placeholder={field.placeholder}
            data-testid={`answer-input-${field.id}`}
          />
        );

      case 'number':
        return (
          <Input
            {...commonProps}
            type="number"
            value={value || ''}
            onChange={(e) => handleChange(e.target.value ? Number(e.target.value) : undefined)}
            placeholder={field.placeholder}
            data-testid={`answer-input-${field.id}`}
          />
        );

      case 'numeric_input':
        return (
          <div className="space-y-2">
            <div className="relative">
              <Input
                {...commonProps}
                type="number"
                value={value || ''}
                onChange={(e) => handleChange(e.target.value ? Number(e.target.value) : undefined)}
                placeholder={field.placeholder || 'Enter minutes'}
                min="0"
                step="1"
                data-testid={`answer-input-${field.id}`}
              />
              {field.description?.includes('minutes') && (
                <span className="absolute right-3 top-1/2 transform -translate-y-1/2 text-sm text-muted-foreground">
                  min
                </span>
              )}
            </div>
            {field.helpText && (
              <p className="text-xs text-muted-foreground">
                {field.helpText}
              </p>
            )}
          </div>
        );

      case 'date':
        return (
          <Input
            {...commonProps}
            type="date"
            value={value || ''}
            onChange={(e) => handleChange(e.target.value)}
            data-testid={`answer-input-${field.id}`}
          />
        );

      case 'date_input':
        return (
          <div className="space-y-2">
            <Input
              {...commonProps}
              type="date"
              value={value || ''}
              onChange={(e) => handleChange(e.target.value)}
              placeholder={field.placeholder || 'Select date'}
              data-testid={`answer-input-${field.id}`}
            />
            {field.helpText && (
              <p className="text-xs text-muted-foreground">
                {field.helpText}
              </p>
            )}
          </div>
        );

      case 'textarea':
        return (
          <Textarea
            {...commonProps}
            value={value || ''}
            onChange={(e) => handleChange(e.target.value)}
            placeholder={field.placeholder}
            rows={4}
            data-testid={`answer-input-${field.id}`}
          />
        );

      case 'select':
        return (
          <Select
            value={value || ''}
            onValueChange={handleChange}
            disabled={disabled}
          >
            <SelectTrigger className={commonProps.className} data-testid={`answer-input-${field.id}`}>
              <SelectValue placeholder={field.placeholder || 'Select an option'} />
            </SelectTrigger>
            <SelectContent>
              {field.options?.map((option) => (
                <SelectItem key={option.value} value={option.value}>
                  {option.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        );

      case 'multiselect': {
        const selectedValues = Array.isArray(value) ? value : [];
        return (
          <div className="space-y-2">
            {field.options?.map((option) => (
              <div key={option.value} className="flex items-center space-x-2">
                <Checkbox
                  id={`${field.id}-${option.value}`}
                  checked={selectedValues.includes(option.value)}
                  onCheckedChange={(checked) => {
                    if (checked) {
                      handleChange([...selectedValues, option.value]);
                    } else {
                      handleChange(selectedValues.filter(v => v !== option.value));
                    }
                  }}
                  disabled={disabled}
                />
                <Label
                  htmlFor={`${field.id}-${option.value}`}
                  className="text-sm font-normal cursor-pointer"
                >
                  {option.label}
                </Label>
              </div>
            ))}
          </div>
        );
      }

      case 'multi_select': {
        const selectedValues = Array.isArray(value) ? value : [];
        return (
          <div className="space-y-3">
            <div className="border rounded-lg p-3 max-h-48 overflow-y-auto">
              <div className="space-y-2">
                {field.options?.map((option) => (
                  <div key={option.value} className="flex items-center space-x-2">
                    <Checkbox
                      id={`${field.id}-${option.value}`}
                      checked={selectedValues.includes(option.value)}
                      onCheckedChange={(checked) => {
                        if (checked) {
                          handleChange([...selectedValues, option.value]);
                        } else {
                          handleChange(selectedValues.filter(v => v !== option.value));
                        }
                      }}
                      disabled={disabled}
                    />
                    <Label
                      htmlFor={`${field.id}-${option.value}`}
                      className="text-sm font-normal cursor-pointer flex-1"
                    >
                      {option.label}
                    </Label>
                  </div>
                ))}
              </div>
            </div>
            {selectedValues.length > 0 && (
              <div className="flex flex-wrap gap-1">
                {selectedValues.map((val) => {
                  const option = field.options?.find(opt => opt.value === val);
                  return (
                    <Badge key={val} variant="secondary" className="text-xs">
                      {option?.label || val}
                    </Badge>
                  );
                })}
              </div>
            )}
            {field.helpText && (
              <p className="text-xs text-muted-foreground">
                {field.helpText}
              </p>
            )}
          </div>
        );
      }

      case 'radio':
        return (
          <RadioGroup
            value={value || ''}
            onValueChange={handleChange}
            disabled={disabled}
            className="space-y-2"
            data-testid={`answer-input-${field.id}`}
          >
            {field.options?.map((option) => (
              <div key={option.value} className="flex items-center space-x-2">
                <RadioGroupItem
                  value={option.value}
                  id={`${field.id}-${option.value}`}
                />
                <Label
                  htmlFor={`${field.id}-${option.value}`}
                  className="text-sm font-normal cursor-pointer"
                >
                  {option.label}
                </Label>
              </div>
            ))}
          </RadioGroup>
        );

      case 'checkbox':
        return (
          <div className="flex items-center space-x-2">
            <Checkbox
              id={field.id}
              checked={Boolean(value)}
              onCheckedChange={handleChange}
              disabled={disabled}
              data-testid={`answer-input-${field.id}`}
            />
            <Label
              htmlFor={field.id}
              className="text-sm font-normal cursor-pointer"
            >
              {field.label}
            </Label>
          </div>
        );

      case 'file':
        return (
          <Input
            {...commonProps}
            type="file"
            onChange={(e) => handleChange(e.target.files?.[0])}
            accept=".csv,.xlsx,.json"
            data-testid={`answer-input-${field.id}`}
          />
        );

      case 'technology_selection':
        return (
          <TechnologyPicker
            value={value as VendorProduct | VendorProduct[]}
            onChange={handleChange}
            placeholder={field.placeholder || 'Select vendor/product...'}
            multiple={field.description?.includes('multiple') || false}
            disabled={disabled}
            helpText={field.helpText}
          />
        );

      case 'asset_selector':
        return (
          <AssetSelector
            options={field.options || []}
            value={value}
            onChange={handleChange}
            multiple={field.metadata?.multiple}
            required={field.validation?.required}
            showCompleteness={field.metadata?.show_completeness}
            showTypeFilter={field.metadata?.show_type_filter}
            allowSearch={field.metadata?.allow_search}
            placeholder={field.placeholder || "Select assets..."}
          />
        );

      default:
        return (
          <Input
            {...commonProps}
            value={value || ''}
            onChange={(e) => handleChange(e.target.value)}
            placeholder={field.placeholder}
            data-testid={`answer-input-${field.id}`}
          />
        );
    }
  };

  const renderValidationFeedback = (): JSX.Element => {
    if (!validation || !hasBeenTouched) return null;

    const { errors, warnings } = validation;
    const allIssues = [...errors, ...warnings];

    if (allIssues.length === 0) {
      return validation.isValid && hasBeenTouched ? (
        <div className="flex items-center gap-1 text-sm text-green-600">
          <CheckCircle className="h-4 w-4" />
          Valid
        </div>
      ) : null;
    }

    return (
      <div className="space-y-1">
        {allIssues.map((issue, index) => (
          <div
            key={index}
            className={cn(
              'flex items-start gap-1 text-sm',
              issue.severity === 'error' && 'text-red-600',
              issue.severity === 'warning' && 'text-amber-600',
              issue.severity === 'info' && 'text-blue-600'
            )}
          >
            <AlertCircle className="h-4 w-4 mt-0.5 flex-shrink-0" />
            <div>
              <p>{issue.errorMessage}</p>
              {issue.suggestedValue && (
                <Button
                  type="button"
                  variant="link"
                  size="sm"
                  className="h-auto p-0 text-xs"
                  onClick={() => handleChange(issue.suggestedValue)}
                >
                  Use suggested: "{issue.suggestedValue}"
                </Button>
              )}
            </div>
          </div>
        ))}
      </div>
    );
  };

  const isRequired = field.validation?.required || false;
  const hasBusinessImpact = field.businessImpactScore >= 0.05;

  return (
    <div className={cn('space-y-2', className)} data-testid={`question-item-${field.id}`}>
      {/* Field Label */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Label
            htmlFor={field.id}
            className={cn(
              'text-sm font-medium',
              isRequired && 'after:content-["*"] after:ml-0.5 after:text-red-500'
            )}
            data-testid={`question-${field.id}-text`}
          >
            {(questionNumber !== undefined && questionNumber !== null && questionNumber >= 0) && (
              <span className="text-muted-foreground mr-2">
                {questionNumber}.
              </span>
            )}
            {field.label}
          </Label>

          {hasBusinessImpact && (
            <Badge variant="secondary" className="text-xs">
              High Impact
            </Badge>
          )}

          <Badge
            variant="outline"
            className="text-xs"
            data-testid={`question-${field.id}-status`}
          >
            {value !== undefined && value !== null && value !== '' ? 'answered' : 'unanswered'}
          </Badge>

          {field.helpText && (
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    className="h-auto p-0 w-4 h-4"
                    onClick={() => setShowHelp(!showHelp)}
                  >
                    <HelpCircle className="h-4 w-4 text-muted-foreground" />
                  </Button>
                </TooltipTrigger>
                <TooltipContent side="top" className="max-w-xs">
                  <p>{field.helpText}</p>
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
          )}
        </div>

        {/* Confidence Score - Only show after field has been touched */}
        {hasBeenTouched && validation?.confidenceScore !== undefined && validation.confidenceScore > 0 && (
          <Badge
            variant="outline"
            className={cn(
              'text-xs',
              validation.confidenceScore >= 0.8 && 'border-green-500 text-green-700',
              validation.confidenceScore >= 0.6 && validation.confidenceScore < 0.8 && 'border-amber-500 text-amber-700',
              validation.confidenceScore < 0.6 && 'border-red-500 text-red-700'
            )}
          >
            {Math.round(validation.confidenceScore * 100)}% confidence
          </Badge>
        )}
      </div>

      {/* Field Description */}
      {field.description && (
        <p className="text-xs text-muted-foreground">
          {field.description}
        </p>
      )}

      {/* Field Input */}
      <div className="relative">
        {renderFieldInput()}

        {/* Focus indicator for business impact fields */}
        {isFocused && hasBusinessImpact && (
          <div className="absolute -inset-0.5 bg-blue-500/20 rounded-lg pointer-events-none" />
        )}
      </div>

      {/* Extended Help Text */}
      {showHelp && field.helpText && (
        <div className="p-3 bg-muted rounded-lg">
          <div className="flex items-start justify-between gap-2">
            <p className="text-sm text-muted-foreground">
              {field.helpText}
            </p>
            <Button
              type="button"
              variant="ghost"
              size="sm"
              className="h-auto p-0"
              onClick={() => setShowHelp(false)}
            >
              <X className="h-4 w-4" />
            </Button>
          </div>
        </div>
      )}

      {/* Validation Feedback */}
      {renderValidationFeedback()}
    </div>
  );
};
