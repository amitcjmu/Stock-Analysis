import React from 'react';
import { AlertCircle } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import type { CreateEngagementData } from './types'
import { Currencies } from './types'

interface EngagementTimelineProps {
  formData: CreateEngagementData;
  errors: Record<string, string>;
  onFormChange: (field: keyof CreateEngagementData, value: unknown) => void;
}

export const EngagementTimeline: React.FC<EngagementTimelineProps> = ({
  formData,
  errors,
  onFormChange
}) => {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Timeline & Budget</CardTitle>
        <CardDescription>Project timeline and financial information</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label htmlFor="estimated_start_date">Estimated Start Date *</Label>
            <Input
              id="estimated_start_date"
              type="date"
              value={formData.estimated_start_date}
              onChange={(e) => onFormChange('estimated_start_date', e.target.value)}
              required
            />
            {errors.estimated_start_date && (
              <p className="text-sm text-red-600 flex items-center gap-1">
                <AlertCircle className="w-3 h-3" />
                {errors.estimated_start_date}
              </p>
            )}
          </div>

          <div className="space-y-2">
            <Label htmlFor="estimated_end_date">Estimated End Date *</Label>
            <Input
              id="estimated_end_date"
              type="date"
              value={formData.estimated_end_date}
              onChange={(e) => onFormChange('estimated_end_date', e.target.value)}
              required
            />
            {errors.estimated_end_date && (
              <p className="text-sm text-red-600 flex items-center gap-1">
                <AlertCircle className="w-3 h-3" />
                {errors.estimated_end_date}
              </p>
            )}
          </div>

          <div className="space-y-2">
            <Label htmlFor="budget">Budget</Label>
            <Input
              id="budget"
              type="number"
              value={formData.budget}
              onChange={(e) => onFormChange('budget', e.target.value)}
              placeholder="0.00"
              min="0"
              step="0.01"
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
                  <SelectItem key={currency.value} value={currency.value}>
                    {currency.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}; 