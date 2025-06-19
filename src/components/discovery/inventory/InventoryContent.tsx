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
          <Card>
            <CardHeader>
              <CardTitle>Classification Analysis</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-center py-8">
                <Brain className="h-12 w-12 mx-auto mb-4 text-gray-300" />
                <p className="text-gray-500">Classification details and insights coming soon</p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
        
        <TabsContent value="insights">
          <Card>
            <CardHeader>
              <CardTitle>CrewAI Insights</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-center py-8">
                <Users className="h-12 w-12 mx-auto mb-4 text-gray-300" />
                <p className="text-gray-500">Agent insights and recommendations coming soon</p>
              </div>
            </CardContent>
          </Card>
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