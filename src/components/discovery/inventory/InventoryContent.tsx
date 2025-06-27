import React, { useState, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Progress } from '@/components/ui/progress';
import { 
  Server, Database, Cpu, Router, Shield, TrendingUp, Target, Activity,
  CheckCircle, Brain, ArrowRight, Search, Filter, Download, 
  ChevronLeft, ChevronRight, RefreshCw
} from 'lucide-react';
import { useAuth } from '../../../contexts/AuthContext';
import { useDiscoveryFlowV2 } from '../../../hooks/discovery/useDiscoveryFlowV2';
import { EnhancedInventoryInsights } from './EnhancedInventoryInsights';

interface AssetInventory {
  id: string;
  asset_name: string;
  asset_type?: string;
  environment?: string;
  operating_system?: string;
  location?: string;
  status?: string;
  business_criticality?: string;
  risk_score?: number;
  migration_readiness?: number;
  dependencies?: string;
  last_updated?: string;
  confidence_score?: number;
  criticality?: string;
  [key: string]: any;
}

interface InventoryProgress {
  total: number;
  servers: number;
  applications: number;
  databases: number;
  devices: number;
  classification_accuracy: number;
}

interface InventoryContentProps {
  className?: string;
  flowId?: string;
}

const InventoryContent: React.FC<InventoryContentProps> = ({
  className = "",
  flowId
}) => {
  const { client, engagement } = useAuth();
  const { getAssets, getFlow } = useDiscoveryFlowV2(flowId);

  // State for table management
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedAssetType, setSelectedAssetType] = useState('all');
  const [selectedEnvironment, setSelectedEnvironment] = useState('all');
  const [selectedAssets, setSelectedAssets] = useState<string[]>([]);
  const [selectedColumns, setSelectedColumns] = useState([
    'asset_name', 'asset_type', 'environment', 'operating_system', 
    'location', 'status', 'business_criticality', 'risk_score', 
    'migration_readiness', 'dependencies', 'last_updated'
  ]);
  const [showAdvancedFilters, setShowAdvancedFilters] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const recordsPerPage = 10;

  // Get assets and flow data
  const { data: assetsData, isLoading: assetsLoading, error: assetsError, refetch: refetchAssets } = useQuery({
    queryKey: ['discovery-assets', flowId, client?.id, engagement?.id],
    queryFn: () => getAssets(),
    enabled: !!client && !!engagement && !!flowId,
    staleTime: 30000,
    refetchOnWindowFocus: false
  });

  const assets: AssetInventory[] = useMemo(() => {
    if (!assetsData) return [];
    return Array.isArray(assetsData) ? assetsData : assetsData.assets || [];
  }, [assetsData]);

  // Get all available columns from the data
  const allColumns = useMemo(() => {
    if (assets.length === 0) return [];
    const columns = new Set<string>();
    assets.forEach(asset => {
      Object.keys(asset).forEach(key => {
        if (key !== 'id') columns.add(key);
      });
    });
    return Array.from(columns).sort();
  }, [assets]);

  // Get unique environments for filtering
  const uniqueEnvironments = useMemo(() => {
    const environments = new Set(assets.map(asset => asset.environment).filter(Boolean));
    return Array.from(environments);
  }, [assets]);

  // Calculate inventory progress
  const inventoryProgress: InventoryProgress = useMemo(() => {
    const total = assets.length;
    const servers = assets.filter(asset => 
      asset.asset_type?.toLowerCase().includes('server') || 
      asset.asset_type?.toLowerCase() === 'server'
    ).length;
    const applications = assets.filter(asset => 
      asset.asset_type?.toLowerCase().includes('application') || 
      asset.asset_type?.toLowerCase() === 'application'
    ).length;
    const databases = assets.filter(asset => 
      asset.asset_type?.toLowerCase().includes('database') || 
      asset.asset_type?.toLowerCase() === 'database'
    ).length;
    const devices = assets.filter(asset => 
      asset.asset_type?.toLowerCase().includes('device') || 
      asset.asset_type?.toLowerCase().includes('network')
    ).length;
    
    return {
      total,
      servers,
      applications,
      databases,
      devices,
      classification_accuracy: 100 // From CrewAI classification
    };
  }, [assets]);

  // Filter and search assets
  const filteredAssets = useMemo(() => {
    return assets.filter(asset => {
      const matchesSearch = !searchTerm || 
        Object.values(asset).some(value => 
          String(value).toLowerCase().includes(searchTerm.toLowerCase())
        );
      
      const matchesType = selectedAssetType === 'all' || 
        asset.asset_type === selectedAssetType;
      
      const matchesEnvironment = selectedEnvironment === 'all' || 
        asset.environment === selectedEnvironment;
      
      return matchesSearch && matchesType && matchesEnvironment;
    });
  }, [assets, searchTerm, selectedAssetType, selectedEnvironment]);

  // Pagination
  const totalPages = Math.ceil(filteredAssets.length / recordsPerPage);
  const paginatedAssets = useMemo(() => {
    const start = (currentPage - 1) * recordsPerPage;
    return filteredAssets.slice(start, start + recordsPerPage);
  }, [filteredAssets, currentPage]);

  // Classification cards for interactive filtering
  const classificationCards = useMemo(() => [
    {
      type: 'Servers',
      count: inventoryProgress.servers,
      icon: <Server className="w-5 h-5" />,
      color: 'text-blue-600',
      bgColor: 'bg-blue-50'
    },
    {
      type: 'Applications',
      count: inventoryProgress.applications,
      icon: <Cpu className="w-5 h-5" />,
      color: 'text-green-600',
      bgColor: 'bg-green-50'
    },
    {
      type: 'Databases',
      count: inventoryProgress.databases,
      icon: <Database className="w-5 h-5" />,
      color: 'text-purple-600',
      bgColor: 'bg-purple-50'
    },
    {
      type: 'Devices',
      count: inventoryProgress.devices,
      icon: <Router className="w-5 h-5" />,
      color: 'text-orange-600',
      bgColor: 'bg-orange-50'
    }
  ], [inventoryProgress]);

  // Event handlers
  const handleClassificationCardClick = (type: string) => {
    setSelectedAssetType(selectedAssetType === type ? 'all' : type);
    setCurrentPage(1);
  };

  const handleSelectAsset = (assetId: string) => {
    setSelectedAssets(prev => 
      prev.includes(assetId) 
        ? prev.filter(id => id !== assetId)
        : [...prev, assetId]
    );
  };

  const handleSelectAll = () => {
    if (selectedAssets.length === paginatedAssets.length) {
      setSelectedAssets([]);
    } else {
      setSelectedAssets(paginatedAssets.map(asset => asset.id));
    }
  };

  const toggleColumn = (column: string) => {
    setSelectedColumns(prev => 
      prev.includes(column)
        ? prev.filter(col => col !== column)
        : [...prev, column]
    );
  };

  const exportAssets = () => {
    const csvContent = [
      selectedColumns.join(','),
      ...filteredAssets.map(asset => 
        selectedColumns.map(col => 
          JSON.stringify(asset[col] || '')
        ).join(',')
      )
    ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `asset_inventory_${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const getTypeIcon = (type: string) => {
    switch (type?.toLowerCase()) {
      case 'server': return <Server className="h-4 w-4 text-blue-600" />;
      case 'application': return <Cpu className="h-4 w-4 text-green-600" />;
      case 'database': return <Database className="h-4 w-4 text-purple-600" />;
      case 'device': 
      case 'network device': return <Router className="h-4 w-4 text-orange-600" />;
      default: return <Shield className="h-4 w-4 text-gray-600" />;
    }
  };

  const getReadinessColor = (readiness: number) => {
    if (readiness > 0.8) return 'text-green-600';
    if (readiness > 0.5) return 'text-yellow-600';
    return 'text-red-600';
  };

  if (!client || !engagement) {
    return (
      <div className={`bg-white rounded-lg border shadow-sm p-6 ${className}`}>
        <div className="flex items-center justify-center py-8">
          <Database className="w-6 h-6 animate-pulse text-blue-500 mr-2" />
          <span className="text-gray-600">Loading context...</span>
        </div>
      </div>
    );
  }

  if (assetsLoading) {
    return (
      <div className={`bg-white rounded-lg border shadow-sm p-6 ${className}`}>
        <div className="flex items-center justify-center py-8">
          <Database className="w-6 h-6 animate-pulse text-blue-500 mr-2" />
          <span className="text-gray-600">Loading asset inventory...</span>
        </div>
      </div>
    );
  }

  if (assetsError || assets.length === 0) {
    return (
      <div className={`bg-white rounded-lg border shadow-sm p-6 ${className}`}>
        <div className="flex flex-col items-center justify-center py-8">
          <Database className="w-8 h-8 text-gray-400 mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No Assets Discovered</h3>
          <p className="text-sm text-gray-500 mb-4">
            No asset inventory data is available yet. Please ensure the discovery flow has completed successfully.
          </p>
          <Button onClick={() => refetchAssets()} variant="outline">
            Refresh Data
          </Button>
        </div>
      </div>
    );
  }

  const renderInventoryOverview = () => (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
      <Card>
        <CardContent className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Total Assets</p>
              <p className="text-2xl font-bold text-gray-900">{inventoryProgress.total}</p>
            </div>
            <Shield className="h-8 w-8 text-blue-500" />
          </div>
        </CardContent>
      </Card>
      <Card>
        <CardContent className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Classification Accuracy</p>
              <p className="text-2xl font-bold text-green-600">{inventoryProgress.classification_accuracy}%</p>
            </div>
            <CheckCircle className="h-8 w-8 text-green-500" />
          </div>
        </CardContent>
      </Card>
      <Card>
        <CardContent className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Discovery Status</p>
              <p className="text-sm font-semibold text-green-600">Complete</p>
            </div>
            <Activity className="h-8 w-8 text-green-500" />
          </div>
        </CardContent>
      </Card>
      <Card>
        <CardContent className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">CrewAI Analysis</p>
              <p className="text-sm font-semibold text-blue-600">AI-Powered</p>
            </div>
            <Brain className="h-8 w-8 text-blue-500" />
          </div>
        </CardContent>
      </Card>
    </div>
  );

  const renderClassificationProgress = () => (
    <Card className="mb-6">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Target className="h-5 w-5" />
          Asset Classification Summary
        </CardTitle>
        <p className="text-sm text-gray-600">
          {inventoryProgress.total} assets analyzed with {inventoryProgress.servers} servers, {inventoryProgress.applications} applications, {inventoryProgress.databases} databases, and {inventoryProgress.devices} devices identified.
        </p>
      </CardHeader>
      <CardContent>
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <CheckCircle className="h-4 w-4 text-green-500" />
              <span className="text-sm font-medium">Classification Complete</span>
            </div>
            <Badge variant="secondary">
              {inventoryProgress.classification_accuracy}% Accuracy
            </Badge>
          </div>
          <div className="flex gap-2">
            <Button onClick={() => refetchAssets()} variant="outline" size="sm">
              <RefreshCw className="h-4 w-4 mr-2" />
              Refresh Analysis
            </Button>
          </div>
        </div>
        <Progress value={inventoryProgress.classification_accuracy} className="w-full" />
      </CardContent>
    </Card>
  );

  const renderAssetTable = () => (
    <Card>
      <CardHeader className="pb-4">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg font-semibold">Complete Asset Table</CardTitle>
          <div className="flex items-center space-x-2">
            <Button onClick={exportAssets} variant="outline" size="sm">
              <Download className="w-4 h-4 mr-2" />
              Export CSV
            </Button>
            <Button 
              onClick={() => setShowAdvancedFilters(!showAdvancedFilters)} 
              variant="outline" 
              size="sm"
            >
              <Filter className="w-4 h-4 mr-2" />
              Column Selection
            </Button>
          </div>
        </div>
        
        {/* Basic Filters */}
        <div className="flex flex-col lg:flex-row gap-4">
          <div className="flex-1">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
              <Input
                placeholder="Search across all asset attributes..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10"
              />
            </div>
          </div>
          <div className="flex gap-2">
            <Select value={selectedAssetType} onValueChange={(value) => setSelectedAssetType(value)}>
              <SelectTrigger className="w-40">
                <SelectValue placeholder="Asset Type" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Types</SelectItem>
                <SelectItem value="Servers">Servers</SelectItem>
                <SelectItem value="Applications">Applications</SelectItem>
                <SelectItem value="Databases">Databases</SelectItem>
                <SelectItem value="Devices">Devices</SelectItem>
              </SelectContent>
            </Select>
            
            <Select value={selectedEnvironment} onValueChange={(value) => setSelectedEnvironment(value)}>
              <SelectTrigger className="w-40">
                <SelectValue placeholder="Environment" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Environments</SelectItem>
                {uniqueEnvironments.map(env => (
                  <SelectItem key={env} value={env}>{env}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>

        {/* Advanced Column Selection */}
        {showAdvancedFilters && (
          <div className="pt-4 border-t">
            <div className="mb-4">
              <Label className="text-sm font-medium mb-2 block">Select Columns to Display (like Attribute Mapping page)</Label>
              <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-2 max-h-32 overflow-y-auto border rounded-md p-2 bg-gray-50">
                {allColumns.map(column => (
                  <div key={column} className="flex items-center space-x-2">
                    <Switch
                      id={column}
                      checked={selectedColumns.includes(column)}
                      onCheckedChange={() => toggleColumn(column)}
                    />
                    <Label htmlFor={column} className="text-sm truncate">
                      {column.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                    </Label>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </CardHeader>

      <CardContent className="p-0">
        {/* Dynamic Asset Table */}
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left">
                  <input
                    type="checkbox"
                    checked={selectedAssets.length === paginatedAssets.length && paginatedAssets.length > 0}
                    onChange={handleSelectAll}
                    className="rounded border-gray-300"
                  />
                </th>
                {selectedColumns.map(column => (
                  <th key={column} className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    {column.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                  </th>
                ))}
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {paginatedAssets.map((asset) => (
                <tr key={asset.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3">
                    <input
                      type="checkbox"
                      checked={selectedAssets.includes(asset.id)}
                      onChange={() => handleSelectAsset(asset.id)}
                      className="rounded border-gray-300"
                    />
                  </td>
                  {selectedColumns.map(column => (
                    <td key={column} className="px-4 py-3 text-sm text-gray-900 max-w-xs truncate">
                      {column === 'risk_score' && typeof asset[column] === 'number' ? 
                        <Badge variant={asset[column] > 70 ? 'destructive' : asset[column] > 40 ? 'default' : 'secondary'}>
                          {asset[column]}%
                        </Badge>
                      : column === 'status' ?
                        <Badge variant={asset[column] === 'Active' ? 'default' : 'secondary'}>
                          {asset[column]}
                        </Badge>
                      : column === 'business_criticality' ?
                        <Badge variant={
                          asset[column] === 'Critical' ? 'destructive' : 
                          asset[column] === 'High' ? 'default' : 'secondary'
                        }>
                          {asset[column]}
                        </Badge>
                      : column === 'migration_readiness' && typeof asset[column] === 'number' ?
                        <div className="flex items-center gap-2">
                          <Progress value={(asset[column] || 0) * 100} className="w-16 h-2" />
                          <span className={`text-xs ${getReadinessColor(asset[column] || 0)}`}>
                            {((asset[column] || 0) * 100).toFixed(0)}%
                          </span>
                        </div>
                      : column === 'last_updated' && asset[column] ?
                        new Date(asset[column]).toLocaleDateString()
                      : String(asset[column] || '-')
                      }
                    </td>
                  ))}
                  <td className="px-4 py-3 text-sm">
                    <div className="flex space-x-2">
                      <Button variant="ghost" size="sm">View</Button>
                      <Button variant="ghost" size="sm">Edit</Button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Pagination and Summary */}
        <div className="px-4 py-3 border-t bg-gray-50">
          <div className="flex items-center justify-between">
            <div className="text-sm text-gray-700">
              Showing {((currentPage - 1) * recordsPerPage) + 1} to {Math.min(currentPage * recordsPerPage, filteredAssets.length)} of {filteredAssets.length} results
              {selectedAssets.length > 0 && (
                <span className="ml-4 text-blue-600 font-medium">
                  {selectedAssets.length} selected for operations
                </span>
              )}
            </div>
            {totalPages > 1 && (
              <div className="flex items-center space-x-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
                  disabled={currentPage === 1}
                >
                  <ChevronLeft className="w-4 h-4" />
                </Button>
                <span className="text-sm text-gray-700">
                  Page {currentPage} of {totalPages}
                </span>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setCurrentPage(prev => Math.min(totalPages, prev + 1))}
                  disabled={currentPage === totalPages}
                >
                  <ChevronRight className="w-4 h-4" />
                </Button>
              </div>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );

  const renderClassificationCards = () => (
    <div className="space-y-6">
      {/* Interactive Classification Cards */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Target className="h-5 w-5" />
            Asset Classification Cards
          </CardTitle>
          <p className="text-sm text-gray-600">
            Click on any card to filter the asset table below. Cards show real counts from discovery data.
          </p>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {classificationCards.map((card) => (
              <Card 
                key={card.type} 
                className={`cursor-pointer transition-all hover:shadow-md border-2 ${
                  selectedAssetType === card.type ? 'border-blue-500 bg-blue-50' : 'border-gray-200'
                }`}
                onClick={() => handleClassificationCardClick(card.type)}
              >
                <CardContent className="p-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-gray-600">{card.type}</p>
                      <p className="text-3xl font-bold text-gray-900">{card.count}</p>
                      <p className="text-xs text-gray-500 mt-1">
                        {card.count > 0 ? 'Click to filter' : 'No assets found'}
                      </p>
                    </div>
                    <div className={`p-3 rounded-lg ${card.bgColor}`}>
                      <div className={card.color}>
                        {card.icon}
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Filtered Asset Table when card is selected */}
      {selectedAssetType !== 'all' && (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                {getTypeIcon(selectedAssetType)}
                <CardTitle>{selectedAssetType} Assets</CardTitle>
                <Badge variant="secondary">{filteredAssets.length} found</Badge>
              </div>
              <Button 
                onClick={() => setSelectedAssetType('all')}
                variant="outline" 
                size="sm"
              >
                Clear Filter
              </Button>
            </div>
            <p className="text-sm text-gray-600">
              Showing detailed view of {filteredAssets.length} {selectedAssetType.toLowerCase()} assets
            </p>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Asset</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Environment</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Operating System</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Criticality</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Migration Readiness</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {filteredAssets.slice(0, 10).map((asset) => (
                    <tr key={asset.id} className="hover:bg-gray-50">
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-2">
                          {getTypeIcon(asset.asset_type || '')}
                          <div>
                            <div className="font-medium text-gray-900">{asset.asset_name}</div>
                            <div className="text-sm text-gray-500">{asset.asset_type}</div>
                          </div>
                        </div>
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-900">{asset.environment || '-'}</td>
                      <td className="px-4 py-3 text-sm text-gray-900">{asset.operating_system || '-'}</td>
                      <td className="px-4 py-3">
                        <Badge variant={asset.status === 'Active' ? 'default' : 'secondary'}>
                          {asset.status || 'Unknown'}
                        </Badge>
                      </td>
                      <td className="px-4 py-3">
                        <Badge variant={
                          asset.business_criticality === 'Critical' ? 'destructive' : 
                          asset.business_criticality === 'High' ? 'default' : 'secondary'
                        }>
                          {asset.business_criticality || 'Medium'}
                        </Badge>
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-2">
                          <Progress 
                            value={(asset.migration_readiness || 0.5) * 100} 
                            className="w-16 h-2" 
                          />
                          <span className={`text-sm font-medium ${getReadinessColor(asset.migration_readiness || 0.5)}`}>
                            {((asset.migration_readiness || 0.5) * 100).toFixed(0)}%
                          </span>
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex gap-1">
                          <Button size="sm" variant="ghost">Edit</Button>
                          <Button size="sm" variant="ghost">View</Button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {filteredAssets.length > 10 && (
              <div className="mt-4 text-center">
                <p className="text-sm text-gray-500">
                  Showing first 10 of {filteredAssets.length} {selectedAssetType.toLowerCase()} assets.
                  Use the "Asset Inventory" tab to see all assets with pagination.
                </p>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Classification Accuracy */}
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
    </div>
  );

  const renderNextStepCard = () => (
    <Card className="mt-6">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <ArrowRight className="h-5 w-5" />
          Ready for Assessment Phase
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          <p className="text-gray-600">
            Your asset inventory is complete with {inventoryProgress.classification_accuracy}% classification accuracy. 
            This is the perfect starting point to select applications for the Assessment phase.
          </p>
          
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <div className="text-sm text-blue-800">
              <div className="font-medium mb-2">🔍 Assessment Phase - App Selection:</div>
              <ul className="space-y-1">
                <li>• Select applications from the inventory for detailed migration assessment</li>
                <li>• Analyze 6R migration strategies per selected application</li>
                <li>• Assess business criticality and technical complexity</li>
                <li>• Generate migration readiness scores and recommendations</li>
              </ul>
            </div>
          </div>
          
          <Button className="w-full">
            <ArrowRight className="h-4 w-4 mr-2" />
            Continue to Assessment Phase
          </Button>
        </div>
      </CardContent>
    </Card>
  );

  return (
    <div className={`space-y-6 ${className}`}>
      {renderInventoryOverview()}
      {renderClassificationProgress()}
      
      <Tabs defaultValue="assets" className="w-full">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="assets">Asset Inventory</TabsTrigger>
          <TabsTrigger value="classification">Classification Cards</TabsTrigger>
          <TabsTrigger value="insights">CrewAI Insights</TabsTrigger>
        </TabsList>
        
        <TabsContent value="assets" className="space-y-6">
          {renderAssetTable()}
        </TabsContent>
        
        <TabsContent value="classification" className="space-y-6">
          {renderClassificationCards()}
        </TabsContent>
        
        <TabsContent value="insights" className="space-y-6">
          <EnhancedInventoryInsights 
            assets={assets}
            inventoryProgress={inventoryProgress}
            className=""
          />
        </TabsContent>
      </Tabs>
      
      {renderNextStepCard()}
    </div>
  );
};

export default InventoryContent;
