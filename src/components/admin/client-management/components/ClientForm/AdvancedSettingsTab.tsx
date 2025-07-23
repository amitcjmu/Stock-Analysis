import React from 'react';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import type { ClientFormData } from '../../types';

interface AdvancedSettingsTabProps {
  formData: ClientFormData;
  onFormChange: (field: keyof ClientFormData, value: string | string[]) => void;
}

export const AdvancedSettingsTab: React.FC<AdvancedSettingsTabProps> = ({ formData, onFormChange }) => {
  return (
    <div className="space-y-6">
      <div className="space-y-4">
        <h3 className="text-lg font-medium">Agent Preferences</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <Label htmlFor="confidence_threshold">Field Mapping Confidence</Label>
            <Select 
              value={formData.agent_preferences?.confidence_thresholds?.field_mapping?.toString() || '0.8'} 
              onValueChange={(value) => onFormChange('agent_preferences', { 
                ...formData.agent_preferences, 
                confidence_thresholds: {
                  ...formData.agent_preferences?.confidence_thresholds,
                  field_mapping: parseFloat(value)
                }
              })}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="0.7">70% - Permissive</SelectItem>
                <SelectItem value="0.8">80% - Balanced</SelectItem>
                <SelectItem value="0.9">90% - Conservative</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div>
            <Label htmlFor="dependency_confidence">Dependency Detection Confidence</Label>
            <Select 
              value={formData.agent_preferences?.confidence_thresholds?.dependency_detection?.toString() || '0.75'} 
              onValueChange={(value) => onFormChange('agent_preferences', { 
                ...formData.agent_preferences, 
                confidence_thresholds: {
                  ...formData.agent_preferences?.confidence_thresholds,
                  dependency_detection: parseFloat(value)
                }
              })}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="0.7">70% - Permissive</SelectItem>
                <SelectItem value="0.75">75% - Balanced</SelectItem>
                <SelectItem value="0.85">85% - Conservative</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div>
            <Label htmlFor="risk_confidence">Risk Assessment Confidence</Label>
            <Select 
              value={formData.agent_preferences?.confidence_thresholds?.risk_assessment?.toString() || '0.85'} 
              onValueChange={(value) => onFormChange('agent_preferences', { 
                ...formData.agent_preferences, 
                confidence_thresholds: {
                  ...formData.agent_preferences?.confidence_thresholds,
                  risk_assessment: parseFloat(value)
                }
              })}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="0.8">80% - Permissive</SelectItem>
                <SelectItem value="0.85">85% - Balanced</SelectItem>
                <SelectItem value="0.9">90% - Conservative</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div>
            <Label htmlFor="escalation_mode">Escalation Mode</Label>
            <Select 
              value={formData.agent_preferences?.escalation_mode || 'balanced'} 
              onValueChange={(value) => onFormChange('agent_preferences', { 
                ...formData.agent_preferences, 
                escalation_mode: value 
              })}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="minimal">Minimal - Only critical issues</SelectItem>
                <SelectItem value="balanced">Balanced - Important decisions</SelectItem>
                <SelectItem value="frequent">Frequent - Most decisions</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>
      </div>

      <div className="space-y-4">
        <h3 className="text-lg font-medium">Platform Settings</h3>
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label htmlFor="enable_notifications">Enable Notifications</Label>
              <p className="text-sm text-gray-600">Send email notifications for important events</p>
            </div>
            <Switch
              id="enable_notifications"
              checked={formData.platform_settings?.enable_notifications || false}
              onCheckedChange={(checked) => onFormChange('platform_settings', {
                ...formData.platform_settings,
                enable_notifications: checked
              })}
            />
          </div>

          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label htmlFor="enable_auto_discovery">Enable Auto-Discovery</Label>
              <p className="text-sm text-gray-600">Automatically discover new applications and dependencies</p>
            </div>
            <Switch
              id="enable_auto_discovery"
              checked={formData.platform_settings?.enable_auto_discovery || false}
              onCheckedChange={(checked) => onFormChange('platform_settings', {
                ...formData.platform_settings,
                enable_auto_discovery: checked
              })}
            />
          </div>

          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label htmlFor="enable_cost_optimization">Enable Cost Optimization</Label>
              <p className="text-sm text-gray-600">Provide cost optimization recommendations</p>
            </div>
            <Switch
              id="enable_cost_optimization"
              checked={formData.platform_settings?.enable_cost_optimization || false}
              onCheckedChange={(checked) => onFormChange('platform_settings', {
                ...formData.platform_settings,
                enable_cost_optimization: checked
              })}
            />
          </div>
        </div>
      </div>

      <div className="space-y-4">
        <h3 className="text-lg font-medium">Data Retention</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <Label htmlFor="retention_period">Retention Period (days)</Label>
            <Select 
              value={formData.platform_settings?.data_retention_days?.toString() || '90'} 
              onValueChange={(value) => onFormChange('platform_settings', { 
                ...formData.platform_settings, 
                data_retention_days: parseInt(value) 
              })}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="30">30 days</SelectItem>
                <SelectItem value="60">60 days</SelectItem>
                <SelectItem value="90">90 days</SelectItem>
                <SelectItem value="180">180 days</SelectItem>
                <SelectItem value="365">365 days</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div>
            <Label htmlFor="backup_frequency">Backup Frequency</Label>
            <Select 
              value={formData.platform_settings?.backup_frequency || 'daily'} 
              onValueChange={(value) => onFormChange('platform_settings', { 
                ...formData.platform_settings, 
                backup_frequency: value 
              })}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="hourly">Hourly</SelectItem>
                <SelectItem value="daily">Daily</SelectItem>
                <SelectItem value="weekly">Weekly</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>
      </div>
    </div>
  );
};