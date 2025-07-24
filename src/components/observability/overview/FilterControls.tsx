/**
 * Filter controls component extracted from ResponsiveAgentListOverview
 * Provides search, status filter, and sorting controls
 */

import React from 'react';
import { Search, Grid, List } from 'lucide-react';
import { Card, CardContent } from '../../ui/card';
import { Input } from '../../ui/input';
import { Button } from '../../ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../ui/select';
import { cn } from '../../../lib/utils';

interface FilterControlsProps {
  searchQuery?: string;
  statusFilter?: string;
  sortBy?: string;
  viewMode: 'grid' | 'list';
  isMobile?: boolean;
  onSearchChange: (query: string) => void;
  onStatusChange: (status: string) => void;
  onSortChange: (sort: string) => void;
  onViewModeChange: (mode: 'grid' | 'list') => void;
}

export const FilterControls: React.FC<FilterControlsProps> = ({
  searchQuery = '',
  statusFilter = 'all',
  sortBy = 'name',
  viewMode,
  isMobile = false,
  onSearchChange,
  onStatusChange,
  onSortChange,
  onViewModeChange
}) => {
  return (
    <Card>
      <CardContent className="py-4">
        <div className={cn(
          'grid gap-4',
          isMobile ? 'grid-cols-1' : 'grid-cols-1 md:grid-cols-4'
        )}>
          {/* Search */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
            <Input
              placeholder="Search agents..."
              value={searchQuery}
              onChange={(e) => onSearchChange(e.target.value)}
              className="pl-10"
            />
          </div>

          {/* Status Filter */}
          <Select
            value={statusFilter}
            onValueChange={onStatusChange}
          >
            <SelectTrigger>
              <SelectValue placeholder="Filter by status" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Status</SelectItem>
              <SelectItem value="active">Active</SelectItem>
              <SelectItem value="idle">Idle</SelectItem>
              <SelectItem value="error">Error</SelectItem>
              <SelectItem value="offline">Offline</SelectItem>
            </SelectContent>
          </Select>

          {/* Sort By */}
          <Select
            value={sortBy}
            onValueChange={onSortChange}
          >
            <SelectTrigger>
              <SelectValue placeholder="Sort by" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="name">Name</SelectItem>
              <SelectItem value="successRate">Success Rate</SelectItem>
              <SelectItem value="totalTasks">Total Tasks</SelectItem>
              <SelectItem value="lastActive">Last Active</SelectItem>
            </SelectContent>
          </Select>

          {/* View Mode */}
          {!isMobile && (
            <div className="flex items-center space-x-2">
              <Button
                variant={viewMode === 'grid' ? 'default' : 'outline'}
                size="sm"
                onClick={() => onViewModeChange('grid')}
                className="flex-1"
              >
                <Grid className="h-4 w-4" />
              </Button>
              <Button
                variant={viewMode === 'list' ? 'default' : 'outline'}
                size="sm"
                onClick={() => onViewModeChange('list')}
                className="flex-1"
              >
                <List className="h-4 w-4" />
              </Button>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
};