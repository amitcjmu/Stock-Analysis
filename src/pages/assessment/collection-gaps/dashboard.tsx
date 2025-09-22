import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { CompletenessDashboard } from '@/components/collection/components/CompletenessDashboard';
import { MaintenanceWindowTable } from '@/components/collection/components/MaintenanceWindowTable';
import { ConflictsOverview } from '@/components/collection/ConflictsOverview';

/**
 * Collection Gaps Dashboard
 *
 * This dashboard provides a comprehensive overview of collection gaps
 * by mounting existing components and new asset-agnostic collection features.
 */
export const CollectionGapsDashboard: React.FC = () => {
  return (
    <div className="container mx-auto py-6 space-y-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900">Collection Gaps Dashboard</h1>
        <p className="text-gray-600 mt-2">
          Monitor and manage data collection completeness, maintenance windows, and resolve conflicts across assets
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
        {/* Completeness Metrics - Reusing existing component */}
        <Card className="lg:col-span-1">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              📊 Collection Completeness
            </CardTitle>
          </CardHeader>
          <CardContent>
            <CompletenessDashboard />
          </CardContent>
        </Card>

        {/* Data Conflicts Overview - New asset-agnostic component */}
        <Card className="lg:col-span-1">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              ⚠️ Data Conflicts
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ConflictsOverview />
          </CardContent>
        </Card>

        {/* Maintenance Windows - Existing component in a card wrapper */}
        <Card className="lg:col-span-1 xl:col-span-1">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              🔧 Maintenance Windows
            </CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            {/* MaintenanceWindowTable handles its own padding */}
            <MaintenanceWindowTable />
          </CardContent>
        </Card>
      </div>

      {/* Additional insights row */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Recent Activity</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center gap-3 p-3 bg-blue-50 rounded-lg">
                <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                <div>
                  <p className="text-sm font-medium">Conflict resolution in progress</p>
                  <p className="text-xs text-gray-600">3 fields pending resolution</p>
                </div>
              </div>
              <div className="flex items-center gap-3 p-3 bg-green-50 rounded-lg">
                <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                <div>
                  <p className="text-sm font-medium">Maintenance window scheduled</p>
                  <p className="text-xs text-gray-600">Database cluster update - tonight 2AM</p>
                </div>
              </div>
              <div className="flex items-center gap-3 p-3 bg-yellow-50 rounded-lg">
                <div className="w-2 h-2 bg-yellow-500 rounded-full"></div>
                <div>
                  <p className="text-sm font-medium">Collection quality check</p>
                  <p className="text-xs text-gray-600">87% completeness across all assets</p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Quick Actions</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <button className="w-full text-left p-3 border rounded-lg hover:bg-gray-50 transition-colors">
                <div className="font-medium text-sm">Start Asset Collection</div>
                <div className="text-xs text-gray-600">Begin collecting data for new assets</div>
              </button>
              <button className="w-full text-left p-3 border rounded-lg hover:bg-gray-50 transition-colors">
                <div className="font-medium text-sm">Review Conflicts</div>
                <div className="text-xs text-gray-600">Resolve pending data conflicts</div>
              </button>
              <button className="w-full text-left p-3 border rounded-lg hover:bg-gray-50 transition-colors">
                <div className="font-medium text-sm">Schedule Maintenance</div>
                <div className="text-xs text-gray-600">Plan maintenance windows</div>
              </button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default CollectionGapsDashboard;
