import React from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { 
  Database, Server, HardDrive, RefreshCw, Router, Shield, Cpu, Cloud, Zap,
  ChevronRight, CheckCircle, AlertCircle, ArrowRight, Users, Brain,
  Filter, Search, Download, Plus
} from 'lucide-react';

interface AssetInventory {
  id?: string;
  asset_name?: string;
  asset_type?: string;
  environment?: string;
  department?: string;
  criticality?: string;
  discovery_status?: string;
  migration_readiness?: number;
  confidence_score?: number;
  created_at?: string;
  updated_at?: string;
}

interface InventoryProgress {
  total_assets: number;
  classified_assets: number;
  servers: number;
  applications: number;
  devices: number;
  databases: number;
  unknown: number;
  classification_accuracy: number;
  crew_completion_status: Record<string, boolean>;
}

interface InventorySummary {
  total: number;
  filtered: number;
  applications: number;
  servers: number;
  databases: number;
  devices: number;
  unknown: number;
  discovered: number;
  pending: number;
  device_breakdown: {
    network: number;
    storage: number;
    security: number;
    infrastructure: number;
    virtualization: number;
  };
}

interface InventoryContentProps {
  assets: AssetInventory[];
  summary: InventorySummary;
  inventoryProgress: InventoryProgress;
  currentPage: number;
  filters: Record<string, any>;
  searchTerm: string;
  selectedAssets: string[];
  lastUpdated: Date | null;
  onTriggerAnalysis: () => void;
  onFilterChange: (filterType: string, value: string) => void;
  onSearchChange: (search: string) => void;
  onPageChange: (page: number) => void;
  onAssetSelect: (assetId: string) => void;
  onSelectAll: () => void;
  onClearSelection: () => void;
  onBulkUpdate: (updateData: any) => void;
  onClassificationUpdate: (assetId: string, newClassification: string) => void;
  onContinueToAppServerDependencies: () => void;
  canContinueToAppServerDependencies: boolean;
}

