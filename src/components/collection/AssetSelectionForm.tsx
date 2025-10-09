/**
 * Asset Selection Form Component
 *
 * Handles the bootstrap_asset_selection questionnaire that allows users to select
 * assets for collection flows when no assets are initially selected.
 */

import React, { useState, useCallback } from 'react';
import { CheckSquare, Square, Search, Building, Server, Database, ArrowRight, AlertCircle, RefreshCw } from 'lucide-react';

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
  onRetry?: () => void;
  isSubmitting?: boolean;
  isLoading?: boolean;
  error?: Error | null;
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
  onRetry,
  isSubmitting = false,
  isLoading = false,
  error = null,
  className = ''
}) => {
  // All hooks MUST be declared at the top level before any conditional logic
  // State for search and selection
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedAssets, setSelectedAssets] = useState<string[]>(
    Array.isArray(formValues.selected_assets) ? formValues.selected_assets : []
  );
  const [validationError, setValidationError] = useState<string | null>(null);

  // Handle asset selection toggle - store just the ID, not the display text
  const handleAssetToggle = useCallback((assetId: string) => {
    const newSelection = selectedAssets.includes(assetId)
      ? selectedAssets.filter(id => id !== assetId)
      : [...selectedAssets, assetId];

    setSelectedAssets(newSelection);
    // Update form values with just the IDs for backend
    onFieldChange('selected_assets', newSelection);
    // Clear validation error when assets are selected
    if (newSelection.length > 0) {
      setValidationError(null);
    }
  }, [selectedAssets, onFieldChange]);

  // Handle form submission
  const handleSubmit = useCallback(() => {
    console.log('🔵 AssetSelectionForm.handleSubmit CALLED');
    console.log('🔵 Selected assets:', selectedAssets);
    console.log('🔵 Form values:', formValues);

    if (selectedAssets.length === 0) {
      // Validation - at least one asset must be selected
      console.log('❌ Validation failed: No assets selected');
      setValidationError('Please select at least one asset to continue');
      return;
    }

    // CRITICAL FIX: Merge current selection with existing form values to ensure completeness
    // This prevents the backend from receiving empty selected_assets_response
    const submissionData = {
      ...formValues,
      selected_assets: selectedAssets
    };

    console.log('🔵 Calling onSubmit with data:', submissionData);
    onSubmit(submissionData);
    console.log('🔵 onSubmit called successfully');
  }, [selectedAssets, onSubmit, formValues]);

  // Find the selected_assets question from the form data
  const assetQuestion = formData.sections
    .flatMap(section => section.fields)
    .find(field => field.id === 'selected_assets');

  // Parse asset options - handle both string and object formats
  // IMPORTANT: This useMemo must be declared before any conditional returns
  const assetOptions = React.useMemo(() => {
    if (!assetQuestion?.options) return [];

    return assetQuestion.options.map((opt, index) => {
      if (typeof opt === 'string') {
        // String format: try to parse ID from "Name (ID: uuid)" format
        const match = opt.match(/^(.+?)\s*\(ID:\s*([a-f0-9-]+)\)$/);
        if (match) {
          const [, name, id] = match;
          return {
            id: id.trim(),
            name: name.trim(),
            displayText: opt,
            type: 'application'
          };
        }
        // Fallback for strings without ID format
        return {
          id: `asset-${index}`,
          name: opt,
          displayText: opt,
          type: 'unknown'
        };
      } else {
        // Object format from backend with metadata
        const assetId = opt.metadata?.asset_id || opt.value || `asset-${index}`;
        const name = opt.label?.split(' - ')[0] || opt.label || opt.value || '';
        return {
          id: assetId,
          name: name,
          displayText: opt.label || opt.value || '',
          type: opt.metadata?.type || 'application'
        };
      }
    });
  }, [assetQuestion]);

  // Filter assets based on search
  const filteredAssets = assetOptions.filter(asset =>
    asset.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    asset.displayText.toLowerCase().includes(searchTerm.toLowerCase())
  );

  // Check if form is valid and get validation constraints
  const isValid = selectedAssets.length > 0;
  const minSelections = assetQuestion?.validation?.min_selections || 1;
  const maxSelections = assetQuestion?.validation?.max_selections || 10;

  // Update validation error based on selection count
  React.useEffect(() => {
    if (selectedAssets.length < minSelections && selectedAssets.length > 0) {
      setValidationError(`Please select at least ${minSelections} asset${minSelections > 1 ? 's' : ''}`);
    } else if (selectedAssets.length > maxSelections) {
      setValidationError(`Please select no more than ${maxSelections} assets`);
    } else if (selectedAssets.length === 0) {
      // Don't show error initially when nothing is selected
      setValidationError(null);
    } else {
      setValidationError(null);
    }
  }, [selectedAssets, minSelections, maxSelections]);

  // Early return AFTER all hooks have been declared
  if (!assetQuestion || !assetQuestion.options) {
    return (
      <div className="space-y-4 m-4">
        <Alert variant={error ? "destructive" : "default"}>
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            {error ?
              `Failed to load asset selection options: ${error.message}` :
              'Unable to load asset selection options. This may be because no assets were found or there was a temporary error.'
            }
          </AlertDescription>
        </Alert>

        {onRetry && (
          <div className="flex justify-center">
            <Button
              onClick={onRetry}
              disabled={isLoading}
              variant="outline"
              className="flex items-center gap-2"
            >
              <RefreshCw className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
              {isLoading ? 'Loading...' : 'Retry Loading Assets'}
            </Button>
          </div>
        )}

        <Alert>
          <AlertDescription>
            If this problem persists, please:
            <ul className="list-disc ml-4 mt-2">
              <li>Check that you have applications configured in your account</li>
              <li>Verify your network connection</li>
              <li>Contact support if the issue continues</li>
            </ul>
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  // Show loading state while fetching assets
  if (isLoading) {
    return (
      <div className={`space-y-6 ${className}`}>
        <Card>
          <CardContent className="flex items-center justify-center py-8">
            <div className="flex items-center gap-3">
              <RefreshCw className="h-5 w-5 animate-spin" />
              <span>Loading available assets...</span>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Error Alert */}
      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription className="flex items-center justify-between">
            <span>{error.message}</span>
            {onRetry && (
              <Button
                onClick={onRetry}
                variant="outline"
                size="sm"
                className="ml-4"
              >
                <RefreshCw className="h-3 w-3 mr-1" />
                Retry
              </Button>
            )}
          </AlertDescription>
        </Alert>
      )}

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
                  const isSelected = selectedAssets.includes(asset.id);
                  return (
                    <div
                      key={asset.id}
                      className={`flex items-center gap-3 p-3 border rounded-lg cursor-pointer transition-colors ${
                        isSelected
                          ? 'border-blue-500 bg-blue-50 hover:bg-blue-100'
                          : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                      }`}
                      onClick={() => handleAssetToggle(asset.id)}
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
