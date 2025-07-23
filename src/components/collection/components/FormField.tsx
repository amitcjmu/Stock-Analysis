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

import { FormFieldProps, FieldType, FieldValue } from '../types';

export const FormField: React.FC<FormFieldProps> = ({
  field,
  value,
  onChange,
  validation,
  disabled = false,
  className
}) => {
  const [isFocused, setIsFocused] = useState(false);
  const [showHelp, setShowHelp] = useState(false);
  const [hasBeenTouched, setHasBeenTouched] = useState(false);

  const handleChange = useCallback((newValue: FieldValue) => {
    onChange(newValue);
  }, [onChange]);

  const renderFieldInput = () => {
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
          />
        );

      case 'date':
        return (
          <Input
            {...commonProps}
            type="date"
            value={value || ''}
            onChange={(e) => handleChange(e.target.value)}
          />
        );

      case 'textarea':
        return (
          <Textarea
            {...commonProps}
            value={value || ''}
            onChange={(e) => handleChange(e.target.value)}
            placeholder={field.placeholder}
            rows={4}
          />
        );

      case 'select':
        return (
          <Select
            value={value || ''}
            onValueChange={handleChange}
            disabled={disabled}
          >
            <SelectTrigger className={commonProps.className}>
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

      case 'radio':
        return (
          <RadioGroup
            value={value || ''}
            onValueChange={handleChange}
            disabled={disabled}
            className="space-y-2"
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
          />
        );

      default:
        return (
          <Input
            {...commonProps}
            value={value || ''}
            onChange={(e) => handleChange(e.target.value)}
            placeholder={field.placeholder}
          />
        );
    }
  };

  const renderValidationFeedback = () => {
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
    <div className={cn('space-y-2', className)}>
      {/* Field Label */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Label
            htmlFor={field.id}
            className={cn(
              'text-sm font-medium',
              isRequired && 'after:content-["*"] after:ml-0.5 after:text-red-500'
            )}
          >
            {field.label}
          </Label>
          
          {hasBusinessImpact && (
            <Badge variant="secondary" className="text-xs">
              High Impact
            </Badge>
          )}
          
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