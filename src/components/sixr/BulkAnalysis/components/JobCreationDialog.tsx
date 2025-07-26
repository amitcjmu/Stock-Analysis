import React from 'react';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '../../../ui/dialog';
import { Button } from '../../../ui/button';
import { Input } from '../../../ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../../ui/select';
import { Checkbox } from '../../../ui/checkbox';
import { Label } from '../../../ui/label';
import { Textarea } from '../../../ui/textarea';
import type { JobCreationFormData } from '../types';

interface JobCreationDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  formData: JobCreationFormData;
  onFormDataChange: (data: JobCreationFormData) => void;
  onCreateJob: () => void;
}

export const JobCreationDialog: React.FC<JobCreationDialogProps> = ({
  open,
  onOpenChange,
  formData,
  onFormDataChange,
  onCreateJob
}) => {
  const updateFormData = (updates: Partial<JobCreationFormData>): any => {
    onFormDataChange({ ...formData, ...updates });
  };

  const updateParameters = (updates: Partial<JobCreationFormData['parameters']>): any => {
    onFormDataChange({
      ...formData,
      parameters: { ...formData.parameters, ...updates }
    });
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>Create New Bulk Analysis Job</DialogTitle>
          <DialogDescription>
            Configure a new bulk analysis job to analyze multiple applications using the 6R migration strategies.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6">
          {/* Basic Information */}
          <div className="space-y-4">
            <h3 className="text-lg font-medium">Basic Information</h3>

            <div className="space-y-2">
              <Label htmlFor="job-name">Job Name *</Label>
              <Input
                id="job-name"
                value={formData.name}
                onChange={(e) => updateFormData({ name: e.target.value })}
                placeholder="Enter job name..."
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="job-description">Description</Label>
              <Textarea
                id="job-description"
                value={formData.description}
                onChange={(e) => updateFormData({ description: e.target.value })}
                placeholder="Optional description..."
                rows={3}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="job-priority">Priority</Label>
              <Select
                value={formData.priority}
                onValueChange={(value: unknown) => updateFormData({ priority: value })}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="low">Low</SelectItem>
                  <SelectItem value="medium">Medium</SelectItem>
                  <SelectItem value="high">High</SelectItem>
                  <SelectItem value="urgent">Urgent</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          {/* Application Selection */}
          <div className="space-y-4">
            <h3 className="text-lg font-medium">Application Selection</h3>
            <div className="p-4 border rounded-lg bg-gray-50">
              <p className="text-sm text-gray-600 mb-2">
                Selected Applications: {formData.selectedApplications.length}
              </p>
              <Button variant="outline" size="sm">
                Select Applications
              </Button>
              <p className="text-xs text-gray-500 mt-2">
                Click to open application selector dialog
              </p>
            </div>
          </div>

          {/* Advanced Parameters */}
          <div className="space-y-4">
            <h3 className="text-lg font-medium">Advanced Parameters</h3>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="parallel-limit">Parallel Processing Limit</Label>
                <Input
                  id="parallel-limit"
                  type="number"
                  min="1"
                  max="20"
                  value={formData.parameters.parallel_limit}
                  onChange={(e) => updateParameters({
                    parallel_limit: parseInt(e.target.value) || 1
                  })}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="confidence-threshold">Confidence Threshold</Label>
                <Input
                  id="confidence-threshold"
                  type="number"
                  min="0"
                  max="1"
                  step="0.1"
                  value={formData.parameters.confidence_threshold}
                  onChange={(e) => updateParameters({
                    confidence_threshold: parseFloat(e.target.value) || 0.8
                  })}
                />
              </div>
            </div>

            <div className="space-y-3">
              <div className="flex items-center space-x-2">
                <Checkbox
                  id="retry-failed"
                  checked={formData.parameters.retry_failed}
                  onCheckedChange={(checked) => updateParameters({
                    retry_failed: checked as boolean
                  })}
                />
                <Label htmlFor="retry-failed" className="text-sm">
                  Automatically retry failed analyses
                </Label>
              </div>

              <div className="flex items-center space-x-2">
                <Checkbox
                  id="auto-approve"
                  checked={formData.parameters.auto_approve_high_confidence}
                  onCheckedChange={(checked) => updateParameters({
                    auto_approve_high_confidence: checked as boolean
                  })}
                />
                <Label htmlFor="auto-approve" className="text-sm">
                  Auto-approve results with high confidence scores
                </Label>
              </div>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex justify-end space-x-3 pt-4 border-t">
            <Button variant="outline" onClick={() => onOpenChange(false)}>
              Cancel
            </Button>
            <Button onClick={onCreateJob} disabled={!formData.name.trim()}>
              Create Job
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};
