/**
 * Data Integration View Component
 *
 * Displays integrated data from multiple sources with conflict resolution
 * Agent Team B3 - Task B3.6 Frontend Implementation
 */

import React from 'react'
import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Database,
  GitMerge,
  AlertTriangle,
  CheckCircle,
  TrendingUp,
  Download,
  RefreshCw
} from 'lucide-react';
import { cn } from '@/lib/utils';

import { ConflictResolver } from './components/ConflictResolver';
import type { DataConflict, ConflictResolution } from './types';

interface DataRecord {
  id?: string;
  [key: string]: unknown;
}

interface DataIntegrationViewProps {
  applicationId: string;
  integratedData: Record<string, unknown>;
  conflicts: DataConflict[];
  dataSources: Record<string, DataRecord[]>;
  qualityScore: number;
  confidenceScore: number;
  completenessScore: number;
  onResolveConflict: (conflictId: string, resolution: ConflictResolution) => void;
  onRefreshIntegration: () => void;
  onExport: (format: 'json' | 'csv') => void;
  className?: string;
}

export const DataIntegrationView: React.FC<DataIntegrationViewProps> = ({
  applicationId,
  integratedData,
  conflicts,
  dataSources,
  qualityScore,
  confidenceScore,
  completenessScore,
  onResolveConflict,
  onRefreshIntegration,
  onExport,
  className
}) => {
  const [activeTab, setActiveTab] = useState('overview');

  const unresolvedConflicts = conflicts.filter(c => !c.id);
  const sourceCount = Object.keys(dataSources).length;
  const attributeCount = Object.keys(integratedData).length;

  const getQualityBadge = (score: number): JSX.Element => {
    if (score >= 0.9) return <Badge className="bg-green-100 text-green-800">Excellent</Badge>;
    if (score >= 0.7) return <Badge className="bg-blue-100 text-blue-800">Good</Badge>;
    if (score >= 0.5) return <Badge className="bg-amber-100 text-amber-800">Fair</Badge>;
    return <Badge variant="destructive">Poor</Badge>;
  };

  return (
    <div className={cn('space-y-6', className)}>
      {/* Header */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <Database className="h-5 w-5" />
                Integrated Application Data
              </CardTitle>
              <CardDescription>
                Data from {sourceCount} sources integrated for application {applicationId}
              </CardDescription>
            </div>

            <div className="flex items-center gap-2">
              <Button variant="outline" size="sm" onClick={onRefreshIntegration}>
                <RefreshCw className="h-4 w-4 mr-2" />
                Refresh
              </Button>

              <Button variant="outline" size="sm" onClick={() => onExport('json')}>
                <Download className="h-4 w-4 mr-2" />
                Export
              </Button>
            </div>
          </div>

          {/* Summary Metrics */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-4">
            <div className="text-center p-3 bg-muted rounded-lg">
              <div className="text-2xl font-bold text-primary">{attributeCount}</div>
              <div className="text-sm text-muted-foreground">Attributes</div>
            </div>

            <div className="text-center p-3 bg-muted rounded-lg">
              <div className="text-2xl font-bold">{Math.round(completenessScore)}%</div>
              <div className="text-sm text-muted-foreground">Complete</div>
            </div>

            <div className="text-center p-3 bg-muted rounded-lg">
              <div className="text-2xl font-bold">{Math.round(confidenceScore * 100)}%</div>
              <div className="text-sm text-muted-foreground">Confidence</div>
            </div>

            <div className="text-center p-3 bg-muted rounded-lg">
              <div className="flex items-center justify-center">
                {getQualityBadge(qualityScore)}
              </div>
              <div className="text-sm text-muted-foreground">Quality</div>
            </div>
          </div>
        </CardHeader>
      </Card>

      {/* Conflicts Alert */}
      {unresolvedConflicts.length > 0 && (
        <Alert variant="destructive">
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>
            {unresolvedConflicts.length} data conflicts require your attention before proceeding with 6R analysis.
          </AlertDescription>
        </Alert>
      )}

      {/* Content Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="conflicts" className="relative">
            Conflicts
            {unresolvedConflicts.length > 0 && (
              <Badge variant="destructive" className="ml-2 h-5 w-5 p-0 text-xs">
                {unresolvedConflicts.length}
              </Badge>
            )}
          </TabsTrigger>
          <TabsTrigger value="sources">Sources</TabsTrigger>
          <TabsTrigger value="data">Raw Data</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Integration Status */}
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Integration Status</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm">Data Quality</span>
                  <div className="flex items-center gap-2">
                    <div className="w-20 h-2 bg-gray-200 rounded-full">
                      <div
                        className="h-full bg-blue-500 rounded-full"
                        style={{ width: `${qualityScore * 100}%` }}
                      />
                    </div>
                    <span className="text-sm font-medium">{Math.round(qualityScore * 100)}%</span>
                  </div>
                </div>

                <div className="flex items-center justify-between">
                  <span className="text-sm">Completeness</span>
                  <div className="flex items-center gap-2">
                    <div className="w-20 h-2 bg-gray-200 rounded-full">
                      <div
                        className="h-full bg-green-500 rounded-full"
                        style={{ width: `${completenessScore}%` }}
                      />
                    </div>
                    <span className="text-sm font-medium">{Math.round(completenessScore)}%</span>
                  </div>
                </div>

                <div className="flex items-center justify-between">
                  <span className="text-sm">6R Readiness</span>
                  {confidenceScore >= 0.7 ? (
                    <Badge className="bg-green-100 text-green-800">
                      <CheckCircle className="h-3 w-3 mr-1" />
                      Ready
                    </Badge>
                  ) : (
                    <Badge variant="secondary">
                      Needs more data
                    </Badge>
                  )}
                </div>
              </CardContent>
            </Card>

            {/* Data Sources */}
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Data Sources</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                {Object.entries(dataSources).map(([source, data]) => (
                  <div key={source} className="flex items-center justify-between">
                    <span className="text-sm capitalize">{source.replace('_', ' ')}</span>
                    <Badge variant="outline">{Array.isArray(data) ? data.length : 1} records</Badge>
                  </div>
                ))}
              </CardContent>
            </Card>
          </div>

          {/* Recommendations */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base flex items-center gap-2">
                <TrendingUp className="h-4 w-4" />
                Recommendations
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2 text-sm">
                {confidenceScore < 0.7 && (
                  <div className="flex items-start gap-2 p-2 bg-amber-50 rounded">
                    <AlertTriangle className="h-4 w-4 text-amber-600 mt-0.5" />
                    <div>
                      <p className="font-medium text-amber-800">Improve confidence score</p>
                      <p className="text-amber-700">Consider collecting additional manual data for critical attributes</p>
                    </div>
                  </div>
                )}

                {unresolvedConflicts.length > 0 && (
                  <div className="flex items-start gap-2 p-2 bg-red-50 rounded">
                    <AlertTriangle className="h-4 w-4 text-red-600 mt-0.5" />
                    <div>
                      <p className="font-medium text-red-800">Resolve data conflicts</p>
                      <p className="text-red-700">Review and resolve {unresolvedConflicts.length} conflicting data points</p>
                    </div>
                  </div>
                )}

                {confidenceScore >= 0.7 && unresolvedConflicts.length === 0 && (
                  <div className="flex items-start gap-2 p-2 bg-green-50 rounded">
                    <CheckCircle className="h-4 w-4 text-green-600 mt-0.5" />
                    <div>
                      <p className="font-medium text-green-800">Ready for 6R analysis</p>
                      <p className="text-green-700">Data quality is sufficient to proceed with migration strategy analysis</p>
                    </div>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="conflicts">
          <ConflictResolver
            conflicts={conflicts}
            onResolve={onResolveConflict}
          />
        </TabsContent>

        <TabsContent value="sources" className="space-y-4">
          {Object.entries(dataSources).map(([source, data]) => (
            <Card key={source}>
              <CardHeader>
                <CardTitle className="text-base capitalize flex items-center gap-2">
                  <GitMerge className="h-4 w-4" />
                  {source.replace('_', ' ')} Source
                </CardTitle>
                <CardDescription>
                  {Array.isArray(data) ? data.length : 1} records from {source}
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="text-sm text-muted-foreground">
                  <pre className="bg-muted p-2 rounded text-xs overflow-auto max-h-40">
                    {JSON.stringify(data, null, 2)}
                  </pre>
                </div>
              </CardContent>
            </Card>
          ))}
        </TabsContent>

        <TabsContent value="data">
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Integrated Dataset</CardTitle>
              <CardDescription>
                Final integrated data after conflict resolution
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-sm">
                <pre className="bg-muted p-4 rounded text-xs overflow-auto max-h-96">
                  {JSON.stringify(integratedData, null, 2)}
                </pre>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};
