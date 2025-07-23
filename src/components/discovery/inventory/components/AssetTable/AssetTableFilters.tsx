import React from 'react';
import type { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import type { Filter } from 'lucide-react'
import { Search, Download, RefreshCw } from 'lucide-react'

interface AssetTableFiltersProps {
  searchTerm: string;
  onSearchChange: (value: string) => void;
  selectedEnvironment: string;
  onEnvironmentChange: (value: string) => void;
  uniqueEnvironments: string[];
  showAdvancedFilters: boolean;
  onToggleAdvancedFilters: () => void;
  onExport: () => void;
  selectedCount: number;
  onReclassifySelected?: () => void;
  isReclassifying?: boolean;
}

export const AssetTableFilters: React.FC<AssetTableFiltersProps> = ({
  searchTerm,
  onSearchChange,
  selectedEnvironment,
  onEnvironmentChange,
  uniqueEnvironments,
  showAdvancedFilters,
  onToggleAdvancedFilters,
  onExport,
  selectedCount,
  onReclassifySelected,
  isReclassifying = false
}) => {
  return (
    <div className="space-y-4">
      <div className="flex gap-4">
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
          <Input
            placeholder="Search assets..."
            value={searchTerm}
            onChange={(e) => onSearchChange(e.target.value)}
            className="pl-10"
          />
        </div>
        <Select value={selectedEnvironment} onValueChange={onEnvironmentChange}>
          <SelectTrigger className="w-48">
            <SelectValue placeholder="Environment" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Environments</SelectItem>
            {uniqueEnvironments.map(env => (
              <SelectItem key={env} value={env}>{env}</SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Button 
          variant="outline" 
          onClick={onToggleAdvancedFilters}
        >
          <Filter className="h-4 w-4 mr-2" />
          Filters
        </Button>
        <Button 
          variant="outline" 
          onClick={onExport}
        >
          <Download className="h-4 w-4 mr-2" />
          Export
        </Button>
      </div>
      
      {selectedCount > 0 && (
        <div className="flex items-center gap-4">
          <div className="text-sm text-blue-600">
            {selectedCount} assets selected
          </div>
          {onReclassifySelected && (
            <Button 
              variant="outline" 
              size="sm"
              onClick={onReclassifySelected}
              disabled={isReclassifying}
              className="text-blue-600 border-blue-600 hover:bg-blue-50"
            >
              <RefreshCw className={`h-4 w-4 mr-2 ${isReclassifying ? 'animate-spin' : ''}`} />
              {isReclassifying ? 'Reclassifying...' : 'Reclassify Selected'}
            </Button>
          )}
        </div>
      )}
    </div>
  );
};