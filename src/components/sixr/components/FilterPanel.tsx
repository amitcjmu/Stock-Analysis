/**
 * FilterPanel Component
 * Extracted from ApplicationSelector.tsx for modularization
 */

import React from 'react';
import { Filter } from 'lucide-react'
import { Search } from 'lucide-react'
import { Input } from '../../ui/input';
import { Button } from '../../ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../ui/select';
import type { FilterPanelProps } from '../types/ApplicationSelectorTypes';

export const FilterPanel: React.FC<FilterPanelProps> = ({
  filters,
  onFiltersChange,
  departments,
  technologies,
  showAdvanced,
  onToggleAdvanced,
  onClearFilters
}) => {
  return (
    <div className="space-y-4">
      <div className="flex space-x-4">
        <div className="flex-1">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
            <Input
              placeholder="Search applications..."
              value={filters.searchTerm}
              onChange={(e) => onFiltersChange({ searchTerm: e.target.value })}
              className="pl-10"
            />
          </div>
        </div>
        <Select value={filters.departmentFilter} onValueChange={(value) => onFiltersChange({ departmentFilter: value })}>
          <SelectTrigger className="w-48">
            <SelectValue placeholder="Department" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Departments</SelectItem>
            {departments.map(dept => (
              <SelectItem key={dept} value={dept}>{dept}</SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {showAdvanced && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 p-4 bg-gray-50 rounded-lg">
          <Select value={filters.criticalityFilter} onValueChange={(value) => onFiltersChange({ criticalityFilter: value })}>
            <SelectTrigger>
              <SelectValue placeholder="Criticality" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Criticality</SelectItem>
              <SelectItem value="low">Low</SelectItem>
              <SelectItem value="medium">Medium</SelectItem>
              <SelectItem value="high">High</SelectItem>
              <SelectItem value="critical">Critical</SelectItem>
            </SelectContent>
          </Select>

          <Select value={filters.statusFilter} onValueChange={(value) => onFiltersChange({ statusFilter: value })}>
            <SelectTrigger>
              <SelectValue placeholder="Analysis Status" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Status</SelectItem>
              <SelectItem value="not_analyzed">Not Analyzed</SelectItem>
              <SelectItem value="in_progress">In Progress</SelectItem>
              <SelectItem value="completed">Completed</SelectItem>
              <SelectItem value="failed">Failed</SelectItem>
            </SelectContent>
          </Select>

          <Select value={filters.technologyFilter} onValueChange={(value) => onFiltersChange({ technologyFilter: value })}>
            <SelectTrigger>
              <SelectValue placeholder="Technology" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Technologies</SelectItem>
              {technologies.map(tech => (
                <SelectItem key={tech} value={tech}>{tech}</SelectItem>
              ))}
            </SelectContent>
          </Select>

          <div className="md:col-span-3 flex justify-end">
            <Button variant="outline" size="sm" onClick={onClearFilters}>
              Clear Filters
            </Button>
          </div>
        </div>
      )}
      
      <div className="flex justify-end">
        <Button
          variant="outline"
          size="sm"
          onClick={() => onToggleAdvanced(!showAdvanced)}
        >
          <Filter className="h-4 w-4 mr-1" />
          {showAdvanced ? 'Hide' : 'Show'} Advanced Filters
        </Button>
      </div>
    </div>
  );
};