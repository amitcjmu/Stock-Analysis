/**
 * Dependency Selector Component (Issue #910)
 *
 * Searchable dropdown for selecting a parent application asset and dependency type
 * when resolving conflicts with "Create Both with Shared Dependency" action.
 *
 * Features:
 * - Typeahead search for parent applications
 * - Radio group for dependency type selection (hosting, infrastructure, server)
 * - Real-time validation feedback
 * - Integration with Asset Conflict Resolution flow
 *
 * CC: All field names use snake_case to match backend API
 */

import React, { useState, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Label } from '@/components/ui/label';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { Input } from '@/components/ui/input';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Loader2, Search } from 'lucide-react';
import { apiCall } from '@/config/api';
import type { DependencySelection } from '@/types/assetConflict';

interface DependencySelectorProps {
  client_account_id: string;
  engagement_id: string;
  onSelectionChange: (selection: DependencySelection | null) => void;
  className?: string;
}

interface ApplicationAsset {
  id: string;
  name: string;
  application_name?: string;
  description?: string;
}

/**
 * Fetch available application assets for parent selection
 */
const fetchAvailableApplications = async (
  client_account_id: string,
  engagement_id: string
): Promise<ApplicationAsset[]> => {
  return apiCall(
    `/api/v1/dependency-analysis/available-applications?client_account_id=${client_account_id}&engagement_id=${engagement_id}`,
    { method: 'GET' }
  );
};

export const DependencySelector: React.FC<DependencySelectorProps> = ({
  client_account_id,
  engagement_id,
  onSelectionChange,
  className,
}) => {
  const [selectedParentId, setSelectedParentId] = useState<string | null>(null);
  const [dependencyType, setDependencyType] = useState<
    'hosting' | 'infrastructure' | 'server'
  >('hosting');
  const [searchQuery, setSearchQuery] = useState('');

  // Fetch available applications
  const {
    data: applications,
    isLoading,
    error,
  } = useQuery<ApplicationAsset[]>({
    queryKey: ['availableApplications', client_account_id, engagement_id],
    queryFn: () => fetchAvailableApplications(client_account_id, engagement_id),
    enabled: !!client_account_id && !!engagement_id,
  });

  // Filter applications by search query
  const filteredApplications = useMemo(() => {
    if (!applications) return [];
    if (!searchQuery) return applications;

    const query = searchQuery.toLowerCase();
    return applications.filter(
      (app) =>
        app.name.toLowerCase().includes(query) ||
        app.application_name?.toLowerCase().includes(query) ||
        app.description?.toLowerCase().includes(query)
    );
  }, [applications, searchQuery]);

  // Find selected application
  const selectedApplication = useMemo(() => {
    return applications?.find((app) => app.id === selectedParentId);
  }, [applications, selectedParentId]);

  // Handler: Parent application selection
  const handleParentChange = (parentId: string) => {
    setSelectedParentId(parentId);
    const parent = applications?.find((app) => app.id === parentId);

    if (parent) {
      onSelectionChange({
        parent_asset_id: parent.id,
        parent_asset_name: parent.application_name || parent.name,
        dependency_type: dependencyType,
        confidence_score: 1.0, // Manual selection = full confidence
      });
    } else {
      onSelectionChange(null);
    }
  };

  // Handler: Dependency type selection
  const handleDependencyTypeChange = (
    type: 'hosting' | 'infrastructure' | 'server'
  ) => {
    setDependencyType(type);

    if (selectedApplication) {
      onSelectionChange({
        parent_asset_id: selectedApplication.id,
        parent_asset_name:
          selectedApplication.application_name || selectedApplication.name,
        dependency_type: type,
        confidence_score: 1.0,
      });
    }
  };

  // Loading state
  if (isLoading) {
    return (
      <div className={`space-y-4 ${className}`}>
        <div className="flex items-center justify-center py-8">
          <Loader2 className="h-6 w-6 animate-spin text-primary" />
          <span className="ml-2 text-sm">Loading applications...</span>
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className={className}>
        <Alert variant="destructive">
          <AlertDescription>
            {error instanceof Error
              ? error.message
              : 'Failed to load available applications'}
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Parent Application Selection */}
      <div className="space-y-2">
        <Label htmlFor="parent-search">
          Select Parent Application{' '}
          <span className="text-destructive">*</span>
        </Label>
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            id="parent-search"
            type="text"
            placeholder="Search applications..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-9"
          />
        </div>

        <Select value={selectedParentId || ''} onValueChange={handleParentChange}>
          <SelectTrigger>
            <SelectValue placeholder="Choose a parent application" />
          </SelectTrigger>
          <SelectContent>
            {filteredApplications.length === 0 ? (
              <div className="py-6 text-center text-sm text-muted-foreground">
                No applications found
              </div>
            ) : (
              filteredApplications.map((app) => (
                <SelectItem key={app.id} value={app.id}>
                  <div className="flex flex-col">
                    <span className="font-medium">
                      {app.application_name || app.name}
                    </span>
                    {app.description && (
                      <span className="text-xs text-muted-foreground">
                        {app.description}
                      </span>
                    )}
                  </div>
                </SelectItem>
              ))
            )}
          </SelectContent>
        </Select>

        {selectedApplication && (
          <p className="text-sm text-muted-foreground">
            Selected: {selectedApplication.application_name || selectedApplication.name}
          </p>
        )}
      </div>

      {/* Dependency Type Selection */}
      <div className="space-y-2">
        <Label>
          Dependency Type <span className="text-destructive">*</span>
        </Label>
        <RadioGroup
          value={dependencyType}
          onValueChange={(value) =>
            handleDependencyTypeChange(
              value as 'hosting' | 'infrastructure' | 'server'
            )
          }
        >
          <div className="flex items-center space-x-2">
            <RadioGroupItem value="hosting" id="dep-hosting" />
            <Label htmlFor="dep-hosting" className="font-normal cursor-pointer">
              Hosting - Parent hosts both assets
            </Label>
          </div>
          <div className="flex items-center space-x-2">
            <RadioGroupItem value="infrastructure" id="dep-infrastructure" />
            <Label
              htmlFor="dep-infrastructure"
              className="font-normal cursor-pointer"
            >
              Infrastructure - Parent provides infrastructure for both
            </Label>
          </div>
          <div className="flex items-center space-x-2">
            <RadioGroupItem value="server" id="dep-server" />
            <Label htmlFor="dep-server" className="font-normal cursor-pointer">
              Server - Parent is the underlying server
            </Label>
          </div>
        </RadioGroup>
      </div>

      {/* Help text */}
      <Alert>
        <AlertDescription className="text-sm">
          <strong>Note:</strong> Both the existing and new assets will be created
          with a dependency relationship to the selected parent application.
          This resolves the conflict while preserving both assets as distinct entities.
        </AlertDescription>
      </Alert>
    </div>
  );
};
