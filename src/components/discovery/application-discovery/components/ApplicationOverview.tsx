import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { AlertCircle, CheckCircle } from 'lucide-react'
import { Users, RefreshCw, HelpCircle } from 'lucide-react'

interface DiscoveryMetadata {
  total_assets_analyzed: number;
  applications_discovered: number;
  high_confidence_apps: number;
  needs_clarification: number;
  analysis_timestamp: string;
}

interface ApplicationOverviewProps {
  discoveryMetadata: DiscoveryMetadata;
  discoveryConfidence: number;
  clarificationCount: number;
  onRefresh: () => void;
}

export const ApplicationOverview: React.FC<ApplicationOverviewProps> = ({
  discoveryMetadata,
  discoveryConfidence,
  clarificationCount,
  onRefresh
}) => {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <span className="flex items-center gap-2">
            <Users className="h-5 w-5" />
            Application Portfolio Discovery
          </span>
          <Button onClick={onRefresh} variant="outline" size="sm">
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </Button>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <div className="text-center">
            <div className="text-2xl font-bold text-blue-600">
              {discoveryMetadata.applications_discovered}
            </div>
            <div className="text-sm text-gray-600">Applications Found</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-green-600">
              {discoveryMetadata.high_confidence_apps}
            </div>
            <div className="text-sm text-gray-600">High Confidence</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-yellow-600">
              {discoveryMetadata.needs_clarification}
            </div>
            <div className="text-sm text-gray-600">Need Clarification</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-purple-600">
              {discoveryMetadata.total_assets_analyzed}
            </div>
            <div className="text-sm text-gray-600">Assets Analyzed</div>
          </div>
        </div>

        <div className="space-y-3">
          <div>
            <div className="flex justify-between text-sm mb-1">
              <span>Overall Discovery Confidence</span>
              <span className="font-medium">{Math.round(discoveryConfidence * 100)}%</span>
            </div>
            <Progress value={discoveryConfidence * 100} className="h-2" />
          </div>

          {clarificationCount > 0 && (
            <div className="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
              <div className="flex items-center gap-2 text-yellow-800">
                <HelpCircle className="h-5 w-5" />
                <span className="font-medium">
                  {clarificationCount} applications need clarification
                </span>
              </div>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
};
