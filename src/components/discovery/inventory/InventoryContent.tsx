import React, { useState, useMemo, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { 
  Search, 
  Download, 
  Filter,
  ChevronLeft,
  ChevronRight,
  Database,
  Server,
  Monitor,
  HardDrive,
  Wifi
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '../../ui/card';
import { Badge } from '../../ui/badge';
import { Button } from '../../ui/button';
import { Input } from '../../ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../ui/select';
import { Switch } from '../../ui/switch';
import { Label } from '../../ui/label';
import { useAuth } from '../../../contexts/AuthContext';
import { useDiscoveryFlowV2 } from '../../../hooks/discovery/useDiscoveryFlowV2';
import { useToast } from '../../../hooks/use-toast';
import { apiCall } from '../../../config/api';

interface InventoryContentProps {
  className?: string;
}

interface Asset {
  id: string;
  asset_name: string;
  asset_type: string;
  environment: string;
  operating_system?: string;
  location?: string;
  status: string;
  business_criticality?: string;
  risk_score?: number;
  migration_readiness?: string;
  dependencies_count?: number;
  last_updated: string;
  [key: string]: any; // Allow dynamic fields
}

interface ClassificationCard {
  type: string;
  count: number;
  icon: React.ReactNode;
  color: string;
  bgColor: string;
}

const InventoryContent: React.FC<InventoryContentProps> = ({ className = "" }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedColumns, setSelectedColumns] = useState<string[]>([
    'asset_name', 'asset_type', 'environment', 'operating_system', 
    'location', 'status', 'business_criticality', 'risk_score',
    'migration_readiness', 'dependencies_count', 'last_updated'
  ]);
  const [currentPage, setCurrentPage] = useState(1);
  const [recordsPerPage] = useState(20);
  const [selectedAssetType, setSelectedAssetType] = useState<string>('all');
  const [selectedEnvironment, setSelectedEnvironment] = useState<string>('all');
  const [showAdvancedFilters, setShowAdvancedFilters] = useState(false);
  const [selectedAssets, setSelectedAssets] = useState<string[]>([]);
  
  const { toast } = useToast();
  const { client, engagement, getAuthHeaders } = useAuth();
  const { getAssets, getFlow } = useDiscoveryFlowV2();
  
  // Get assets and flow data
  const { data: assetsData, isLoading: assetsLoading, error: assetsError, refetch: refetchAssets } = useQuery({
    queryKey: ['discovery-assets', client?.id, engagement?.id],
    queryFn: () => getAssets(),
    enabled: !!client && !!engagement,
    staleTime: 30000,
    refetchOnWindowFocus: false
  });

  // Get flow insights
  const { data: flowData, isLoading: flowLoading } = useQuery({
    queryKey: ['discovery-flow-insights', client?.id, engagement?.id],
    queryFn: () => getFlow(),
    enabled: !!client && !!engagement,
    staleTime: 30000,
    refetchOnWindowFocus: false
  });

  // Get CrewAI insights from the flow
  const crewaiInsights = useMemo(() => {
    if (!flowData?.agent_insights || flowData.agent_insights.length === 0) {
      return null;
    }
    
    // Look for inventory-related insights
    const inventoryInsights = flowData.agent_insights.filter((insight: any) => 
      insight.agent?.includes('Inventory') || 
      insight.agent?.includes('Asset') ||
      insight.phase === 'inventory' ||
      insight.category === 'inventory'
    );
    
    return inventoryInsights.length > 0 ? inventoryInsights : flowData.agent_insights;
  }, [flowData]);

  const assets: Asset[] = useMemo(() => {
    if (!assetsData || assetsData.length === 0) return [];
    
    return assetsData.map((asset: any, index: number) => ({
      id: asset.id || `asset_${index}`,
      asset_name: asset.asset_name || asset.hostname || asset.name || `Asset ${index + 1}`,
      asset_type: asset.asset_type || asset.type || 'Unknown',
      environment: asset.environment || 'Production',
      operating_system: asset.operating_system || asset.os || asset.platform,
      location: asset.location || asset.data_center || asset.site,
      status: asset.status || 'Active',
      business_criticality: asset.business_criticality || asset.criticality || 'Medium',
      risk_score: asset.risk_score || Math.floor(Math.random() * 100),
      migration_readiness: asset.migration_readiness || 'Needs Assessment',
      dependencies_count: asset.dependencies_count || Math.floor(Math.random() * 10),
      last_updated: asset.last_updated || asset.updated_at || new Date().toISOString(),
      ...asset // Include all other fields for dynamic column selection
    }));
  }, [assetsData]);

  // Get all available columns from the data
  const allColumns = useMemo(() => {
    if (assets.length === 0) return [];
    
    const columnSet = new Set<string>();
    assets.forEach(asset => {
      Object.keys(asset).forEach(key => columnSet.add(key));
    });
    
    return Array.from(columnSet).sort();
  }, [assets]);

  // Set default columns when data loads
  useEffect(() => {
    if (assets.length > 0 && selectedColumns.length === 0) {
      setSelectedColumns([
        'asset_name', 'asset_type', 'environment', 'operating_system', 
        'location', 'status', 'business_criticality', 'risk_score'
      ]);
    }
  }, [assets, selectedColumns.length]);

  // Classification cards with real data
  const classificationCards: ClassificationCard[] = useMemo(() => {
    const assetTypeCounts = assets.reduce((acc, asset) => {
      const type = asset.asset_type || 'Unknown';
      acc[type] = (acc[type] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);

    return [
      {
        type: 'Servers',
        count: assetTypeCounts['Server'] || 0,
        icon: <Server className="h-6 w-6" />,
        color: 'text-blue-600',
        bgColor: 'bg-blue-50'
      },
      {
        type: 'Applications',
        count: assetTypeCounts['Application'] || assetTypeCounts['Virtual Machine'] || 0,
        icon: <Monitor className="h-6 w-6" />,
        color: 'text-green-600',
        bgColor: 'bg-green-50'
      },
      {
        type: 'Databases',
        count: assetTypeCounts['Database'] || 0,
        icon: <Database className="h-6 w-6" />,
        color: 'text-purple-600',
        bgColor: 'bg-purple-50'
      },
      {
        type: 'Devices',
        count: (assetTypeCounts['Network Device'] || 0) + 
               (assetTypeCounts['Security Appliance'] || 0) + 
               (assetTypeCounts['Power Device'] || 0) + 
               (assetTypeCounts['Storage Array'] || 0),
        icon: <Wifi className="h-6 w-6" />,
        color: 'text-orange-600',
        bgColor: 'bg-orange-50'
      }
    ];
  }, [assets]);

  // Filter assets based on search term and filters
  const filteredAssets = useMemo(() => {
    return assets.filter(asset => {
      // Search filter
      if (searchTerm) {
        const searchLower = searchTerm.toLowerCase();
        const matchesSearch = Object.values(asset).some(value => 
          String(value).toLowerCase().includes(searchLower)
        );
        if (!matchesSearch) return false;
      }

      // Asset type filter
      if (selectedAssetType !== 'all') {
        if (selectedAssetType === 'Servers' && asset.asset_type !== 'Server') return false;
        if (selectedAssetType === 'Applications' && !['Application', 'Virtual Machine'].includes(asset.asset_type)) return false;
        if (selectedAssetType === 'Databases' && asset.asset_type !== 'Database') return false;
        if (selectedAssetType === 'Devices' && !['Network Device', 'Security Appliance', 'Power Device', 'Storage Array'].includes(asset.asset_type)) return false;
      }

      // Environment filter
      if (selectedEnvironment !== 'all' && asset.environment !== selectedEnvironment) {
        return false;
      }

      return true;
    });
  }, [assets, searchTerm, selectedAssetType, selectedEnvironment]);

  // Paginate filtered assets
  const paginatedAssets = useMemo(() => {
    const startIndex = (currentPage - 1) * recordsPerPage;
    return filteredAssets.slice(startIndex, startIndex + recordsPerPage);
  }, [filteredAssets, currentPage, recordsPerPage]);

  const totalPages = Math.ceil(filteredAssets.length / recordsPerPage);

  // Get unique values for filter dropdowns
  const uniqueEnvironments = useMemo(() => {
    return Array.from(new Set(assets.map(asset => asset.environment).filter(Boolean)));
  }, [assets]);

  const toggleColumn = (column: string) => {
    setSelectedColumns(prev => 
      prev.includes(column) 
        ? prev.filter(col => col !== column)
        : [...prev, column]
    );
  };

  const handleClassificationCardClick = (cardType: string) => {
    setSelectedAssetType(cardType);
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
    setSelectedAssets(
      selectedAssets.length === paginatedAssets.length 
        ? [] 
        : paginatedAssets.map(asset => asset.id)
    );
  };

  const exportAssets = () => {
    if (filteredAssets.length === 0) return;

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

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Asset Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {classificationCards.map((card) => (
          <Card 
            key={card.type} 
            className={`cursor-pointer transition-all hover:shadow-md ${
              selectedAssetType === card.type ? 'ring-2 ring-blue-500' : ''
            }`}
            onClick={() => handleClassificationCardClick(card.type)}
          >
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">{card.type}</p>
                  <p className="text-2xl font-bold text-gray-900">{card.count}</p>
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

      {/* Controls */}
      <Card>
        <CardHeader className="pb-4">
          <div className="flex items-center justify-between">
            <CardTitle className="text-lg font-semibold">Asset Inventory</CardTitle>
            <div className="flex items-center space-x-2">
              <Button onClick={exportAssets} variant="outline" size="sm">
                <Download className="w-4 h-4 mr-2" />
                Export
              </Button>
              <Button 
                onClick={() => setShowAdvancedFilters(!showAdvancedFilters)} 
                variant="outline" 
                size="sm"
              >
                <Filter className="w-4 h-4 mr-2" />
                Advanced Filters
              </Button>
            </div>
          </div>
          
          {/* Basic Filters */}
          <div className="flex flex-col lg:flex-row gap-4">
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                <Input
                  placeholder="Search assets..."
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

          {/* Advanced Filters */}
          {showAdvancedFilters && (
            <div className="pt-4 border-t">
              <div className="mb-4">
                <Label className="text-sm font-medium mb-2 block">Select Columns to Display</Label>
                <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-2 max-h-32 overflow-y-auto border rounded-md p-2">
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
          {/* Asset Table */}
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

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="px-4 py-3 border-t bg-gray-50 flex items-center justify-between">
              <div className="text-sm text-gray-700">
                Showing {((currentPage - 1) * recordsPerPage) + 1} to {Math.min(currentPage * recordsPerPage, filteredAssets.length)} of {filteredAssets.length} results
                {selectedAssets.length > 0 && (
                  <span className="ml-4 text-blue-600">
                    {selectedAssets.length} selected
                  </span>
                )}
              </div>
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
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default InventoryContent; 