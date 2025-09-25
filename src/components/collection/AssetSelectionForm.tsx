/**
 * Asset Selection Form Component
 *
 * Handles the bootstrap_asset_selection questionnaire that allows users to select
 * assets for collection flows when no assets are initially selected.
 */

import React, { useState, useCallback } from 'react';
import { CheckSquare, Square, Search, Building, Server, Database, ArrowRight, AlertCircle } from 'lucide-react';

// UI Components
import { Button } from '@/components/ui/button';
import { Card, CardHeader, CardTitle, CardContent, CardFooter } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';

// Types
import type { AdaptiveFormData, CollectionFormData } from '@/components/collection/types';

export interface AssetSelectionFormProps {
  formData: AdaptiveFormData;
  formValues: CollectionFormData;
  onFieldChange: (fieldId: string, value: unknown) => void;
  onSubmit: (data: CollectionFormData) => void;
  isSubmitting?: boolean;
  className?: string;
}

interface AssetOption {
  id: string;
  name: string;
  displayText: string;
  type?: string;
}

/**
 * Parse asset options from the backend format: "AssetName (ID: asset_id)"
 */
const parseAssetOptions = (options: string[]): AssetOption[] => {
  return options.map((option, index) => {
    // Match the format "Name (ID: uuid)"
    const match = option.match(/^(.+?)\s*\(ID:\s*([a-f0-9-]+)\)$/);
    if (match) {
      const [, name, id] = match;
      return {
        id: id.trim(),
        name: name.trim(),
        displayText: option,
        type: 'application' // Default type
      };
    }

    // Fallback for assets without ID format
    return {
      id: `asset-${index}`,
      name: option,
      displayText: option,
      type: 'unknown'
    };
  });
};

/**
 * Get asset type icon
 */
const getAssetTypeIcon = (type?: string) => {
  switch (type) {
    case 'application':
      return <Building className="h-4 w-4" />;
    case 'server':
      return <Server className="h-4 w-4" />;
    case 'database':
      return <Database className="h-4 w-4" />;
    default:
      return <Building className="h-4 w-4" />;
  }
};

