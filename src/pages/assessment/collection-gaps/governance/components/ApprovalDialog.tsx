/**
 * ApprovalDialog Component
 * Dialog for creating approval requests
 */

import React from 'react';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import type { ApprovalFormData } from '../types';

interface ApprovalDialogProps {
  isOpen: boolean;
  onOpenChange: (open: boolean) => void;
  formData: ApprovalFormData;
  onFormDataChange: (data: ApprovalFormData) => void;
  isSubmitting: boolean;
  onSubmit: () => void;
}

export const ApprovalDialog: React.FC<ApprovalDialogProps> = ({
  isOpen,
  onOpenChange,
  formData,
  onFormDataChange,
  isSubmitting,
  onSubmit
}) => {
  return (
    <Dialog open={isOpen} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>Submit Approval Request</DialogTitle>
          <DialogDescription>
            Request approval for policy deviations, risk acceptance, or compliance waivers
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-4 max-h-96 overflow-y-auto">
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="approval_title">Title *</Label>
              <Input
                id="approval_title"
                value={formData.title}
                onChange={(e) => onFormDataChange({ ...formData, title: e.target.value })}
                placeholder="Brief title for the request"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="request_type">Request Type</Label>
              <Select
                value={formData.request_type}
                onValueChange={(value: 'policy_exception' | 'process_deviation' | 'risk_acceptance' | 'compliance_waiver') =>
                  onFormDataChange({ ...formData, request_type: value })
                }
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="policy_exception">Policy Exception</SelectItem>
                  <SelectItem value="process_deviation">Process Deviation</SelectItem>
                  <SelectItem value="risk_acceptance">Risk Acceptance</SelectItem>
                  <SelectItem value="compliance_waiver">Compliance Waiver</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
          <div className="space-y-2">
            <Label htmlFor="approval_description">Description</Label>
            <Textarea
              id="approval_description"
              value={formData.description}
              onChange={(e) => onFormDataChange({ ...formData, description: e.target.value })}
              placeholder="Detailed description of the request"
              rows={3}
            />
          </div>
          <div className="grid grid-cols-3 gap-4">
            <div className="space-y-2">
              <Label htmlFor="approval_scope">Scope</Label>
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
              <Label htmlFor="approval_scope_id">Scope ID</Label>
              <Input
                id="approval_scope_id"
                value={formData.scope_id}
                onChange={(e) => onFormDataChange({ ...formData, scope_id: e.target.value })}
                placeholder="Specific ID"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="approval_priority">Priority</Label>
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
            <Label htmlFor="business_justification">Business Justification *</Label>
            <Textarea
              id="business_justification"
              value={formData.business_justification}
              onChange={(e) => onFormDataChange({ ...formData, business_justification: e.target.value })}
              placeholder="Explain the business need for this request"
              rows={3}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="risk_assessment">Risk Assessment</Label>
            <Textarea
              id="risk_assessment"
              value={formData.risk_assessment}
              onChange={(e) => onFormDataChange({ ...formData, risk_assessment: e.target.value })}
              placeholder="Assess the risks associated with this request"
              rows={2}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="mitigation_measures">Mitigation Measures</Label>
            <Textarea
              id="mitigation_measures"
              value={formData.mitigation_measures}
              onChange={(e) => onFormDataChange({ ...formData, mitigation_measures: e.target.value })}
              placeholder="Describe how risks will be mitigated"
              rows={2}
            />
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button onClick={onSubmit} disabled={isSubmitting}>
            {isSubmitting ? 'Submitting...' : 'Submit Request'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};
