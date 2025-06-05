import React from 'react';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import { 
  EngagementFormData, 
  Client, 
  MigrationScopes, 
  CloudProviders, 
  MigrationPhases, 
  Currencies 
} from './types';

interface EngagementFormProps {
  formData: EngagementFormData;
  onFormChange: (field: keyof EngagementFormData, value: any) => void;
  clients: Client[];
}

export const EngagementForm: React.FC<EngagementFormProps> = React.memo(({ 
  formData, 
  onFormChange, 
  clients 
}) => (
  <div className="space-y-6 max-h-96 overflow-y-auto">
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
      </div>
      
      <div className="space-y-2">
        <Label htmlFor="client_account_id">Client Account *</Label>
        <Select value={formData.client_account_id} onValueChange={(value) => onFormChange('client_account_id', value)}>
          <SelectTrigger>
            <SelectValue placeholder="Select client" />
          </SelectTrigger>
          <SelectContent>
            {clients.map(client => (
              <SelectItem key={client.id} value={client.id}>{client.account_name}</SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <div className="space-y-2">
        <Label htmlFor="migration_scope">Migration Scope *</Label>
        <Select value={formData.migration_scope} onValueChange={(value) => onFormChange('migration_scope', value)}>
          <SelectTrigger>
            <SelectValue placeholder="Select scope" />
          </SelectTrigger>
          <SelectContent>
            {MigrationScopes.map(scope => (
              <SelectItem key={scope.value} value={scope.value}>{scope.label}</SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <div className="space-y-2">
        <Label htmlFor="target_cloud_provider">Target Cloud Provider *</Label>
        <Select value={formData.target_cloud_provider} onValueChange={(value) => onFormChange('target_cloud_provider', value)}>
          <SelectTrigger>
            <SelectValue placeholder="Select provider" />
          </SelectTrigger>
          <SelectContent>
            {CloudProviders.map(provider => (
              <SelectItem key={provider.value} value={provider.value}>{provider.label}</SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <div className="space-y-2">
        <Label htmlFor="migration_phase">Migration Phase *</Label>
        <Select value={formData.migration_phase} onValueChange={(value) => onFormChange('migration_phase', value)}>
          <SelectTrigger>
            <SelectValue placeholder="Select phase" />
          </SelectTrigger>
          <SelectContent>
            {MigrationPhases.map(phase => (
              <SelectItem key={phase.value} value={phase.value}>{phase.label}</SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <div className="space-y-2">
        <Label htmlFor="engagement_manager">Engagement Manager *</Label>
        <Input
          id="engagement_manager"
          value={formData.engagement_manager}
          onChange={(e) => onFormChange('engagement_manager', e.target.value)}
          placeholder="Enter engagement manager name"
          required
        />
      </div>

      <div className="space-y-2">
        <Label htmlFor="technical_lead">Technical Lead *</Label>
        <Input
          id="technical_lead"
          value={formData.technical_lead}
          onChange={(e) => onFormChange('technical_lead', e.target.value)}
          placeholder="Enter technical lead name"
          required
        />
      </div>

      <div className="space-y-2">
        <Label htmlFor="start_date">Start Date *</Label>
        <Input
          id="start_date"
          type="date"
          value={formData.start_date}
          onChange={(e) => onFormChange('start_date', e.target.value)}
          required
        />
      </div>

      <div className="space-y-2">
        <Label htmlFor="end_date">End Date *</Label>
        <Input
          id="end_date"
          type="date"
          value={formData.end_date}
          onChange={(e) => onFormChange('end_date', e.target.value)}
          required
        />
      </div>

      <div className="space-y-2">
        <Label htmlFor="budget">Budget</Label>
        <Input
          id="budget"
          type="number"
          value={formData.budget || ''}
          onChange={(e) => onFormChange('budget', parseFloat(e.target.value) || 0)}
          placeholder="Enter budget amount"
        />
      </div>

      <div className="space-y-2">
        <Label htmlFor="budget_currency">Budget Currency</Label>
        <Select value={formData.budget_currency} onValueChange={(value) => onFormChange('budget_currency', value)}>
          <SelectTrigger>
            <SelectValue placeholder="Select currency" />
          </SelectTrigger>
          <SelectContent>
            {Currencies.map(currency => (
              <SelectItem key={currency.value} value={currency.value}>{currency.label}</SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>
    </div>

    <div className="space-y-2">
      <Label htmlFor="engagement_description">Description</Label>
      <Textarea
        id="engagement_description"
        value={formData.engagement_description}
        onChange={(e) => onFormChange('engagement_description', e.target.value)}
        placeholder="Enter engagement description..."
        rows={3}
      />
    </div>
  </div>
)); 