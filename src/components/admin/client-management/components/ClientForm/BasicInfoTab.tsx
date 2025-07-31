import React from 'react';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Industries, CompanySizes, SubscriptionTiers } from '../../types';
import type { ClientFormData } from '../../types';

interface BasicInfoTabProps {
  formData: ClientFormData;
  onFormChange: (field: keyof ClientFormData, value: string | string[]) => void;
}

export const BasicInfoTab: React.FC<BasicInfoTabProps> = ({ formData, onFormChange }) => {
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label htmlFor="account_name">Account Name *</Label>
          <Input
            id="account_name"
            value={formData.account_name}
            onChange={(e) => onFormChange('account_name', e.target.value)}
            placeholder="Enter company name"
            required
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="industry">Industry *</Label>
          <Select
            value={formData.industry}
            onValueChange={(value) => onFormChange('industry', value)}
          >
            <SelectTrigger>
              <SelectValue placeholder="Select industry" />
            </SelectTrigger>
            <SelectContent>
              {Industries.map((industry) => (
                <SelectItem key={industry} value={industry}>
                  {industry}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div className="space-y-2">
          <Label htmlFor="company_size">Company Size *</Label>
          <Select
            value={formData.company_size}
            onValueChange={(value) => onFormChange('company_size', value)}
          >
            <SelectTrigger>
              <SelectValue placeholder="Select company size" />
            </SelectTrigger>
            <SelectContent>
              {CompanySizes.map((size) => (
                <SelectItem key={size} value={size}>
                  {size}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div className="space-y-2">
          <Label htmlFor="subscription_tier">Subscription Tier</Label>
          <Select
            value={formData.subscription_tier}
            onValueChange={(value) => onFormChange('subscription_tier', value)}
          >
            <SelectTrigger>
              <SelectValue placeholder="Select tier" />
            </SelectTrigger>
            <SelectContent>
              {SubscriptionTiers.map((tier) => (
                <SelectItem key={tier.value} value={tier.value}>
                  {tier.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>

      <div className="space-y-4">
        <h3 className="text-lg font-medium">Contact Information</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label htmlFor="primary_contact_name">Primary Contact Name *</Label>
            <Input
              id="primary_contact_name"
              value={formData.primary_contact_name}
              onChange={(e) => onFormChange('primary_contact_name', e.target.value)}
              placeholder="John Doe"
              required
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="primary_contact_email">Primary Contact Email *</Label>
            <Input
              id="primary_contact_email"
              type="email"
              value={formData.primary_contact_email}
              onChange={(e) => onFormChange('primary_contact_email', e.target.value)}
              placeholder="john@company.com"
              required
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="primary_contact_phone">Primary Contact Phone</Label>
            <Input
              id="primary_contact_phone"
              type="tel"
              value={formData.primary_contact_phone || ''}
              onChange={(e) => onFormChange('primary_contact_phone', e.target.value)}
              placeholder="+1 (555) 123-4567"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="billing_contact_email">Billing Contact Email</Label>
            <Input
              id="billing_contact_email"
              type="email"
              value={formData.billing_contact_email || ''}
              onChange={(e) => onFormChange('billing_contact_email', e.target.value)}
              placeholder="billing@company.com"
            />
          </div>
        </div>
      </div>

      <div className="space-y-4">
        <h3 className="text-lg font-medium">Location</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label htmlFor="headquarters_location">Headquarters Location</Label>
            <Input
              id="headquarters_location"
              value={formData.headquarters_location || ''}
              onChange={(e) => onFormChange('headquarters_location', e.target.value)}
              placeholder="New York, NY"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="time_zone">Time Zone</Label>
            <Input
              id="time_zone"
              value={formData.time_zone || ''}
              onChange={(e) => onFormChange('time_zone', e.target.value)}
              placeholder="America/New_York"
            />
          </div>
        </div>
      </div>
    </div>
  );
};
