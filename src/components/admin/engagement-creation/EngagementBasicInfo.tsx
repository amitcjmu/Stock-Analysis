import React from 'react';
import { AlertCircle } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import type { CreateEngagementData, ClientAccount } from './types';
import { EngagementStatuses, Phases, RiskLevels } from './types';

interface EngagementBasicInfoProps {
  formData: CreateEngagementData;
  clientAccounts: ClientAccount[];
  errors: Record<string, string>;
  onFormChange: (field: keyof CreateEngagementData, value: unknown) => void;
}

export const EngagementBasicInfo: React.FC<EngagementBasicInfoProps> = ({
  formData,
  clientAccounts,
  errors,
  onFormChange,
}) => {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Basic Information</CardTitle>
        <CardDescription>Engagement details and client assignment</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label htmlFor="engagement_name">Engagement Name *</Label>
            <Input
              id="engagement_name"
              value={formData.engagement_name}
              onChange={(e) => onFormChange('engagement_name', e.target.value)}
              placeholder="Enter engagement name"
              required
            />
            {errors.engagement_name && (
              <p className="text-sm text-red-600 flex items-center gap-1">
                <AlertCircle className="w-3 h-3" />
                {errors.engagement_name}
              </p>
            )}
          </div>

          <div className="space-y-2">
            <Label htmlFor="client_account_id">Client Account *</Label>
            <Select
              value={formData.client_account_id}
              onValueChange={(value) => onFormChange('client_account_id', value)}
            >
              <SelectTrigger>
                <SelectValue placeholder="Select client account" />
              </SelectTrigger>
              <SelectContent>
                {clientAccounts.map((client) => (
                  <SelectItem key={client.id} value={client.id}>
                    {client.account_name} ({client.industry})
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            {errors.client_account_id && (
              <p className="text-sm text-red-600 flex items-center gap-1">
                <AlertCircle className="w-3 h-3" />
                {errors.client_account_id}
              </p>
            )}
          </div>

          <div className="space-y-2">
            <Label htmlFor="project_manager">Project Manager *</Label>
            <Input
              id="project_manager"
              value={formData.project_manager}
              onChange={(e) => onFormChange('project_manager', e.target.value)}
              placeholder="Enter project manager name"
              required
            />
            {errors.project_manager && (
              <p className="text-sm text-red-600 flex items-center gap-1">
                <AlertCircle className="w-3 h-3" />
                {errors.project_manager}
              </p>
            )}
          </div>

          <div className="space-y-2">
            <Label htmlFor="engagement_status">Status</Label>
            <Select
              value={formData.engagement_status}
              onValueChange={(value) => onFormChange('engagement_status', value)}
            >
              <SelectTrigger>
                <SelectValue placeholder="Select status" />
              </SelectTrigger>
              <SelectContent>
                {EngagementStatuses.map((status) => (
                  <SelectItem key={status.value} value={status.value}>
                    {status.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label htmlFor="phase">Current Phase</Label>
            <Select value={formData.phase} onValueChange={(value) => onFormChange('phase', value)}>
              <SelectTrigger>
                <SelectValue placeholder="Select phase" />
              </SelectTrigger>
              <SelectContent>
                {Phases.map((phase) => (
                  <SelectItem key={phase.value} value={phase.value}>
                    {phase.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label htmlFor="risk_level">Risk Level</Label>
            <Select
              value={formData.risk_level}
              onValueChange={(value) => onFormChange('risk_level', value)}
            >
              <SelectTrigger>
                <SelectValue placeholder="Select risk level" />
              </SelectTrigger>
              <SelectContent>
                {RiskLevels.map((risk) => (
                  <SelectItem key={risk.value} value={risk.value}>
                    {risk.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>

        <div className="space-y-2">
          <Label htmlFor="description">Description</Label>
          <Textarea
            id="description"
            value={formData.description}
            onChange={(e) => onFormChange('description', e.target.value)}
            placeholder="Enter engagement description and objectives"
            rows={3}
          />
        </div>
      </CardContent>
    </Card>
  );
};