export const AssetSelectionForm: React.FC<AssetSelectionFormProps> = ({
  formData,
  formValues,
  onFieldChange,
  onSubmit,
  isSubmitting = false,
  className = ''
}) => {
  // All hooks MUST be declared at the top level before any conditional logic
  // State for search and selection
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedAssets, setSelectedAssets] = useState<string[]>(
    Array.isArray(formValues.selected_assets) ? formValues.selected_assets : []
  );

  // Handle asset selection toggle
  const handleAssetToggle = useCallback((assetDisplayText: string) => {
    const newSelection = selectedAssets.includes(assetDisplayText)
      ? selectedAssets.filter(id => id !== assetDisplayText)
      : [...selectedAssets, assetDisplayText];

    setSelectedAssets(newSelection);
    // Update form values with the backend-expected format
    onFieldChange('selected_assets', newSelection);
  }, [selectedAssets, onFieldChange]);

  // Handle form submission
  const handleSubmit = useCallback(() => {
    if (selectedAssets.length === 0) {
      // Validation - at least one asset must be selected
      return;
    }

    const submissionData = {
      selected_assets: selectedAssets
    };

    onSubmit(submissionData);
  }, [selectedAssets, onSubmit]);

  // Find the selected_assets question from the form data
  const assetQuestion = formData.sections
    .flatMap(section => section.fields)
    .find(field => field.id === 'selected_assets');

  if (!assetQuestion || !assetQuestion.options) {
    return (
      <Alert className="m-4">
        <AlertCircle className="h-4 w-4" />
        <AlertDescription>
          Unable to load asset selection options. Please contact support if this issue persists.
        </AlertDescription>
      </Alert>
    );
  }

  // Parse asset options
  const assetOptions = parseAssetOptions(assetQuestion.options.map(opt =>
    typeof opt === 'string' ? opt : opt.label
  ));

  // Filter assets based on search
  const filteredAssets = assetOptions.filter(asset =>
    asset.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    asset.displayText.toLowerCase().includes(searchTerm.toLowerCase())
  );

  // Check if form is valid
  const isValid = selectedAssets.length > 0;
  const minSelections = assetQuestion.validation?.min_selections || 1;
  const maxSelections = assetQuestion.validation?.max_selections || 10;
  const validationError = selectedAssets.length < minSelections
    ? `Please select at least ${minSelections} asset${minSelections > 1 ? 's' : ''}`
    : selectedAssets.length > maxSelections
    ? `Please select no more than ${maxSelections} assets`
    : null;

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Building className="h-5 w-5" />
            {formData.sections[0]?.title || 'Select Assets for Collection'}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-gray-600 mb-4">
            {formData.sections[0]?.description || assetQuestion.helpText ||
            'Please select the assets or applications you want to collect data for. This is required to generate targeted questionnaires based on gaps.'}
          </p>

          {/* Search */}
          <div className="relative mb-4">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
            <Input
              type="text"
              placeholder="Search assets..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10"
            />
          </div>

          {/* Selection Summary */}
          {selectedAssets.length > 0 && (
            <div className="mb-4 p-3 bg-blue-50 rounded-lg border border-blue-200">
              <div className="flex items-center justify-between">
                <span className="font-medium text-blue-900">
                  {selectedAssets.length} asset{selectedAssets.length > 1 ? 's' : ''} selected
                </span>
                <Badge variant="secondary" className="bg-blue-100 text-blue-800">
                  {selectedAssets.length}/{maxSelections}
                </Badge>
              </div>
            </div>
          )}

          {/* Validation Error */}
          {validationError && (
            <Alert className="mb-4">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>{validationError}</AlertDescription>
            </Alert>
          )}
        </CardContent>
      </Card>

      {/* Asset List */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Available Assets ({filteredAssets.length})</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          <ScrollArea className="h-96">
            <div className="p-4 space-y-2">
              {filteredAssets.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  {searchTerm ? 'No assets match your search' : 'No assets available'}
                </div>
              ) : (
                filteredAssets.map((asset) => {
                  const isSelected = selectedAssets.includes(asset.displayText);
                  return (
                    <div
                      key={asset.id}
                      className={`flex items-center gap-3 p-3 border rounded-lg cursor-pointer transition-colors ${
                        isSelected
                          ? 'border-blue-500 bg-blue-50 hover:bg-blue-100'
                          : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                      }`}
                      onClick={() => handleAssetToggle(asset.displayText)}
                    >
                      {/* Checkbox */}
                      <div className="flex-shrink-0">
                        {isSelected ? (
                          <CheckSquare className="h-5 w-5 text-blue-600" />
                        ) : (
                          <Square className="h-5 w-5 text-gray-400" />
                        )}
                      </div>

                      {/* Asset Icon */}
                      <div className="flex-shrink-0 text-gray-500">
                        {getAssetTypeIcon(asset.type)}
                      </div>

                      {/* Asset Info */}
                      <div className="flex-1 min-w-0">
                        <div className="font-medium text-gray-900 truncate">
                          {asset.name}
                        </div>
                        <div className="text-sm text-gray-500 truncate">
                          ID: {asset.id}
                        </div>
                      </div>

                      {/* Selection Indicator */}
                      {isSelected && (
                        <Badge className="bg-blue-600">Selected</Badge>
                      )}
                    </div>
                  );
                })
              )}
            </div>
          </ScrollArea>
        </CardContent>
      </Card>

      {/* Action Buttons */}
      <Card>
        <CardFooter className="flex justify-between items-center">
          <div className="text-sm text-gray-600">
            {assetQuestion.helpText || 'Select assets to generate tailored questionnaires'}
          </div>
          <Button
            onClick={handleSubmit}
            disabled={!isValid || isSubmitting}
            className="flex items-center gap-2"
          >
            {isSubmitting ? 'Processing...' : 'Generate Questionnaires'}
            {!isSubmitting && <ArrowRight className="h-4 w-4" />}
          </Button>
        </CardFooter>
      </Card>
    </div>
  );
};

export default AssetSelectionForm;
