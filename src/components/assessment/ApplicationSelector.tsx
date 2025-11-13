/**
 * Assessment Flow Application Selector
 *
 * Replaces deprecated 6R Analysis ApplicationSelector (Issue #860).
 * Simple, functional component for selecting applications to include in planning.
 */

import React from 'react';
import { CheckSquare, Square, Check, AlertCircle } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import type { Application } from '@/types/assessment';

interface ApplicationSelectorProps {
  applications: Application[];
  selectedApplicationIds: string[];
  onSelectionChange: (selectedIds: string[]) => void;
  isLoading?: boolean;
}

export const ApplicationSelector: React.FC<ApplicationSelectorProps> = ({
  applications,
  selectedApplicationIds,
  onSelectionChange,
  isLoading = false,
}) => {
  const handleToggleApplication = (appId: string) => {
    if (selectedApplicationIds.includes(appId)) {
      onSelectionChange(selectedApplicationIds.filter(id => id !== appId));
    } else {
      onSelectionChange([...selectedApplicationIds, appId]);
    }
  };

  const handleSelectAll = () => {
    onSelectionChange(applications.map(app => String(app.id)));
  };

  const handleDeselectAll = () => {
    onSelectionChange([]);
  };

  const selectedCount = selectedApplicationIds.length;
  const totalCount = applications.length;

  if (isLoading) {
    return (
      <Card>
        <CardContent className="p-6">
          <div className="flex items-center justify-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            <span className="ml-3 text-sm text-gray-600">Loading applications...</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (applications.length === 0) {
    return (
      <Card>
        <CardContent className="p-6">
          <div className="flex items-center justify-center py-8 text-gray-500">
            <AlertCircle className="h-5 w-5 mr-2" />
            <span className="text-sm">No applications available for selection</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>Select Applications</CardTitle>
            <CardDescription>
              Choose applications to include in your migration planning
            </CardDescription>
          </div>
          <div className="flex items-center gap-2">
            <Badge variant="secondary" className="text-sm">
              {selectedCount} of {totalCount} selected
            </Badge>
          </div>
        </div>
        <div className="flex items-center gap-2 mt-4">
          <Button
            variant="outline"
            size="sm"
            onClick={handleSelectAll}
            disabled={selectedCount === totalCount}
          >
            <CheckSquare className="h-4 w-4 mr-2" />
            Select All
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={handleDeselectAll}
            disabled={selectedCount === 0}
          >
            <Square className="h-4 w-4 mr-2" />
            Deselect All
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        <div className="border rounded-lg overflow-hidden">
          <table className="w-full">
            <thead className="bg-gray-50 border-b">
              <tr>
                <th className="w-12 px-4 py-3 text-left">
                  <span className="sr-only">Select</span>
                </th>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">
                  Application Name
                </th>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">
                  Type
                </th>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">
                  Environment
                </th>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">
                  Status
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {applications.map((app) => {
                const appId = String(app.id);
                const isSelected = selectedApplicationIds.includes(appId);

                return (
                  <tr
                    key={appId}
                    className={`hover:bg-gray-50 cursor-pointer transition-colors ${
                      isSelected ? 'bg-blue-50' : ''
                    }`}
                    onClick={() => handleToggleApplication(appId)}
                  >
                    <td className="px-4 py-3">
                      <div className="flex items-center justify-center">
                        {isSelected ? (
                          <div className="w-5 h-5 bg-blue-600 rounded flex items-center justify-center">
                            <Check className="h-4 w-4 text-white" />
                          </div>
                        ) : (
                          <div className="w-5 h-5 border-2 border-gray-300 rounded hover:border-blue-400"></div>
                        )}
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <div className="text-sm font-medium text-gray-900">
                        {app.name || 'Unnamed Application'}
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <Badge variant="outline" className="text-xs">
                        {app.type || 'Unknown'}
                      </Badge>
                    </td>
                    <td className="px-4 py-3">
                      <span className="text-sm text-gray-600">
                        {app.environment || 'N/A'}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <Badge
                        variant={app.status === 'Ready' ? 'default' : 'secondary'}
                        className="text-xs"
                      >
                        {app.status || 'Unknown'}
                      </Badge>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  );
};
