/**
 * ExceptionDialog Component
 * Dialog for creating/editing migration exceptions
 */

import React from 'react';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import type { ExceptionFormData, GovernanceRequirement } from '../types';

interface ExceptionDialogProps {
  isOpen: boolean;
  onOpenChange: (open: boolean) => void;
  formData: ExceptionFormData;
  onFormDataChange: (data: ExceptionFormData) => void;
  selectedRequirement: GovernanceRequirement | null;
  isSubmitting: boolean;
  onSubmit: () => void;
}

export const ExceptionDialog: React.FC<ExceptionDialogProps> = ({
  isOpen,
  onOpenChange,
  formData,
  onFormDataChange,
  selectedRequirement,
  isSubmitting,
  onSubmit
}) => {
  return (
    <Dialog open={isOpen} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>Request Migration Exception</DialogTitle>
          <DialogDescription>
            Submit an exception request for: {selectedRequirement?.title}
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-4 max-h-96 overflow-y-auto">
          <div className="space-y-2">
            <Label htmlFor="exception_title">Exception Title *</Label>
            <Input
              id="exception_title"
              value={formData.title}
              onChange={(e) => onFormDataChange({ ...formData, title: e.target.value })}
              placeholder="Brief title for this exception"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="justification">Justification *</Label>
            <Textarea
              id="justification"
              value={formData.justification}
              onChange={(e) => onFormDataChange({ ...formData, justification: e.target.value })}
              placeholder="Explain why this exception is needed"
              rows={3}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="business_impact">Business Impact</Label>
            <Textarea
              id="business_impact"
              value={formData.business_impact}
              onChange={(e) => onFormDataChange({ ...formData, business_impact: e.target.value })}
              placeholder="Describe the business impact of not granting this exception"
              rows={2}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="mitigation_plan">Mitigation Plan</Label>
            <Textarea
              id="mitigation_plan"
              value={formData.mitigation_plan}
              onChange={(e) => onFormDataChange({ ...formData, mitigation_plan: e.target.value })}
              placeholder="Describe how risks will be mitigated"
              rows={2}
            />
          </div>
          <div className="grid grid-cols-3 gap-4">
            <div className="space-y-2">
              <Label htmlFor="exception_scope">Scope</Label>
              <Select
                value={formData.scope}
                onValueChange={(value: 'tenant' | 'application' | 'asset') =>
                  onFormDataChange({ ...formData, scope: value })
                }
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="tenant">Tenant-wide</SelectItem>
                  <SelectItem value="application">Application</SelectItem>
                  <SelectItem value="asset">Asset</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label htmlFor="exception_scope_id">Scope ID</Label>
              <Input
                id="exception_scope_id"
                value={formData.scope_id}
                onChange={(e) => onFormDataChange({ ...formData, scope_id: e.target.value })}
                placeholder="Specific ID"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="exception_priority">Priority</Label>
              <Select
                value={formData.priority}
                onValueChange={(value: 'low' | 'medium' | 'high' | 'critical') =>
                  onFormDataChange({ ...formData, priority: value })
                }
              >
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
            </div>
          </div>
          <div className="space-y-2">
            <Label htmlFor="expiry_date">Expiry Date (Optional)</Label>
            <Input
              id="expiry_date"
              type="date"
              value={formData.expiry_date || ''}
              onChange={(e) => onFormDataChange({ ...formData, expiry_date: e.target.value })}
            />
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button onClick={onSubmit} disabled={isSubmitting}>
            {isSubmitting ? 'Submitting...' : 'Submit Exception'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};
