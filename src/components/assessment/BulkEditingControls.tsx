import React from 'react'
import type { useState } from 'react'
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import type { ComponentTreatment } from '@/hooks/useAssessmentFlow';
import { Edit3, Check, X, Copy } from 'lucide-react';

interface BulkEditingControlsProps {
  enabled: boolean;
  onToggle: (enabled: boolean) => void;
  selectedComponents: string[];
  onSelectionChange: (selected: string[]) => void;
  componentTreatments: ComponentTreatment[];
  onBulkUpdate: (updates: Partial<ComponentTreatment>) => void;
}

const SIX_R_STRATEGIES = [
  'rehost',
  'replatform',
  'refactor',
  'repurchase',
  'retire',
  'retain'
];

export const BulkEditingControls: React.FC<BulkEditingControlsProps> = ({
  enabled,
  onToggle,
  selectedComponents,
  onSelectionChange,
  componentTreatments,
  onBulkUpdate
}) => {
  const [bulkStrategy, setBulkStrategy] = useState<string>('');
  const [bulkRationale, setBulkRationale] = useState<string>('');

  const handleSelectAll = () => {
    if (selectedComponents.length === componentTreatments.length) {
      onSelectionChange([]);
    } else {
      onSelectionChange(componentTreatments.map(ct => ct.component_name));
    }
  };

  const handleBulkApply = () => {
    if (bulkStrategy && selectedComponents.length > 0) {
      onBulkUpdate({
        recommended_strategy: bulkStrategy,
        ...(bulkRationale && { rationale: bulkRationale })
      });
      setBulkStrategy('');
      setBulkRationale('');
    }
  };

  if (!enabled) {
    return (
      <Card className="border-blue-200 bg-blue-50/30">
        <CardContent className="pt-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <Switch
                id="bulk-edit"
                checked={enabled}
                onCheckedChange={onToggle}
              />
              <Label htmlFor="bulk-edit" className="text-sm font-medium">
                Enable Bulk Editing
              </Label>
            </div>
            <Badge variant="outline">
              <Edit3 className="h-3 w-3 mr-1" />
              Bulk Mode
            </Badge>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="border-blue-200 bg-blue-50/30">
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Edit3 className="h-5 w-5" />
            <span>Bulk Editing Mode</span>
          </div>
          <Button variant="outline" size="sm" onClick={() => onToggle(false)}>
            <X className="h-4 w-4 mr-1" />
            Exit
          </Button>
        </CardTitle>
        <CardDescription>
          Select multiple components to apply changes in bulk
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Selection Controls */}
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Button variant="outline" size="sm" onClick={handleSelectAll}>
              <Copy className="h-4 w-4 mr-1" />
              {selectedComponents.length === componentTreatments.length ? 'Deselect All' : 'Select All'}
            </Button>
            <Badge variant="secondary">
              {selectedComponents.length} of {componentTreatments.length} selected
            </Badge>
          </div>
        </div>

        {/* Bulk Edit Form */}
        {selectedComponents.length > 0 && (
          <div className="space-y-3 p-3 border border-blue-200 rounded-lg bg-white">
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-2">
                <Label className="text-sm">Strategy</Label>
                <Select value={bulkStrategy} onValueChange={setBulkStrategy}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select strategy" />
                  </SelectTrigger>
                  <SelectContent>
                    {SIX_R_STRATEGIES.map((strategy) => (
                      <SelectItem key={strategy} value={strategy}>
                        {strategy.charAt(0).toUpperCase() + strategy.slice(1)}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="flex items-end">
                <Button 
                  onClick={handleBulkApply}
                  disabled={!bulkStrategy || selectedComponents.length === 0}
                  className="w-full"
                >
                  <Check className="h-4 w-4 mr-1" />
                  Apply to {selectedComponents.length} Components
                </Button>
              </div>
            </div>
          </div>
        )}

        {/* Selected Components List */}
        {selectedComponents.length > 0 && (
          <div className="space-y-2">
            <Label className="text-sm font-medium">Selected Components:</Label>
            <div className="flex flex-wrap gap-1">
              {selectedComponents.map((componentName) => (
                <Badge key={componentName} variant="outline" className="text-xs">
                  {componentName}
                </Badge>
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
};