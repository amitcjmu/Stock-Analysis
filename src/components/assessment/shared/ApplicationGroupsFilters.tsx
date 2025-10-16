/**
 * ApplicationGroupsFilters - Search and sort controls for application groups
 *
 * Phase 4 Days 17-18: Assessment Architecture Enhancement
 *
 * Features:
 * - Search input with debouncing
 * - Sort by name, asset count, or readiness
 * - Visual indicators for active sort and direction
 */

import React from 'react';
import {
  Search,
  ArrowUpDown,
  Filter,
  CheckCircle,
} from 'lucide-react';

import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';

export type SortOption = 'name' | 'asset_count' | 'readiness';
export type SortDirection = 'asc' | 'desc';

export interface ApplicationGroupsFiltersProps {
  searchQuery: string;
  onSearchChange: (query: string) => void;
  sortBy: SortOption;
  sortDirection: SortDirection;
  onSortChange: (sortBy: SortOption) => void;
}

export const ApplicationGroupsFilters: React.FC<ApplicationGroupsFiltersProps> = ({
  searchQuery,
  onSearchChange,
  sortBy,
  sortDirection,
  onSortChange,
}) => {
  return (
    <div className="flex flex-col md:flex-row gap-4">
      <div className="flex-1">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            type="text"
            placeholder="Search applications..."
            value={searchQuery}
            onChange={(e) => onSearchChange(e.target.value)}
            className="pl-10"
            aria-label="Search applications"
          />
        </div>
      </div>
      <div className="flex gap-2">
        <Button
          variant={sortBy === 'name' ? 'default' : 'outline'}
          size="sm"
          onClick={() => onSortChange('name')}
          aria-label="Sort by name"
        >
          <ArrowUpDown className="h-4 w-4 mr-2" />
          Name {sortBy === 'name' && (sortDirection === 'asc' ? '↑' : '↓')}
        </Button>
        <Button
          variant={sortBy === 'asset_count' ? 'default' : 'outline'}
          size="sm"
          onClick={() => onSortChange('asset_count')}
          aria-label="Sort by asset count"
        >
          <Filter className="h-4 w-4 mr-2" />
          Count {sortBy === 'asset_count' && (sortDirection === 'asc' ? '↑' : '↓')}
        </Button>
        <Button
          variant={sortBy === 'readiness' ? 'default' : 'outline'}
          size="sm"
          onClick={() => onSortChange('readiness')}
          aria-label="Sort by readiness"
        >
          <CheckCircle className="h-4 w-4 mr-2" />
          Readiness {sortBy === 'readiness' && (sortDirection === 'asc' ? '↑' : '↓')}
        </Button>
      </div>
    </div>
  );
};

export default ApplicationGroupsFilters;