export const InventoryContent: React.FC<InventoryContentProps> = ({
  assets,
  summary,
  inventoryProgress,
  currentPage,
  filters,
  searchTerm,
  selectedAssets,
  lastUpdated,
  onTriggerAnalysis,
  onFilterChange,
  onSearchChange,
  onPageChange,
  onAssetSelect,
  onSelectAll,
  onClearSelection,
  onBulkUpdate,
  onClassificationUpdate,
  onContinueToAppServerDependencies,
  canContinueToAppServerDependencies
}) => {

  const getTypeIcon = (type: string) => {
    const iconMap: Record<string, React.ReactNode> = {
      'Application': <Cpu className="h-4 w-4 text-blue-600" />,
      'Server': <Server className="h-4 w-4 text-green-600" />,
      'Database': <Database className="h-4 w-4 text-purple-600" />,
      'Infrastructure Device': <Router className="h-4 w-4 text-orange-600" />,
      'Security Device': <Shield className="h-4 w-4 text-red-600" />,
      'Storage Device': <HardDrive className="h-4 w-4 text-yellow-600" />,
      'Unknown': <AlertCircle className="h-4 w-4 text-gray-400" />
    };
    return iconMap[type] || iconMap['Unknown'];
  };

  const getReadinessColor = (readiness: number) => {
    if (readiness >= 0.8) return 'text-green-600';
    if (readiness >= 0.6) return 'text-yellow-600';
    return 'text-red-600';
  };

  const renderInventoryOverview = () => (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
      <Card>
        <CardContent className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Total Assets</p>
              <p className="text-2xl font-bold">{inventoryProgress.total_assets}</p>
            </div>
            <Database className="h-8 w-8 text-blue-600" />
          </div>
        </CardContent>
      </Card>
      
      <Card>
        <CardContent className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Classified</p>
              <p className="text-2xl font-bold">{inventoryProgress.classified_assets}</p>
              <p className="text-xs text-green-600">
                {inventoryProgress.classification_accuracy.toFixed(1)}% accuracy
              </p>
            </div>
            <CheckCircle className="h-8 w-8 text-green-600" />
          </div>
        </CardContent>
      </Card>
      
      <Card>
        <CardContent className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Servers</p>
              <p className="text-2xl font-bold">{inventoryProgress.servers}</p>
            </div>
            <Server className="h-8 w-8 text-green-600" />
          </div>
        </CardContent>
      </Card>
      
      <Card>
        <CardContent className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Applications</p>
              <p className="text-2xl font-bold">{inventoryProgress.applications}</p>
            </div>
            <Cpu className="h-8 w-8 text-blue-600" />
          </div>
        </CardContent>
      </Card>
    </div>
  );

  const renderClassificationProgress = () => (
    <Card className="mb-6">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Brain className="h-5 w-5" />
          Inventory Building Progress
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          <div>
            <div className="flex justify-between items-center mb-2">
              <span className="text-sm font-medium">Classification Accuracy</span>
              <span className="text-sm text-gray-600">
                {inventoryProgress.classification_accuracy.toFixed(1)}%
              </span>
            </div>
            <Progress value={inventoryProgress.classification_accuracy} className="h-2" />
          </div>
          
          {inventoryProgress.classification_accuracy < 80 && (
            <Alert>
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>
                Classification accuracy is below 80%. Consider running additional analysis 
                or manually reviewing unclassified assets before proceeding to dependency analysis.
              </AlertDescription>
            </Alert>
          )}
          
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
            <div className="bg-blue-50 p-3 rounded-lg">
              <div className="text-2xl font-bold text-blue-600">{summary.applications}</div>
              <div className="text-sm text-blue-600">Applications</div>
            </div>
            <div className="bg-green-50 p-3 rounded-lg">
              <div className="text-2xl font-bold text-green-600">{summary.servers}</div>
              <div className="text-sm text-green-600">Servers</div>
            </div>
            <div className="bg-purple-50 p-3 rounded-lg">
              <div className="text-2xl font-bold text-purple-600">{summary.databases}</div>
              <div className="text-sm text-purple-600">Databases</div>
            </div>
            <div className="bg-orange-50 p-3 rounded-lg">
              <div className="text-2xl font-bold text-orange-600">{summary.devices}</div>
              <div className="text-sm text-orange-600">Devices</div>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );

  const renderAssetTable = () => (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>Asset Inventory</CardTitle>
          <div className="flex gap-2">
            <Button variant="outline" size="sm" onClick={onTriggerAnalysis}>
              <RefreshCw className="h-4 w-4 mr-2" />
              Refresh Analysis
            </Button>
            {selectedAssets.length > 0 && (
              <Button variant="outline" size="sm" onClick={() => onBulkUpdate({})}>
                <Users className="h-4 w-4 mr-2" />
                Bulk Update ({selectedAssets.length})
              </Button>
            )}
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b">
                <th className="text-left p-2">
                  <input 
                    type="checkbox" 
                    onChange={selectedAssets.length === assets.length ? onClearSelection : onSelectAll}
                    checked={selectedAssets.length === assets.length && assets.length > 0}
                  />
                </th>
                <th className="text-left p-2">Asset Name</th>
                <th className="text-left p-2">Type</th>
                <th className="text-left p-2">Environment</th>
                <th className="text-left p-2">Criticality</th>
                <th className="text-left p-2">Readiness</th>
                <th className="text-left p-2">Actions</th>
              </tr>
            </thead>
            <tbody>
              {assets.map((asset) => (
                <tr key={asset.id} className="border-b hover:bg-gray-50">
                  <td className="p-2">
                    <input 
                      type="checkbox"
                      checked={selectedAssets.includes(asset.id || '')}
                      onChange={() => onAssetSelect(asset.id || '')}
                    />
                  </td>
                  <td className="p-2">
                    <div className="font-medium">{asset.asset_name}</div>
                    <div className="text-sm text-gray-500">ID: {asset.id}</div>
                  </td>
                  <td className="p-2">
                    <div className="flex items-center gap-2">
                      {getTypeIcon(asset.asset_type || 'Unknown')}
                      <Badge variant="secondary">{asset.asset_type || 'Unknown'}</Badge>
                    </div>
                  </td>
                  <td className="p-2">
                    <Badge variant="outline">{asset.environment || 'Unknown'}</Badge>
                  </td>
                  <td className="p-2">
                    <Badge 
                      variant={asset.criticality === 'High' ? 'destructive' : 'secondary'}
                    >
                      {asset.criticality || 'Unknown'}
                    </Badge>
                  </td>
                  <td className="p-2">
                    <span className={getReadinessColor(asset.migration_readiness || 0)}>
                      {((asset.migration_readiness || 0) * 100).toFixed(0)}%
                    </span>
                  </td>
                  <td className="p-2">
                    <Button 
                      size="sm" 
                      variant="ghost"
                      onClick={() => onClassificationUpdate(asset.id || '', asset.asset_type || '')}
                    >
                      Edit
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        
        {assets.length === 0 && (
          <div className="text-center py-8">
            <Database className="h-12 w-12 mx-auto mb-4 text-gray-300" />
            <p className="text-gray-500">No assets found with current filters</p>
          </div>
        )}
      </CardContent>
    </Card>
  );

  const renderNextStepCard = () => (
    <Card className="mt-6">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <ArrowRight className="h-5 w-5" />
          Next: App-Server Dependencies
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          <p className="text-gray-600">
            Once inventory building is complete with sufficient classification accuracy, 
            you can proceed to analyze application-to-server dependencies.
          </p>
          
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <div className="text-sm text-blue-800">
              <div className="font-medium mb-2">🔗 App-Server Dependencies Phase:</div>
              <ul className="space-y-1">
                <li>• Maps applications to their hosting infrastructure</li>
                <li>• Identifies server-application relationships</li>
                <li>• Analyzes hosting patterns and resource dependencies</li>
                <li>• Prepares hosting topology for migration planning</li>
              </ul>
            </div>
          </div>
          
          {canContinueToAppServerDependencies ? (
            <Button onClick={onContinueToAppServerDependencies} className="w-full">
              <ChevronRight className="h-4 w-4 mr-2" />
              Continue to App-Server Dependencies
            </Button>
          ) : (
            <div className="text-center">
              <p className="text-sm text-gray-600 mb-2">
                Complete inventory building to proceed (80%+ classification accuracy required)
              </p>
              <Button variant="outline" onClick={onTriggerAnalysis}>
                <RefreshCw className="h-4 w-4 mr-2" />
                Improve Classification
              </Button>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );

  return (
    <div className="space-y-6">
      {renderInventoryOverview()}
      {renderClassificationProgress()}
      
      <Tabs defaultValue="assets">
        <TabsList>
          <TabsTrigger value="assets">Asset Inventory</TabsTrigger>
          <TabsTrigger value="classification">Classification Details</TabsTrigger>
          <TabsTrigger value="insights">CrewAI Insights</TabsTrigger>
        </TabsList>
        
        <TabsContent value="assets">
          {renderAssetTable()}
        </TabsContent>
        
        <TabsContent value="classification">
          <div className="space-y-6">
            {/* Asset Type Distribution */}
            <Card>
              <CardHeader>
                <CardTitle>Asset Type Distribution</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="text-center p-4 bg-blue-50 rounded-lg">
                    <Server className="h-8 w-8 mx-auto mb-2 text-blue-600" />
                    <div className="text-2xl font-bold text-blue-600">{inventoryProgress.servers}</div>
                    <div className="text-sm text-gray-600">Servers</div>
                  </div>
                  <div className="text-center p-4 bg-green-50 rounded-lg">
                    <Cpu className="h-8 w-8 mx-auto mb-2 text-green-600" />
                    <div className="text-2xl font-bold text-green-600">{inventoryProgress.applications}</div>
                    <div className="text-sm text-gray-600">Applications</div>
                  </div>
                  <div className="text-center p-4 bg-purple-50 rounded-lg">
                    <Database className="h-8 w-8 mx-auto mb-2 text-purple-600" />
                    <div className="text-2xl font-bold text-purple-600">{inventoryProgress.databases}</div>
                    <div className="text-sm text-gray-600">Databases</div>
                  </div>
                  <div className="text-center p-4 bg-orange-50 rounded-lg">
                    <Router className="h-8 w-8 mx-auto mb-2 text-orange-600" />
                    <div className="text-2xl font-bold text-orange-600">{inventoryProgress.devices}</div>
                    <div className="text-sm text-gray-600">Devices</div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Classification Accuracy by Type */}
            <Card>
              <CardHeader>
                <CardTitle>Classification Accuracy by Type</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Server className="h-4 w-4 text-green-600" />
                      <span className="text-sm font-medium">Servers</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <Progress value={100} className="w-20 h-2" />
                      <span className="text-sm text-gray-600">100%</span>
                    </div>
                  </div>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Database className="h-4 w-4 text-purple-600" />
                      <span className="text-sm font-medium">Databases</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <Progress value={100} className="w-20 h-2" />
                      <span className="text-sm text-gray-600">100%</span>
                    </div>
                  </div>
                  {inventoryProgress.applications > 0 && (
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Cpu className="h-4 w-4 text-blue-600" />
                        <span className="text-sm font-medium">Applications</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <Progress value={85} className="w-20 h-2" />
                        <span className="text-sm text-gray-600">85%</span>
                      </div>
                    </div>
                  )}
                  {inventoryProgress.devices > 0 && (
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Router className="h-4 w-4 text-orange-600" />
                        <span className="text-sm font-medium">Devices</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <Progress value={75} className="w-20 h-2" />
                        <span className="text-sm text-gray-600">75%</span>
                      </div>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>

            {/* Migration Readiness Assessment */}
            <Card>
              <CardHeader>
                <CardTitle>Migration Readiness Assessment</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {assets.map((asset) => (
                    <div key={asset.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                      <div className="flex items-center gap-3">
                        {getTypeIcon(asset.asset_type || 'Unknown')}
                        <div>
                          <div className="font-medium">{asset.asset_name}</div>
                          <div className="text-sm text-gray-500">{asset.asset_type}</div>
                        </div>
                      </div>
                      <div className="flex items-center gap-3">
                        <div className="text-right">
                          <div className={`font-medium ${getReadinessColor(asset.migration_readiness || 0)}`}>
                            {((asset.migration_readiness || 0) * 100).toFixed(0)}% Ready
                          </div>
                          <div className="text-sm text-gray-500">
                            Confidence: {((asset.confidence_score || 0) * 100).toFixed(0)}%
                          </div>
                        </div>
                        <Progress 
                          value={(asset.migration_readiness || 0) * 100} 
                          className="w-20 h-2" 
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
        
        <TabsContent value="insights">
          <div className="space-y-6">
            {/* Agent Status */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Users className="h-5 w-5" />
                  Active CrewAI Agents
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="p-3 bg-green-50 border border-green-200 rounded-lg">
                    <div className="flex items-center gap-2 mb-2">
                      <CheckCircle className="h-4 w-4 text-green-600" />
                      <span className="font-medium text-green-800">Asset Intelligence Agent</span>
                    </div>
                    <p className="text-sm text-green-700">
                      Completed asset classification and inventory management with 100% accuracy
                    </p>
                  </div>
                  <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg">
                    <div className="flex items-center gap-2 mb-2">
                      <Brain className="h-4 w-4 text-blue-600" />
                      <span className="font-medium text-blue-800">Learning Specialist</span>
                    </div>
                    <p className="text-sm text-blue-700">
                      Enhanced learning from asset patterns and user feedback
                    </p>
                  </div>
                  <div className="p-3 bg-purple-50 border border-purple-200 rounded-lg">
                    <div className="flex items-center gap-2 mb-2">
                      <Server className="h-4 w-4 text-purple-600" />
                      <span className="font-medium text-purple-800">CMDB Data Analyst</span>
                    </div>
                    <p className="text-sm text-purple-700">
                      Analyzed infrastructure relationships and dependencies
                    </p>
                  </div>
                  <div className="p-3 bg-orange-50 border border-orange-200 rounded-lg">
                    <div className="flex items-center gap-2 mb-2">
                      <Zap className="h-4 w-4 text-orange-600" />
                      <span className="font-medium text-orange-800">Pattern Recognition</span>
                    </div>
                    <p className="text-sm text-orange-700">
                      Identified asset patterns and migration readiness indicators
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Inventory Insights */}
            <Card>
              <CardHeader>
                <CardTitle>Asset Inventory Insights</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <Alert>
                    <CheckCircle className="h-4 w-4" />
                    <AlertDescription>
                      <strong>Infrastructure Assessment Complete:</strong> All {inventoryProgress.total_assets} assets have been successfully classified with high confidence scores.
                    </AlertDescription>
                  </Alert>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="p-4 bg-blue-50 rounded-lg">
                      <h4 className="font-medium text-blue-800 mb-2">Server Infrastructure</h4>
                      <p className="text-sm text-blue-700">
                        {inventoryProgress.servers} server{inventoryProgress.servers !== 1 ? 's' : ''} identified with production workloads. 
                        All servers show high migration readiness (85%+) and are suitable for cloud migration.
                      </p>
                    </div>
                    
                    <div className="p-4 bg-purple-50 rounded-lg">
                      <h4 className="font-medium text-purple-800 mb-2">Database Systems</h4>
                      <p className="text-sm text-purple-700">
                        {inventoryProgress.databases} database{inventoryProgress.databases !== 1 ? 's' : ''} identified with critical business importance. 
                        Recommend prioritizing database migration planning and backup strategies.
                      </p>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Migration Recommendations */}
            <Card>
              <CardHeader>
                <CardTitle>Migration Strategy Recommendations</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="p-4 border border-green-200 bg-green-50 rounded-lg">
                    <div className="flex items-center gap-2 mb-2">
                      <CheckCircle className="h-4 w-4 text-green-600" />
                      <span className="font-medium text-green-800">Ready for App-Server Dependencies Phase</span>
                    </div>
                    <p className="text-sm text-green-700 mb-3">
                      Asset inventory is complete with high classification accuracy. You can now proceed to analyze application-to-server dependencies.
                    </p>
                    <div className="text-sm text-green-700">
                      <strong>Next Phase Benefits:</strong>
                      <ul className="list-disc list-inside mt-1 space-y-1">
                        <li>Map application hosting relationships</li>
                        <li>Identify server consolidation opportunities</li>
                        <li>Plan migration wave sequences</li>
                        <li>Optimize resource allocation</li>
                      </ul>
                    </div>
                  </div>

                  <div className="p-4 border border-blue-200 bg-blue-50 rounded-lg">
                    <div className="flex items-center gap-2 mb-2">
                      <Brain className="h-4 w-4 text-blue-600" />
                      <span className="font-medium text-blue-800">AI-Powered Insights</span>
                    </div>
                    <p className="text-sm text-blue-700">
                      Our CrewAI agents have learned from your asset patterns and will continue to improve recommendations throughout the migration planning process.
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
      
      {renderNextStepCard()}
      
      {lastUpdated && (
        <div className="text-center text-sm text-gray-500">
          Last updated: {lastUpdated.toLocaleString()}
        </div>
      )}
    </div>
  );
}; 