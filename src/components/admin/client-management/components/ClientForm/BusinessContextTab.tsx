import React from 'react';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Input } from '@/components/ui/input';
import { CloudProviders, BusinessPriorities } from '../../types';
import type { ClientFormData } from '../../types';

interface BusinessContextTabProps {
  formData: ClientFormData;
  onFormChange: (field: keyof ClientFormData, value: string | string[]) => void;
}

export const BusinessContextTab: React.FC<BusinessContextTabProps> = ({ formData, onFormChange }) => {
  const handleMultiSelect = (field: keyof ClientFormData, value: string, checked: boolean) => {
    const currentValues = (formData[field] as string[]) || [];
    if (checked) {
      onFormChange(field, [...currentValues, value]);
    } else {
      onFormChange(field, currentValues.filter(v => v !== value));
    }
  };

  const businessObjectives = [
    'Reduce infrastructure costs',
    'Improve application performance',
    'Enhance security posture',
    'Increase operational efficiency',
    'Enable digital transformation',
    'Improve disaster recovery',
    'Achieve compliance requirements',
    'Modernize legacy applications'
  ];

  return (
    <div className="space-y-6">
      <div>
        <Label htmlFor="description">Company Description</Label>
        <Textarea
          id="description"
          value={formData.description || ''}
          onChange={(e) => onFormChange('description', e.target.value)}
          placeholder="Brief description of the company and their business context"
          rows={3}
        />
      </div>

      <div>
        <Label htmlFor="migration_timeline">Migration Timeline</Label>
        <Input
          id="migration_timeline"
          value={formData.migration_timeline || ''}
          onChange={(e) => onFormChange('migration_timeline', e.target.value)}
          placeholder="12-18 months"
        />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div>
          <Label className="text-base font-medium">Business Objectives</Label>
          <p className="text-sm text-gray-600 mb-3">Select all that apply</p>
          <div className="space-y-2">
            {businessObjectives.map((objective) => (
              <div key={objective} className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  id={`objective-${objective}`}
                  checked={formData.business_objectives.includes(objective)}
                  onChange={(e) => handleMultiSelect('business_objectives', objective, e.target.checked)}
                  className="rounded border-gray-300"
                />
                <Label htmlFor={`objective-${objective}`} className="text-sm">{objective}</Label>
              </div>
            ))}
          </div>
        </div>

        <div>
          <Label className="text-base font-medium">Target Cloud Providers</Label>
          <p className="text-sm text-gray-600 mb-3">Select preferred cloud platforms</p>
          <div className="space-y-2">
            {CloudProviders.map((provider) => (
              <div key={provider.value} className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  id={`provider-${provider.value}`}
                  checked={formData.target_cloud_providers.includes(provider.value)}
                  onChange={(e) => handleMultiSelect('target_cloud_providers', provider.value, e.target.checked)}
                  className="rounded border-gray-300"
                />
                <Label htmlFor={`provider-${provider.value}`} className="text-sm">{provider.label}</Label>
              </div>
            ))}
          </div>
        </div>

        <div>
          <Label className="text-base font-medium">Business Priorities</Label>
          <p className="text-sm text-gray-600 mb-3">Rank key business priorities</p>
          <div className="space-y-2">
            {BusinessPriorities.map((priority) => (
              <div key={priority.value} className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  id={`priority-${priority.value}`}
                  checked={formData.business_priorities.includes(priority.value)}
                  onChange={(e) => handleMultiSelect('business_priorities', priority.value, e.target.checked)}
                  className="rounded border-gray-300"
                />
                <Label htmlFor={`priority-${priority.value}`} className="text-sm">{priority.label}</Label>
              </div>
            ))}
          </div>
        </div>

        <div>
          <Label className="text-base font-medium">Compliance Requirements</Label>
          <p className="text-sm text-gray-600 mb-3">Select applicable compliance standards</p>
          <div className="space-y-2">
            {['SOC 2', 'HIPAA', 'PCI DSS', 'GDPR', 'ISO 27001', 'FedRAMP', 'FISMA', 'SOX'].map((compliance) => (
              <div key={compliance} className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  id={`compliance-${compliance}`}
                  checked={formData.compliance_requirements.includes(compliance)}
                  onChange={(e) => handleMultiSelect('compliance_requirements', compliance, e.target.checked)}
                  className="rounded border-gray-300"
                />
                <Label htmlFor={`compliance-${compliance}`} className="text-sm">{compliance}</Label>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};