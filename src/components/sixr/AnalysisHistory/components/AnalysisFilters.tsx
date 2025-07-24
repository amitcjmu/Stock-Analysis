import React from 'react';
import { Input } from '../../../ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../../ui/select';
import { Button } from '../../../ui/button';
import { Filter } from 'lucide-react'
import { Search, X, Calendar } from 'lucide-react'
import type { FilterState } from '../types';
import { dateRangeOptions } from '../constants';

interface AnalysisFiltersProps {
  filters: FilterState;
  departments: string[];
  strategies: string[];
  onFilterChange: <K extends keyof FilterState>(key: K, value: FilterState[K]) => void;
  onClearFilters: () => void;
}

export const AnalysisFilters: React.FC<AnalysisFiltersProps> = ({
  filters,
  departments,
  strategies,
  onFilterChange,
  onClearFilters
}) => {
  const hasActiveFilters = filters.searchTerm || 
    filters.statusFilter !== 'all' || 
    filters.strategyFilter !== 'all' || 
    filters.departmentFilter !== 'all' || 
    filters.dateRange !== 'all';

  return (
    <div className="space-y-4 mb-6">
      {/* Search Bar */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
        <Input
          placeholder="Search applications, departments, or analysts..."
          value={filters.searchTerm}
          onChange={(e) => onFilterChange('searchTerm', e.target.value)}
          className="pl-10"
        />
      </div>

      {/* Filter Row */}
      <div className="flex flex-wrap gap-3">
        <Select 
          value={filters.statusFilter} 
          onValueChange={(value) => onFilterChange('statusFilter', value)}
        >
          <SelectTrigger className="w-40">
            <SelectValue placeholder="Status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Status</SelectItem>
            <SelectItem value="completed">Completed</SelectItem>
            <SelectItem value="in_progress">In Progress</SelectItem>
            <SelectItem value="failed">Failed</SelectItem>
            <SelectItem value="archived">Archived</SelectItem>
          </SelectContent>
        </Select>

        <Select 
          value={filters.strategyFilter} 
          onValueChange={(value) => onFilterChange('strategyFilter', value)}
        >
          <SelectTrigger className="w-40">
            <SelectValue placeholder="Strategy" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Strategies</SelectItem>
            {strategies.map(strategy => (
              <SelectItem key={strategy} value={strategy}>
                {strategy.charAt(0).toUpperCase() + strategy.slice(1)}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        <Select 
          value={filters.departmentFilter} 
          onValueChange={(value) => onFilterChange('departmentFilter', value)}
        >
          <SelectTrigger className="w-40">
            <SelectValue placeholder="Department" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Departments</SelectItem>
            {departments.map(dept => (
              <SelectItem key={dept} value={dept}>{dept}</SelectItem>
            ))}
          </SelectContent>
        </Select>

        <Select 
          value={filters.dateRange} 
          onValueChange={(value) => onFilterChange('dateRange', value)}
        >
          <SelectTrigger className="w-40">
            <Calendar className="h-4 w-4 mr-2" />
            <SelectValue placeholder="Date Range" />
          </SelectTrigger>
          <SelectContent>
            {dateRangeOptions.map(option => (
              <SelectItem key={option.value} value={option.value}>
                {option.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        {hasActiveFilters && (
          <Button
            variant="outline"
            size="sm"
            onClick={onClearFilters}
            className="ml-auto"
          >
            <X className="h-4 w-4 mr-1" />
            Clear Filters
          </Button>
        )}
      </div>
    </div>
  );
};