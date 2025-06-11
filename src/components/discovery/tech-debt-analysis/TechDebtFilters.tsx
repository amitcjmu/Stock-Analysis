import React from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { SlidersHorizontal } from 'lucide-react';

const COMPONENT_FILTERS = [
  { value: 'all', label: 'All Components' },
  { value: 'web', label: 'Web' },
  { value: 'app', label: 'Application' },
  { value: 'database', label: 'Database' },
  { value: 'os', label: 'Operating System' },
  { value: 'framework', label: 'Framework' },
];

const RISK_FILTERS = [
  { value: 'all', label: 'All Risks' },
  { value: 'critical', label: 'Critical' },
  { value: 'high', label: 'High' },
  { value: 'medium', label: 'Medium' },
  { value: 'low', label: 'Low' },
];

const STATUS_FILTERS = [
  { value: 'all', label: 'All Statuses' },
  { value: 'supported', label: 'Supported' },
  { value: 'extended', label: 'Extended Support' },
  { value: 'deprecated', label: 'Deprecated' },
  { value: 'end_of_life', label: 'End of Life' },
];

interface TechDebtFiltersProps {
  searchQuery: string;
  selectedComponent: string;
  selectedRisk: string;
  selectedStatus: string;
  onSearchChange: (value: string) => void;
  onFilterChange: (filter: string, value: string) => void;
  onResetFilters: () => void;
}

export const TechDebtFilters: React.FC<TechDebtFiltersProps> = ({
  searchQuery,
  selectedComponent,
  selectedRisk,
  selectedStatus,
  onSearchChange,
  onFilterChange,
  onResetFilters,
}) => {
  const hasActiveFilters = 
    searchQuery || 
    selectedComponent !== 'all' || 
    selectedRisk !== 'all' ||
    selectedStatus !== 'all';

  return (
    <div className="space-y-4">
      <div className="flex flex-col sm:flex-row gap-4">
        <div className="flex-1">
          <Input
            placeholder="Search technologies..."
            value={searchQuery}
            onChange={(e) => onSearchChange(e.target.value)}
            className="w-full"
          />
        </div>
        <div className="flex items-center gap-2">
          <Select
            value={selectedComponent}
            onValueChange={(value) => onFilterChange('component', value)}
          >
            <SelectTrigger className="w-[180px]">
              <SelectValue placeholder="Component" />
            </SelectTrigger>
            <SelectContent>
              {COMPONENT_FILTERS.map((filter) => (
                <SelectItem key={filter.value} value={filter.value}>
                  {filter.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>

          <Select
            value={selectedRisk}
            onValueChange={(value) => onFilterChange('risk', value)}
          >
            <SelectTrigger className="w-[140px]">
              <SelectValue placeholder="Risk Level" />
            </SelectTrigger>
            <SelectContent>
              {RISK_FILTERS.map((filter) => (
                <SelectItem key={filter.value} value={filter.value}>
                  {filter.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>

          <Select
            value={selectedStatus}
            onValueChange={(value) => onFilterChange('status', value)}
          >
            <SelectTrigger className="w-[160px]">
              <SelectValue placeholder="Support Status" />
            </SelectTrigger>
            <SelectContent>
              {STATUS_FILTERS.map((filter) => (
                <SelectItem key={filter.value} value={filter.value}>
                  {filter.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>

          {hasActiveFilters && (
            <Button
              variant="outline"
              size="sm"
              onClick={onResetFilters}
              className="flex items-center gap-1"
            >
              <SlidersHorizontal className="h-4 w-4" />
              Reset Filters
            </Button>
          )}
        </div>
      </div>

      {hasActiveFilters && (
        <div className="flex flex-wrap items-center gap-2 text-sm text-muted-foreground">
          <span className="font-medium">Active Filters:</span>
          {searchQuery && (
            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
              Search: {searchQuery}
            </span>
          )}
          {selectedComponent !== 'all' && (
            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-purple-100 text-purple-800">
              Component: {
                COMPONENT_FILTERS.find(f => f.value === selectedComponent)?.label || selectedComponent
              }
            </span>
          )}
          {selectedRisk !== 'all' && (
            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-orange-100 text-orange-800">
              Risk: {
                RISK_FILTERS.find(f => f.value === selectedRisk)?.label || selectedRisk
              }
            </span>
          )}
          {selectedStatus !== 'all' && (
            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
              Status: {
                STATUS_FILTERS.find(f => f.value === selectedStatus)?.label || selectedStatus
              }
            </span>
          )}
        </div>
      )}
    </div>
  );
};
