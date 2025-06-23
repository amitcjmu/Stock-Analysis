/**
 * Discovery Flow V2 Dashboard
 * Comprehensive dashboard for managing Discovery Flow V2 with real-time progress tracking
 */

import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { Progress } from '../ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';
import { Alert, AlertDescription } from '../ui/alert';
import { Separator } from '../ui/separator';
import { 
  CheckCircle, 
  AlertCircle, 
  Clock, 
  Database,
  FileText,
  ArrowRight,
  RefreshCw,
  Download,
  Upload
} from 'lucide-react';
import { useDiscoveryFlowV2 } from '../../hooks/discovery/useDiscoveryFlowV2';
import { DiscoveryFlowV2Utils } from '../../services/discoveryFlowV2Service';
import { toast } from 'sonner';

interface DiscoveryFlowV2DashboardProps {
  flowId?: string;
  enableRealTimeUpdates?: boolean;
  onFlowComplete?: (flowId: string) => void;
}

export function DiscoveryFlowV2Dashboard({
  flowId,
  enableRealTimeUpdates = true,
  onFlowComplete
}: DiscoveryFlowV2DashboardProps) {
  const [selectedAssetIds, setSelectedAssetIds] = useState<string[]>([]);
  const [validationData, setValidationData] = useState<any>(null);

  const {
    flow,
    assets,
    isLoading,
    isUpdating,
    isCompleting,
    error,
    updatePhase,
    completeFlow,
    createAssetsFromDiscovery,
    validateCompletion,
    generateAssessmentPackage,
    completeWithAssessment,
    progressPercentage,
    currentPhase,
    completedPhases,
    nextPhase,
    refresh
  } = useDiscoveryFlowV2(flowId, {
    enableRealTimeUpdates,
    autoRefresh: true,
    pollInterval: 5000
  });

  // Handle validation check
  const handleValidateCompletion = async () => {
    try {
      const validation = await validateCompletion();
      setValidationData(validation);
    } catch (error) {
      toast.error('Failed to validate flow completion');
    }
  };

  // Handle flow completion
  const handleCompleteFlow = async () => {
    try {
      await completeFlow();
      toast.success('Discovery flow completed successfully');
      onFlowComplete?.(flowId!);
    } catch (error) {
      toast.error('Failed to complete flow');
    }
  };

  // Handle assessment package generation
  const handleGenerateAssessment = async () => {
    try {
      const assessmentPackage = await generateAssessmentPackage(selectedAssetIds);
      toast.success('Assessment package generated successfully');
      console.log('Assessment package:', assessmentPackage);
    } catch (error) {
      toast.error('Failed to generate assessment package');
    }
  };

  // Handle complete with assessment
  const handleCompleteWithAssessment = async () => {
    try {
      await completeWithAssessment(selectedAssetIds);
      toast.success('Flow completed with assessment package');
      onFlowComplete?.(flowId!);
    } catch (error) {
      toast.error('Failed to complete flow with assessment');
    }
  };

  // Handle phase update
  const handlePhaseUpdate = async (phase: string, data: any) => {
    try {
      await updatePhase(phase, data);
      toast.success(`Phase ${DiscoveryFlowV2Utils.formatPhaseDisplayName(phase)} updated successfully`);
    } catch (error) {
      toast.error(`Failed to update phase ${phase}`);
    }
  };

  // Handle asset creation
  const handleCreateAssets = async () => {
    try {
      await createAssetsFromDiscovery();
      toast.success('Assets created from discovery data');
    } catch (error) {
      toast.error('Failed to create assets');
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center p-8">
        <RefreshCw className="h-8 w-8 animate-spin" />
        <span className="ml-2">Loading discovery flow...</span>
      </div>
    );
  }

  if (error) {
    return (
      <Alert variant="destructive">
        <AlertCircle className="h-4 w-4" />
        <AlertDescription>
          Failed to load discovery flow: {error.message}
        </AlertDescription>
      </Alert>
    );
  }

  if (!flow) {
    return (
      <Card>
        <CardContent className="p-8 text-center">
          <FileText className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
          <h3 className="text-lg font-semibold mb-2">No Discovery Flow Selected</h3>
          <p className="text-muted-foreground">Select a discovery flow to view its dashboard.</p>
        </CardContent>
      </Card>
    );
  }

  const phases = [
    { key: 'data_import', label: 'Data Import', icon: '📥' },
    { key: 'attribute_mapping', label: 'Attribute Mapping', icon: '🗺️' },
    { key: 'data_cleansing', label: 'Data Cleansing', icon: '🧹' },
    { key: 'inventory', label: 'Inventory', icon: '📋' },
    { key: 'dependencies', label: 'Dependencies', icon: '🔗' },
    { key: 'tech_debt', label: 'Tech Debt', icon: '⚠️' }
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">{flow.flow_name}</h1>
          <p className="text-muted-foreground">
            Flow ID: {flow.flow_id} • Status: <Badge variant={
              flow.status === 'completed' ? 'default' : 
              flow.status === 'in_progress' ? 'secondary' : 'outline'
            }>{flow.status}</Badge>
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={refresh} disabled={isLoading}>
            <RefreshCw className={`h-4 w-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
          <Button variant="outline" onClick={handleValidateCompletion}>
            <CheckCircle className="h-4 w-4 mr-2" />
            Validate
          </Button>
        </div>
      </div>

      {/* Progress Overview */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Clock className="h-5 w-5" />
            Progress Overview
          </CardTitle>
          <CardDescription>
            Current progress: {progressPercentage}% complete
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <Progress value={progressPercentage} className="w-full" />
          
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
            {phases.map((phase) => {
              const isCompleted = completedPhases.includes(phase.key);
              const isCurrent = currentPhase === phase.key;
              
              return (
                <div
                  key={phase.key}
                  className={`p-3 rounded-lg border text-center transition-colors ${
                    isCompleted 
                      ? 'bg-green-50 border-green-200' 
                      : isCurrent 
                        ? 'bg-blue-50 border-blue-200' 
                        : 'bg-gray-50 border-gray-200'
                  }`}
                >
                  <div className="text-2xl mb-1">{phase.icon}</div>
                  <div className="text-sm font-medium">{phase.label}</div>
                  <div className="mt-1">
                    {isCompleted && <CheckCircle className="h-4 w-4 mx-auto text-green-600" />}
                    {isCurrent && <Clock className="h-4 w-4 mx-auto text-blue-600" />}
                  </div>
                </div>
              );
            })}
          </div>

          {nextPhase && (
            <Alert>
              <ArrowRight className="h-4 w-4" />
              <AlertDescription>
                Next phase: <strong>{DiscoveryFlowV2Utils.formatPhaseDisplayName(nextPhase)}</strong>
              </AlertDescription>
            </Alert>
          )}
        </CardContent>
      </Card>

      {/* Main Content Tabs */}
      <Tabs defaultValue="assets" className="space-y-4">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="assets">Assets ({assets.length})</TabsTrigger>
          <TabsTrigger value="phases">Phases</TabsTrigger>
          <TabsTrigger value="validation">Validation</TabsTrigger>
          <TabsTrigger value="assessment">Assessment</TabsTrigger>
        </TabsList>

        {/* Assets Tab */}
        <TabsContent value="assets" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Database className="h-5 w-5" />
                Discovery Assets
              </CardTitle>
              <CardDescription>
                Assets discovered during the flow execution
              </CardDescription>
            </CardHeader>
            <CardContent>
              {assets.length === 0 ? (
                <div className="text-center py-8">
                  <Database className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
                  <p className="text-muted-foreground">No assets discovered yet</p>
                  <Button 
                    className="mt-4" 
                    onClick={handleCreateAssets}
                    disabled={isUpdating}
                  >
                    <Upload className="h-4 w-4 mr-2" />
                    Create Assets from Discovery
                  </Button>
                </div>
              ) : (
                <div className="space-y-4">
                  {/* Asset Summary */}
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="p-3 bg-blue-50 rounded-lg">
                      <div className="text-2xl font-bold text-blue-600">{assets.length}</div>
                      <div className="text-sm text-blue-800">Total Assets</div>
                    </div>
                    <div className="p-3 bg-green-50 rounded-lg">
                      <div className="text-2xl font-bold text-green-600">
                        {assets.filter(a => a.migration_ready).length}
                      </div>
                      <div className="text-sm text-green-800">Migration Ready</div>
                    </div>
                    <div className="p-3 bg-yellow-50 rounded-lg">
                      <div className="text-2xl font-bold text-yellow-600">
                        {assets.filter(a => a.validation_status === 'pending').length}
                      </div>
                      <div className="text-sm text-yellow-800">Pending Validation</div>
                    </div>
                    <div className="p-3 bg-purple-50 rounded-lg">
                      <div className="text-2xl font-bold text-purple-600">
                        {new Set(assets.map(a => a.asset_type)).size}
                      </div>
                      <div className="text-sm text-purple-800">Asset Types</div>
                    </div>
                  </div>

                  <Separator />

                  {/* Asset List */}
                  <div className="space-y-2 max-h-96 overflow-y-auto">
                    {assets.map((asset) => (
                      <div
                        key={asset.id}
                        className="flex items-center justify-between p-3 border rounded-lg hover:bg-gray-50"
                      >
                        <div className="flex items-center gap-3">
                          <input
                            type="checkbox"
                            checked={selectedAssetIds.includes(asset.id)}
                            onChange={(e) => {
                              if (e.target.checked) {
                                setSelectedAssetIds([...selectedAssetIds, asset.id]);
                              } else {
                                setSelectedAssetIds(selectedAssetIds.filter(id => id !== asset.id));
                              }
                            }}
                            className="rounded"
                          />
                          <div>
                            <div className="font-medium">{asset.asset_name}</div>
                            <div className="text-sm text-muted-foreground">
                              {asset.asset_type} • {asset.discovered_in_phase}
                            </div>
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          <Badge variant={asset.migration_ready ? 'default' : 'secondary'}>
                            {asset.migration_ready ? 'Ready' : 'Not Ready'}
                          </Badge>
                          <Badge variant="outline">
                            {DiscoveryFlowV2Utils.formatMigrationComplexity(asset.migration_complexity)}
                          </Badge>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Phases Tab */}
        <TabsContent value="phases" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Phase Management</CardTitle>
              <CardDescription>
                Manage and monitor individual discovery phases
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {phases.map((phase) => {
                const isCompleted = completedPhases.includes(phase.key);
                const isCurrent = currentPhase === phase.key;
                
                return (
                  <div key={phase.key} className="flex items-center justify-between p-4 border rounded-lg">
                    <div className="flex items-center gap-3">
                      <div className="text-2xl">{phase.icon}</div>
                      <div>
                        <div className="font-medium">{phase.label}</div>
                        <div className="text-sm text-muted-foreground">
                          {isCompleted ? 'Completed' : isCurrent ? 'In Progress' : 'Pending'}
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      {isCompleted && <CheckCircle className="h-5 w-5 text-green-600" />}
                      {isCurrent && <Clock className="h-5 w-5 text-blue-600" />}
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handlePhaseUpdate(phase.key, {})}
                        disabled={isUpdating || isCompleted}
                      >
                        {isCurrent ? 'Complete' : 'Start'}
                      </Button>
                    </div>
                  </div>
                );
              })}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Validation Tab */}
        <TabsContent value="validation" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Flow Validation</CardTitle>
              <CardDescription>
                Validate flow completion and readiness for assessment
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <Button onClick={handleValidateCompletion} disabled={isLoading}>
                <CheckCircle className="h-4 w-4 mr-2" />
                Run Validation
              </Button>

              {validationData && (
                <div className="space-y-4">
                  <Alert variant={validationData.is_ready ? 'default' : 'destructive'}>
                    <AlertCircle className="h-4 w-4" />
                    <AlertDescription>
                      Flow is {validationData.is_ready ? 'ready' : 'not ready'} for completion
                      (Readiness Score: {validationData.readiness_score}%)
                    </AlertDescription>
                  </Alert>

                  {validationData.warnings?.length > 0 && (
                    <div className="space-y-2">
                      <h4 className="font-medium text-yellow-800">Warnings:</h4>
                      {validationData.warnings.map((warning: string, index: number) => (
                        <div key={index} className="text-sm text-yellow-700 bg-yellow-50 p-2 rounded">
                          {warning}
                        </div>
                      ))}
                    </div>
                  )}

                  {validationData.errors?.length > 0 && (
                    <div className="space-y-2">
                      <h4 className="font-medium text-red-800">Errors:</h4>
                      {validationData.errors.map((error: string, index: number) => (
                        <div key={index} className="text-sm text-red-700 bg-red-50 p-2 rounded">
                          {error}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Assessment Tab */}
        <TabsContent value="assessment" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Assessment Handoff</CardTitle>
              <CardDescription>
                Generate assessment packages and complete the discovery flow
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <span>Selected assets: {selectedAssetIds.length}</span>
                <Button
                  variant="link"
                  size="sm"
                  onClick={() => setSelectedAssetIds(assets.map(a => a.id))}
                >
                  Select All
                </Button>
                <Button
                  variant="link"
                  size="sm"
                  onClick={() => setSelectedAssetIds([])}
                >
                  Clear Selection
                </Button>
              </div>

              <div className="flex gap-2">
                <Button
                  onClick={handleGenerateAssessment}
                  disabled={isCompleting || selectedAssetIds.length === 0}
                >
                  <Download className="h-4 w-4 mr-2" />
                  Generate Assessment Package
                </Button>
                <Button
                  onClick={handleCompleteWithAssessment}
                  disabled={isCompleting || selectedAssetIds.length === 0}
                  variant="default"
                >
                  <CheckCircle className="h-4 w-4 mr-2" />
                  Complete with Assessment
                </Button>
              </div>

              <Alert>
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>
                  Completing with assessment will generate migration waves, risk assessments, 
                  and 6R strategy recommendations for the selected assets.
                </AlertDescription>
              </Alert>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Flow Actions */}
      {!flow.is_complete && (
        <Card>
          <CardHeader>
            <CardTitle>Flow Actions</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex gap-2">
              <Button
                onClick={handleCompleteFlow}
                disabled={isCompleting}
                variant="default"
              >
                {isCompleting ? (
                  <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                ) : (
                  <CheckCircle className="h-4 w-4 mr-2" />
                )}
                Complete Flow
              </Button>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
} 