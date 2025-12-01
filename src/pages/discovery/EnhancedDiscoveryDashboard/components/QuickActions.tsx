import React from 'react';
import {
  Plus,
  Upload,
  Settings,
  Eye,
  RefreshCw,
  BarChart3,
  Users,
  ArrowRight
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

interface QuickActionsProps {
  onNewFlow: () => void;  // Bug #972: Kept for backward compatibility
  onDataImport: () => void;  // Bug #972: Primary action - merged with "New Flow"
  onViewFlows: () => void;
  onSystemHealth: () => void;
  onRefreshDashboard: () => void;
  isLoading?: boolean;
}

export const QuickActions: React.FC<QuickActionsProps> = ({
  onNewFlow,
  onDataImport,
  onViewFlows,
  onSystemHealth,
  onRefreshDashboard,
  isLoading = false
}) => {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center space-x-2">
          <Settings className="h-5 w-5 text-gray-600" />
          <span>Quick Actions</span>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {/* Bug #972 Fix: Merged "New Discovery Flow" and "Import Data" into single action */}
          {/* Both actions previously navigated to /discovery/cmdb-import */}
          <Button
            onClick={onDataImport}
            className="flex items-center justify-between p-4 h-auto bg-blue-600 hover:bg-blue-700 sm:col-span-2"
          >
            <div className="flex items-center space-x-2">
              <Plus className="h-4 w-4" />
              <span>Start New Discovery</span>
            </div>
            <ArrowRight className="h-4 w-4" />
          </Button>

          {/* Bug #972 Fix: Manage Flows now switches to Flows tab */}
          <Button
            onClick={onViewFlows}
            variant="outline"
            className="flex items-center justify-between p-4 h-auto"
          >
            <div className="flex items-center space-x-2">
              <Eye className="h-4 w-4" />
              <span>Manage Flows</span>
            </div>
            <ArrowRight className="h-4 w-4" />
          </Button>

          {/* Bug #972 Fix: System Health now navigates to /observability */}
          <Button
            onClick={onSystemHealth}
            variant="outline"
            className="flex items-center justify-between p-4 h-auto"
          >
            <div className="flex items-center space-x-2">
              <BarChart3 className="h-4 w-4" />
              <span>System Health</span>
            </div>
            <ArrowRight className="h-4 w-4" />
          </Button>
        </div>

        {/* Additional Actions */}
        <div className="mt-4 pt-4 border-t">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2 text-sm text-gray-600">
              <Users className="h-4 w-4" />
              <span>Agent Management</span>
            </div>

            <Button
              onClick={onRefreshDashboard}
              variant="ghost"
              size="sm"
              disabled={isLoading}
              className="flex items-center space-x-1"
            >
              <RefreshCw className={`h-3 w-3 ${isLoading ? 'animate-spin' : ''}`} />
              <span>Refresh</span>
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};
