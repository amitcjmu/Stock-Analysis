import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Checkbox } from '@/components/ui/checkbox';
import type { CreateEngagementData } from './types'
import { CloudProviders } from './types'

interface EngagementScopeProps {
  formData: CreateEngagementData;
  onFormChange: (field: keyof CreateEngagementData, value: unknown) => void;
}

export const EngagementScope: React.FC<EngagementScopeProps> = ({
  formData,
  onFormChange
}) => {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Migration Scope</CardTitle>
        <CardDescription>Define the scope and target cloud provider</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="target_cloud_provider">Target Cloud Provider</Label>
          <Select value={formData.target_cloud_provider} onValueChange={(value) => onFormChange('target_cloud_provider', value)}>
            <SelectTrigger>
              <SelectValue placeholder="Select cloud provider" />
            </SelectTrigger>
            <SelectContent>
              {CloudProviders.map(provider => (
                <SelectItem key={provider.value} value={provider.value}>{provider.label}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div className="space-y-2">
          <Label>Migration Scope</Label>
          <div className="grid grid-cols-2 gap-2">
            <label className="flex items-center space-x-2">
              <Checkbox
                checked={formData.scope_applications}
                onCheckedChange={(checked) => onFormChange('scope_applications', checked)}
              />
              <span className="text-sm">Applications</span>
            </label>
            <label className="flex items-center space-x-2">
              <Checkbox
                checked={formData.scope_databases}
                onCheckedChange={(checked) => onFormChange('scope_databases', checked)}
              />
              <span className="text-sm">Databases</span>
            </label>
            <label className="flex items-center space-x-2">
              <Checkbox
                checked={formData.scope_infrastructure}
                onCheckedChange={(checked) => onFormChange('scope_infrastructure', checked)}
              />
              <span className="text-sm">Infrastructure</span>
            </label>
            <label className="flex items-center space-x-2">
              <Checkbox
                checked={formData.scope_data_migration}
                onCheckedChange={(checked) => onFormChange('scope_data_migration', checked)}
              />
              <span className="text-sm">Data Migration</span>
            </label>
          </div>
        </div>

        <div className="space-y-2">
          <Label htmlFor="business_objectives">Business Objectives</Label>
          <Textarea
            id="business_objectives"
            placeholder="Enter business objectives (one per line)"
            value={formData.business_objectives.join('\n')}
            onChange={(e) => {
              const newArray = e.target.value.split('\n').filter(item => item.trim());
              onFormChange('business_objectives', newArray);
            }}
            rows={3}
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="compliance_requirements">Compliance Requirements</Label>
          <Textarea
            id="compliance_requirements"
            placeholder="Enter compliance requirements (one per line)"
            value={formData.compliance_requirements.join('\n')}
            onChange={(e) => {
              const newArray = e.target.value.split('\n').filter(item => item.trim());
              onFormChange('compliance_requirements', newArray);
            }}
            rows={3}
          />
        </div>
      </CardContent>
    </Card>
  );
};
