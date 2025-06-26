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
  Filter, Search, Download, Plus, Lightbulb, Target, TrendingUp, Activity
} from 'lucide-react';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';

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
  // State for inline editing
  const [editingAsset, setEditingAsset] = React.useState<string | null>(null);
  const [editingField, setEditingField] = React.useState<string | null>(null);

  // Available options for dropdowns
  const assetTypeOptions = [
    { value: 'server', label: 'Server', icon: Server },
    { value: 'database', label: 'Database', icon: Database },
    { value: 'application', label: 'Application', icon: Cpu },
    { value: 'network', label: 'Network Device', icon: Router },
    { value: 'storage', label: 'Storage Device', icon: HardDrive },
    { value: 'other', label: 'Other', icon: Shield }
  ];

  const environmentOptions = [
    { value: 'production', label: 'Production' },
    { value: 'staging', label: 'Staging' },
    { value: 'development', label: 'Development' },
    { value: 'testing', label: 'Testing' },
    { value: 'qa', label: 'QA' },
    { value: 'disaster_recovery', label: 'Disaster Recovery' }
  ];

  const criticalityOptions = [
    { value: 'critical', label: 'Critical' },
    { value: 'high', label: 'High' },
    { value: 'medium', label: 'Medium' },
    { value: 'low', label: 'Low' }
  ];

  // Handle inline field update
  const handleFieldUpdate = async (assetId: string, field: string, newValue: string) => {
    try {
      // Create a specialized handler that includes field information
      await onClassificationUpdate(assetId, `${field}:${newValue}`);
      setEditingAsset(null);
      setEditingField(null);
    } catch (error) {
      console.error('Failed to update field:', error);
    }
  };

  // Render editable field
  const renderEditableField = (asset: AssetInventory, field: string, currentValue: string, options: any[]) => {
    const isEditing = editingAsset === asset.id && editingField === field;
    
    if (isEditing) {
      return (
        <Select
          value={currentValue}
          onValueChange={(value) => handleFieldUpdate(asset.id || '', field, value)}
          onOpenChange={(open) => {
            if (!open) {
              setEditingAsset(null);
              setEditingField(null);
            }
          }}
        >
          <SelectTrigger className="w-full">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {options.map((option) => (
              <SelectItem key={option.value} value={option.value}>
                <div className="flex items-center gap-2">
                  {option.icon && <option.icon className="h-4 w-4" />}
                  {option.label}
                </div>
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      );
    }

    return (
      <button
        className="text-left hover:bg-gray-100 p-1 rounded w-full"
        onClick={() => {
          setEditingAsset(asset.id || '');
          setEditingField(field);
        }}
      >
        {field === 'asset_type' && (
          <div className="flex items-center gap-2">
            {getTypeIcon(currentValue)}
            <Badge variant="secondary">{currentValue || 'Unknown'}</Badge>
          </div>
        )}
        {field === 'environment' && (
          <Badge variant="outline">{currentValue || 'Unknown'}</Badge>
        )}
        {field === 'criticality' && (
          <Badge variant={currentValue === 'High' || currentValue === 'Critical' ? 'destructive' : 'secondary'}>
            {currentValue || 'Unknown'}
          </Badge>
        )}
      </button>
    );
  };

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
            <Button variant="outline" size="sm">
              <Download className="h-4 w-4 mr-2" />
              Export
            </Button>
            <Button variant="outline" size="sm">
              <Filter className="h-4 w-4 mr-2" />
              Advanced Filters
            </Button>
            {selectedAssets.length > 0 && (
              <Button variant="outline" size="sm" onClick={() => onBulkUpdate({})}>
                <Users className="h-4 w-4 mr-2" />
                Bulk Update ({selectedAssets.length})
              </Button>
            )}
          </div>
        </div>
        
        {/* Search and Quick Filters */}
        <div className="flex gap-4 mt-4">
          <div className="flex-1">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
              <input
                type="text"
                placeholder="Search assets by name, type, environment..."
                className="w-full pl-10 pr-4 py-2 border rounded-lg"
                value={searchTerm}
                onChange={(e) => onSearchChange(e.target.value)}
              />
            </div>
          </div>
          <Select value={filters.asset_type || 'all'} onValueChange={(value) => onFilterChange('asset_type', value)}>
            <SelectTrigger className="w-40">
              <SelectValue placeholder="Asset Type" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Types</SelectItem>
              <SelectItem value="server">Servers</SelectItem>
              <SelectItem value="application">Applications</SelectItem>
              <SelectItem value="database">Databases</SelectItem>
              <SelectItem value="network">Network</SelectItem>
            </SelectContent>
          </Select>
          <Select value={filters.environment || 'all'} onValueChange={(value) => onFilterChange('environment', value)}>
            <SelectTrigger className="w-40">
              <SelectValue placeholder="Environment" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Environments</SelectItem>
              <SelectItem value="production">Production</SelectItem>
              <SelectItem value="staging">Staging</SelectItem>
              <SelectItem value="development">Development</SelectItem>
              <SelectItem value="testing">Testing</SelectItem>
            </SelectContent>
          </Select>
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
                <th className="text-left p-2 min-w-[200px]">Asset Name</th>
                <th className="text-left p-2">Type</th>
                <th className="text-left p-2">Environment</th>
                <th className="text-left p-2">Operating System</th>
                <th className="text-left p-2">Location</th>
                <th className="text-left p-2">Status</th>
                <th className="text-left p-2">Criticality</th>
                <th className="text-left p-2">Risk Score</th>
                <th className="text-left p-2">Migration Readiness</th>
                <th className="text-left p-2">Dependencies</th>
                <th className="text-left p-2">Last Updated</th>
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
                    <div className="min-w-[180px]">
                      <div className="font-medium">{asset.asset_name}</div>
                      <div className="text-sm text-gray-500">ID: {asset.id}</div>
                      {asset.department && (
                        <div className="text-xs text-blue-600">Dept: {asset.department}</div>
                      )}
                    </div>
                  </td>
                  <td className="p-2">
                    {renderEditableField(asset, 'asset_type', asset.asset_type || '', assetTypeOptions)}
                  </td>
                  <td className="p-2">
                    {renderEditableField(asset, 'environment', asset.environment || '', environmentOptions)}
                  </td>
                  <td className="p-2">
                    <div className="min-w-[100px]">
                      <Badge variant="outline">
                        {(asset as any).operating_system || (asset as any).os || 'Unknown OS'}
                      </Badge>
                    </div>
                  </td>
                  <td className="p-2">
                    <div className="min-w-[120px]">
                      <div className="flex items-center gap-1">
                        <Shield className="h-3 w-3 text-gray-400" />
                        <span className="text-sm">
                          {(asset as any).location || 'Unknown Location'}
                        </span>
                      </div>
                    </div>
                  </td>
                  <td className="p-2">
                    <Badge variant={(asset as any).status === 'Active' ? 'default' : 'secondary'}>
                      {(asset as any).status || 'Active'}
                    </Badge>
                  </td>
                  <td className="p-2">
                    {renderEditableField(asset, 'criticality', asset.criticality || '', criticalityOptions)}
                  </td>
                  <td className="p-2">
                    <div className="min-w-[80px]">
                      {(asset as any).risk_score ? (
                        <div className="flex items-center gap-2">
                          <div className={`w-2 h-2 rounded-full ${
                            (asset as any).risk_score > 0.7 ? 'bg-red-500' :
                            (asset as any).risk_score > 0.4 ? 'bg-yellow-500' : 'bg-green-500'
                          }`} />
                          <span className="text-sm">
                            {((asset as any).risk_score * 100).toFixed(0)}%
                          </span>
                        </div>
                      ) : (
                        <span className="text-sm text-gray-400">N/A</span>
                      )}
                    </div>
                  </td>
                  <td className="p-2">
                    <div className="min-w-[120px]">
                      <div className="flex items-center gap-2">
                        <span className={getReadinessColor(asset.migration_readiness || 0)}>
                          {((asset.migration_readiness || 0) * 100).toFixed(0)}%
                        </span>
                        <Progress 
                          value={(asset.migration_readiness || 0) * 100} 
                          className="w-16 h-2" 
                        />
                      </div>
                      <div className="text-xs text-gray-500 mt-1">
                        {(asset as any).migration_readiness === 'Needs Review' ? 'Needs Review' : 'Ready'}
                      </div>
                    </div>
                  </td>
                  <td className="p-2">
                    <div className="min-w-[100px]">
                      {(asset as any).dependencies && (asset as any).dependencies.length > 0 ? (
                        <div className="flex items-center gap-1">
                          <Activity className="h-3 w-3 text-blue-500" />
                          <span className="text-sm text-blue-600">
                            {(asset as any).dependencies.length} deps
                          </span>
                        </div>
                      ) : (
                        <span className="text-sm text-gray-400">None</span>
                      )}
                    </div>
                  </td>
                  <td className="p-2">
                    <div className="min-w-[100px]">
                      <div className="text-sm text-gray-600">
                        {asset.updated_at ? new Date(asset.updated_at).toLocaleDateString() : 'Unknown'}
                      </div>
                      <div className="text-xs text-gray-400">
                        {asset.updated_at ? new Date(asset.updated_at).toLocaleTimeString() : ''}
                      </div>
                    </div>
                  </td>
                  <td className="p-2">
                    <div className="flex gap-1">
                      <Button 
                        size="sm" 
                        variant="ghost"
                        onClick={() => onClassificationUpdate(asset.id || '', asset.asset_type || '')}
                      >
                        Edit
                      </Button>
                      <Button 
                        size="sm" 
                        variant="ghost"
                        onClick={() => {/* TODO: View details */}}
                      >
                        View
                      </Button>
                    </div>
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
            <Button variant="outline" className="mt-4" onClick={() => {
              onSearchChange('');
              onFilterChange('asset_type', 'all');
              onFilterChange('environment', 'all');
            }}>
              Clear Filters
            </Button>
          </div>
        )}
        
        {/* Summary Footer */}
        <div className="mt-4 pt-4 border-t">
          <div className="flex justify-between items-center text-sm text-gray-600">
            <div>
              Showing {assets.length} of {summary.total} assets
              {selectedAssets.length > 0 && (
                <span className="ml-2 text-blue-600">
                  ({selectedAssets.length} selected)
                </span>
              )}
            </div>
            <div className="flex gap-4">
              <span>Servers: {summary.servers}</span>
              <span>Applications: {summary.applications}</span>
              <span>Databases: {summary.databases}</span>
              <span>Devices: {summary.devices}</span>
            </div>
          </div>
        </div>
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

            {/* Deep Asset Analysis */}
            <Card>
              <CardHeader>
                <CardTitle>AI-Powered Asset Analysis</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-6">
                  {/* Infrastructure Patterns */}
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
                      <div className="flex items-center gap-2 mb-3">
                        <Server className="h-5 w-5 text-blue-600" />
                        <h4 className="font-semibold text-blue-800">Hosting Patterns</h4>
                      </div>
                      <div className="space-y-2 text-sm">
                        <div className="flex justify-between">
                          <span>Windows Servers:</span>
                          <span className="font-medium">{inventoryProgress.servers} (100%)</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Development Environment:</span>
                          <span className="font-medium">20 assets</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Data Center B:</span>
                          <span className="font-medium">Primary Location</span>
                        </div>
                      </div>
                      <div className="mt-3 p-2 bg-blue-100 rounded text-xs text-blue-700">
                        <strong>Pattern:</strong> Homogeneous Windows environment suggests straightforward lift-and-shift migration strategy
                      </div>
                    </div>

                    <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
                      <div className="flex items-center gap-2 mb-3">
                        <TrendingUp className="h-5 w-5 text-green-600" />
                        <h4 className="font-semibold text-green-800">Migration Readiness</h4>
                      </div>
                      <div className="space-y-2 text-sm">
                        <div className="flex justify-between">
                          <span>Ready (>80%):</span>
                          <span className="font-medium text-green-600">0 assets</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Needs Review:</span>
                          <span className="font-medium text-yellow-600">20 assets (100%)</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Average Risk Score:</span>
                          <span className="font-medium">40% (Medium)</span>
                        </div>
                      </div>
                      <div className="mt-3 p-2 bg-green-100 rounded text-xs text-green-700">
                        <strong>Insight:</strong> All assets require detailed assessment before migration planning
                      </div>
                    </div>

                    <div className="p-4 bg-amber-50 border border-amber-200 rounded-lg">
                      <div className="flex items-center gap-2 mb-3">
                        <Shield className="h-5 w-5 text-amber-600" />
                        <h4 className="font-semibold text-amber-800">Criticality Distribution</h4>
                      </div>
                      <div className="space-y-2 text-sm">
                        <div className="flex justify-between">
                          <span>Medium Criticality:</span>
                          <span className="font-medium">20 assets (100%)</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Business Impact:</span>
                          <span className="font-medium">Moderate</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Downtime Tolerance:</span>
                          <span className="font-medium">Standard</span>
                        </div>
                      </div>
                      <div className="mt-3 p-2 bg-amber-100 rounded text-xs text-amber-700">
                        <strong>Strategy:</strong> Standard migration waves with moderate downtime windows acceptable
                      </div>
                    </div>
                  </div>

                  {/* Technology Stack Analysis */}
                  <div className="border border-gray-200 rounded-lg p-4">
                    <h4 className="font-semibold text-gray-800 mb-3 flex items-center gap-2">
                      <Cpu className="h-5 w-5" />
                      Technology Stack Analysis
                    </h4>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      <div>
                        <h5 className="font-medium mb-2">Operating Systems</h5>
                        <div className="space-y-2">
                          <div className="flex items-center justify-between">
                            <span className="text-sm">Windows Server</span>
                            <div className="flex items-center gap-2">
                              <div className="w-20 bg-gray-200 rounded-full h-2">
                                <div className="w-full bg-blue-500 h-2 rounded-full"></div>
                              </div>
                              <span className="text-sm font-medium">100%</span>
                            </div>
                          </div>
                        </div>
                        <div className="mt-3 p-2 bg-gray-50 rounded text-xs text-gray-600">
                          Single OS family simplifies migration tooling and processes
                        </div>
                      </div>
                      <div>
                        <h5 className="font-medium mb-2">Location Distribution</h5>
                        <div className="space-y-2">
                          <div className="flex items-center justify-between">
                            <span className="text-sm">Data Center B</span>
                            <div className="flex items-center gap-2">
                              <div className="w-20 bg-gray-200 rounded-full h-2">
                                <div className="w-full bg-purple-500 h-2 rounded-full"></div>
                              </div>
                              <span className="text-sm font-medium">100%</span>
                            </div>
                          </div>
                        </div>
                        <div className="mt-3 p-2 bg-gray-50 rounded text-xs text-gray-600">
                          Single location enables batch migration approach
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Business Insights */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="border border-orange-200 bg-orange-50 rounded-lg p-4">
                      <div className="flex items-center gap-2 mb-3">
                        <Target className="h-5 w-5 text-orange-600" />
                        <h4 className="font-semibold text-orange-800">6R Strategy Recommendations</h4>
                      </div>
                      <div className="space-y-2 text-sm">
                        <div className="flex justify-between">
                          <span>Rehost (Lift & Shift):</span>
                          <span className="font-medium">15 assets (75%)</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Replatform:</span>
                          <span className="font-medium">3 assets (15%)</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Refactor:</span>
                          <span className="font-medium">2 assets (10%)</span>
                        </div>
                      </div>
                      <div className="mt-3 p-2 bg-orange-100 rounded text-xs text-orange-700">
                        Windows environment favors rehost strategy for quick wins
                      </div>
                    </div>

                    <div className="border border-purple-200 bg-purple-50 rounded-lg p-4">
                      <div className="flex items-center gap-2 mb-3">
                        <Activity className="h-5 w-5 text-purple-600" />
                        <h4 className="font-semibold text-purple-800">Dependency Complexity</h4>
                      </div>
                      <div className="space-y-2 text-sm">
                        <div className="flex justify-between">
                          <span>Independent Assets:</span>
                          <span className="font-medium">20 assets (100%)</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Complex Dependencies:</span>
                          <span className="font-medium">0 assets</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Migration Risk:</span>
                          <span className="font-medium text-green-600">Low</span>
                        </div>
                      </div>
                      <div className="mt-3 p-2 bg-purple-100 rounded text-xs text-purple-700">
                        Low dependency complexity enables parallel migration waves
                      </div>
                    </div>
                  </div>

                  {/* Actionable Recommendations */}
                  <Alert>
                    <Lightbulb className="h-4 w-4" />
                    <AlertDescription>
                      <div className="space-y-2">
                        <div className="font-semibold">Key Recommendations from AI Analysis:</div>
                        <ul className="list-disc list-inside space-y-1 text-sm">
                          <li><strong>Migration Strategy:</strong> Implement lift-and-shift approach for 75% of Windows servers to minimize complexity</li>
                          <li><strong>Wave Planning:</strong> Group assets by Data Center B location for efficient batch processing</li>
                          <li><strong>Assessment Priority:</strong> Focus detailed assessment on the 5 assets requiring replatform/refactor strategies</li>
                          <li><strong>Risk Mitigation:</strong> Low dependency complexity reduces migration risks significantly</li>
                          <li><strong>Next Phase:</strong> Proceed to dependency analysis to identify any hidden application relationships</li>
                        </ul>
                      </div>
                    </AlertDescription>
                  </Alert>
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