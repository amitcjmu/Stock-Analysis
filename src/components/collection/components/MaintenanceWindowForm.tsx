/**
 * Maintenance Window Form Component
 *
 * Simple form for adding/editing maintenance windows with scope selection
 */

import React, { useState, useCallback } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Calendar, Clock, AlertTriangle, Save, X } from 'lucide-react';
import { cn } from '@/lib/utils';
import type { MaintenanceWindow } from '../types';

interface MaintenanceWindowFormProps {
  initialData?: MaintenanceWindow;
  onSave: (data: MaintenanceWindow) => Promise<void>;
  onCancel: () => void;
  className?: string;
  scopeOptions?: Array<{ value: string; label: string; type: 'tenant' | 'application' | 'asset' }>;
}

export const MaintenanceWindowForm: React.FC<MaintenanceWindowFormProps> = ({
  initialData,
  onSave,
  onCancel,
  className,
  scopeOptions = []
}) => {
  const [formData, setFormData] = useState<MaintenanceWindow>({
    name: '',
    description: '',
    scope: 'tenant',
    scope_id: '',
    start_time: '',
    end_time: '',
    recurrence_pattern: 'none',
    timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
    impact_level: 'medium',
    approval_required: false,
    ...initialData
  });

  const [isSaving, setIsSaving] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});

  const validateForm = useCallback((): boolean => {
    const newErrors: Record<string, string> = {};

    if (!formData.name.trim()) {
      newErrors.name = 'Name is required';
    }

    if (!formData.scope_id) {
      newErrors.scope_id = 'Scope selection is required';
    }

    if (!formData.start_time) {
      newErrors.start_time = 'Start time is required';
    }

    if (!formData.end_time) {
      newErrors.end_time = 'End time is required';
    }

    if (formData.start_time && formData.end_time) {
      const startDate = new Date(formData.start_time);
      const endDate = new Date(formData.end_time);
      if (endDate <= startDate) {
        newErrors.end_time = 'End time must be after start time';
      }
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  }, [formData]);

  const handleSubmit = useCallback(async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateForm()) {
      return;
    }

    setIsSaving(true);
    try {
      await onSave(formData);
    } catch (error) {
      console.error('Failed to save maintenance window:', error);
    } finally {
      setIsSaving(false);
    }
  }, [formData, onSave, validateForm]);

  const handleFieldChange = useCallback((field: keyof MaintenanceWindow, value: any) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));

    // Clear field error when user starts typing
    if (errors[field]) {
      setErrors(prev => ({
        ...prev,
        [field]: ''
      }));
    }
  }, [errors]);

  const getImpactColor = (level: string) => {
    switch (level) {
      case 'low': return 'bg-green-100 text-green-800';
      case 'medium': return 'bg-yellow-100 text-yellow-800';
      case 'high': return 'bg-orange-100 text-orange-800';
      case 'critical': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <Card className={cn('w-full', className)}>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Calendar className="h-5 w-5" />
          {initialData?.id ? 'Edit Maintenance Window' : 'Create Maintenance Window'}
        </CardTitle>
        <CardDescription>
          Define a maintenance window for planned downtime or restricted operations
        </CardDescription>
      </CardHeader>

      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Basic Information */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="name">
                Name <span className="text-red-500">*</span>
              </Label>
              <Input
                id="name"
                value={formData.name}
                onChange={(e) => handleFieldChange('name', e.target.value)}
                placeholder="e.g., Monthly Patching Window"
                className={cn(errors.name && 'border-red-500')}
              />
              {errors.name && (
                <p className="text-sm text-red-600">{errors.name}</p>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="impact_level">Impact Level</Label>
              <Select value={formData.impact_level} onValueChange={(value) => handleFieldChange('impact_level', value)}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="low">Low</SelectItem>
                  <SelectItem value="medium">Medium</SelectItem>
                  <SelectItem value="high">High</SelectItem>
                  <SelectItem value="critical">Critical</SelectItem>
                </SelectContent>
              </Select>
              <Badge className={getImpactColor(formData.impact_level)}>
                {formData.impact_level.charAt(0).toUpperCase() + formData.impact_level.slice(1)} Impact
              </Badge>
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="description">Description</Label>
            <Textarea
              id="description"
              value={formData.description || ''}
              onChange={(e) => handleFieldChange('description', e.target.value)}
              placeholder="Describe the maintenance activities and expected impact..."
              rows={3}
            />
          </div>

          {/* Scope Selection */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="scope">Scope Type</Label>
              <Select value={formData.scope} onValueChange={(value) => handleFieldChange('scope', value)}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="tenant">Tenant-wide</SelectItem>
                  <SelectItem value="application">Application-specific</SelectItem>
                  <SelectItem value="asset">Asset-specific</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="scope_id">
                Scope Target <span className="text-red-500">*</span>
              </Label>
              <Select value={formData.scope_id} onValueChange={(value) => handleFieldChange('scope_id', value)}>
                <SelectTrigger className={cn(errors.scope_id && 'border-red-500')}>
                  <SelectValue placeholder="Select target..." />
                </SelectTrigger>
                <SelectContent>
                  {scopeOptions
                    .filter(option => option.type === formData.scope)
                    .map((option) => (
                      <SelectItem key={option.value} value={option.value}>
                        {option.label}
                      </SelectItem>
                    ))}
                </SelectContent>
              </Select>
              {errors.scope_id && (
                <p className="text-sm text-red-600">{errors.scope_id}</p>
              )}
            </div>
          </div>

          {/* Timing */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="start_time">
                Start Time <span className="text-red-500">*</span>
              </Label>
              <Input
                id="start_time"
                type="datetime-local"
                value={formData.start_time}
                onChange={(e) => handleFieldChange('start_time', e.target.value)}
                className={cn(errors.start_time && 'border-red-500')}
              />
              {errors.start_time && (
                <p className="text-sm text-red-600">{errors.start_time}</p>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="end_time">
                End Time <span className="text-red-500">*</span>
              </Label>
              <Input
                id="end_time"
                type="datetime-local"
                value={formData.end_time}
                onChange={(e) => handleFieldChange('end_time', e.target.value)}
                className={cn(errors.end_time && 'border-red-500')}
              />
              {errors.end_time && (
                <p className="text-sm text-red-600">{errors.end_time}</p>
              )}
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="recurrence">Recurrence Pattern</Label>
              <Select value={formData.recurrence_pattern} onValueChange={(value) => handleFieldChange('recurrence_pattern', value)}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="none">One-time</SelectItem>
                  <SelectItem value="daily">Daily</SelectItem>
                  <SelectItem value="weekly">Weekly</SelectItem>
                  <SelectItem value="monthly">Monthly</SelectItem>
                  <SelectItem value="quarterly">Quarterly</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="timezone">Timezone</Label>
              <Input
                id="timezone"
                value={formData.timezone}
                onChange={(e) => handleFieldChange('timezone', e.target.value)}
                placeholder="e.g., UTC, America/New_York"
              />
            </div>
          </div>

          {/* Options */}
          <div className="space-y-4">
            <div className="flex items-center space-x-2">
              <Switch
                id="approval_required"
                checked={formData.approval_required}
                onCheckedChange={(checked) => handleFieldChange('approval_required', checked)}
              />
              <Label htmlFor="approval_required" className="flex items-center gap-2">
                <AlertTriangle className="h-4 w-4 text-amber-500" />
                Requires approval before execution
              </Label>
            </div>
          </div>

          {/* Actions */}
          <div className="flex gap-3 pt-4 border-t">
            <Button
              type="submit"
              disabled={isSaving}
              className="flex items-center gap-2"
            >
              <Save className="h-4 w-4" />
              {isSaving ? 'Saving...' : 'Save Maintenance Window'}
            </Button>

            <Button
              type="button"
              variant="outline"
              onClick={onCancel}
              disabled={isSaving}
              className="flex items-center gap-2"
            >
              <X className="h-4 w-4" />
              Cancel
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  );
};
