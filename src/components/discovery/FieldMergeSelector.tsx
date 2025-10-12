/**
 * Field Merge Selector Component
 *
 * Displays toggleable field selector for merge conflict resolution action.
 * Shows side-by-side comparison and allows user to choose "existing" or "new" for each field.
 *
 * CC: Only shows mergeable fields from MERGEABLE_FIELDS allowlist
 */

import React, { useState, useEffect, useRef } from 'react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { ArrowRight, Check } from 'lucide-react';
import type { AssetConflictData, FieldSource, MergeFieldSelections } from '@/types/assetConflict';
import { MERGEABLE_FIELDS, FIELD_LABELS } from '@/types/assetConflict';

interface FieldMergeSelectorProps {
  existing_asset: AssetConflictData;
  new_asset: AssetConflictData;
  onChange: (selections: MergeFieldSelections) => void;
  initialSelections?: MergeFieldSelections;
}

/**
 * Helper to get display value for a field
 */
function getDisplayValue(value: unknown): string {
  if (value === null || value === undefined) {
    return '(empty)';
  }
  if (typeof value === 'object') {
    return JSON.stringify(value);
  }
  return String(value);
}

/**
 * Helper to check if field values differ
 */
function fieldsDiffer(existing: unknown, newValue: unknown): boolean {
  // Handle null/undefined equality
  if (existing === newValue) return false;
  if (existing == null && newValue == null) return false;
  if (existing == null || newValue == null) return true;

  // For objects, do deep comparison
  if (typeof existing === 'object' && typeof newValue === 'object') {
    return JSON.stringify(existing) !== JSON.stringify(newValue);
  }

  return existing !== newValue;
}

export const FieldMergeSelector: React.FC<FieldMergeSelectorProps> = ({
  existing_asset,
  new_asset,
  onChange,
  initialSelections = {},
}) => {
  // Track selections: field_name -> 'existing' | 'new'
  const [selections, setSelections] = useState<MergeFieldSelections>(initialSelections);

  // Track initial mount to prevent premature onChange call (Qodo Bot feedback)
  const isInitialMount = useRef(true);

  // Get fields that exist in either asset and are mergeable
  const mergeableFields = MERGEABLE_FIELDS.filter((field) => {
    const existingValue = existing_asset[field as keyof AssetConflictData];
    const newValue = new_asset[field as keyof AssetConflictData];
    // Include field if at least one asset has a value
    return existingValue != null || newValue != null;
  });

  // Group fields by category for better UX
  const fieldCategories = {
    Technical: [
      'operating_system',
      'os_version',
      'cpu_cores',
      'memory_gb',
      'storage_gb',
    ],
    Network: ['ip_address', 'fqdn', 'mac_address'],
    Infrastructure: [
      'environment',
      'location',
      'datacenter',
      'rack_location',
      'availability_zone',
    ],
    Business: [
      'business_owner',
      'technical_owner',
      'department',
      'application_name',
      'technology_stack',
      'criticality',
      'business_criticality',
    ],
    Migration: [
      'six_r_strategy',
      'migration_priority',
      'migration_complexity',
      'migration_wave',
    ],
    Other: ['description'],
  };

  // Notify parent of selection changes (skip on initial mount to prevent premature updates)
  useEffect(() => {
    // Skip effect on initial mount - parent already has initialSelections
    if (isInitialMount.current) {
      isInitialMount.current = false;
      return;
    }

    onChange(selections);
  }, [selections, onChange]);

  const handleSelectField = (fieldName: string, source: FieldSource) => {
    setSelections((prev) => ({
      ...prev,
      [fieldName]: source,
    }));
  };

  const handleSelectAll = (source: FieldSource) => {
    const allSelections: MergeFieldSelections = {};
    mergeableFields.forEach((field) => {
      allSelections[field] = source;
    });
    setSelections(allSelections);
  };

  return (
    <Card className="border-blue-200">
      <CardHeader className="pb-3">
        <CardTitle className="text-base flex items-center justify-between">
          <span>Select Fields to Merge</span>
          <div className="flex gap-2">
            <Button
              size="sm"
              variant="outline"
              onClick={() => handleSelectAll('existing')}
            >
              Select All Existing
            </Button>
            <Button size="sm" variant="outline" onClick={() => handleSelectAll('new')}>
              Select All New
            </Button>
          </div>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4 max-h-96 overflow-y-auto">
        {Object.entries(fieldCategories).map(([category, categoryFields]) => {
          // Filter to only fields present in this conflict
          const fieldsInCategory = categoryFields.filter((field) =>
            mergeableFields.includes(field)
          );

          if (fieldsInCategory.length === 0) return null;

          return (
            <div key={category} className="space-y-2">
              <h4 className="text-sm font-semibold text-gray-700 border-b pb-1">
                {category}
              </h4>
              {fieldsInCategory.map((field) => {
                const existingValue = existing_asset[field as keyof AssetConflictData];
                const newValue = new_asset[field as keyof AssetConflictData];
                const differs = fieldsDiffer(existingValue, newValue);
                const currentSelection = selections[field] || 'existing'; // Default to existing

                return (
                  <div
                    key={field}
                    className={`grid grid-cols-5 gap-2 p-2 rounded-lg border ${
                      differs ? 'bg-yellow-50 border-yellow-200' : 'bg-gray-50 border-gray-200'
                    }`}
                  >
                    {/* Field Label */}
                    <div className="col-span-1 flex items-center">
                      <div>
                        <p className="text-xs font-medium text-gray-700">
                          {FIELD_LABELS[field] || field}
                        </p>
                        {differs && (
                          <Badge variant="outline" className="text-xs mt-1">
                            Different
                          </Badge>
                        )}
                      </div>
                    </div>

                    {/* Existing Value */}
                    <div className="col-span-2">
                      <Button
                        size="sm"
                        variant={currentSelection === 'existing' ? 'default' : 'outline'}
                        onClick={() => handleSelectField(field, 'existing')}
                        className="w-full justify-start text-left h-auto py-2 px-3"
                      >
                        <div className="flex items-start gap-2 w-full">
                          {currentSelection === 'existing' && (
                            <Check className="h-4 w-4 shrink-0 mt-0.5" />
                          )}
                          <div className="flex-1 min-w-0">
                            <p className="text-xs text-gray-500 mb-1">Existing</p>
                            <p className="text-sm break-words">
                              {getDisplayValue(existingValue)}
                            </p>
                          </div>
                        </div>
                      </Button>
                    </div>

                    {/* New Value */}
                    <div className="col-span-2">
                      <Button
                        size="sm"
                        variant={currentSelection === 'new' ? 'default' : 'outline'}
                        onClick={() => handleSelectField(field, 'new')}
                        className="w-full justify-start text-left h-auto py-2 px-3"
                      >
                        <div className="flex items-start gap-2 w-full">
                          {currentSelection === 'new' && (
                            <Check className="h-4 w-4 shrink-0 mt-0.5" />
                          )}
                          <div className="flex-1 min-w-0">
                            <p className="text-xs text-gray-500 mb-1">New</p>
                            <p className="text-sm break-words">
                              {getDisplayValue(newValue)}
                            </p>
                          </div>
                        </div>
                      </Button>
                    </div>
                  </div>
                );
              })}
            </div>
          );
        })}

        {mergeableFields.length === 0 && (
          <div className="text-center py-8 text-gray-500">
            <p>No mergeable fields found in these assets.</p>
            <p className="text-sm mt-2">Consider using "Keep Existing" or "Replace with New" instead.</p>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default FieldMergeSelector;
