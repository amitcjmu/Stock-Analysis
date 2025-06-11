import React from 'react';
import { Search, Filter, X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { FilterBarProps } from '../../types';

export const FilterBar: React.FC<FilterBarProps> = ({
  filters,
  onFilterChange,
  onReset,
  availableDepartments = [],
  availableEnvironments = [],
  availableCriticalities = ['low', 'medium', 'high', 'critical']
}) => {
  const hasActiveFilters = Object.entries(filters).some(
    ([key, value]) => key !== 'page' && key !== 'page_size' && value && value !== 'all'
  );

  const handleSearch = (e: React.ChangeEvent<HTMLInputElement>) => {
    onFilterChange({ search: e.target.value, page: 1 });
  };

  const handleSelectChange = (key: string) => (value: string) => {
    onFilterChange({ [key]: value, page: 1 });
  };

  return (
    <div className="bg-white p-4 rounded-lg shadow mb-6">
      <div className="flex flex-col sm:flex-row gap-4">
        {/* Search Input */}
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
          <Input
            type="text"
            placeholder="Search assets..."
            className="pl-10"
            value={filters.search || ''}
            onChange={handleSearch}
          />
        </div>

        {/* Environment Filter */}
        <Select
          value={filters.environment || 'all'}
          onValueChange={handleSelectChange('environment')}
        >
          <SelectTrigger className="w-[180px]">
            <Filter className="mr-2 h-4 w-4 text-gray-400" />
            <SelectValue placeholder="Environment" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Environments</SelectItem>
            {availableEnvironments.map((env) => (
              <SelectItem key={env} value={env}>
                {env}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        {/* Department Filter */}
        <Select
          value={filters.department || 'all'}
          onValueChange={handleSelectChange('department')}
        >
          <SelectTrigger className="w-[180px]">
            <Filter className="mr-2 h-4 w-4 text-gray-400" />
            <SelectValue placeholder="Department" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Departments</SelectItem>
            {availableDepartments.map((dept) => (
              <SelectItem key={dept} value={dept}>
                {dept}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        {/* Criticality Filter */}
        <Select
          value={filters.criticality || 'all'}
          onValueChange={handleSelectChange('criticality')}
        >
          <SelectTrigger className="w-[180px]">
            <Filter className="mr-2 h-4 w-4 text-gray-400" />
            <SelectValue placeholder="Criticality" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Criticalities</SelectItem>
            {availableCriticalities.map((crit) => (
              <SelectItem key={crit} value={crit}>
                {crit.charAt(0).toUpperCase() + crit.slice(1)}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        {/* Reset Button */}
        {hasActiveFilters && (
          <Button
            variant="ghost"
            onClick={onReset}
            className="flex items-center gap-2"
          >
            <X className="h-4 w-4" />
            Reset
          </Button>
        )}
      </div>
    </div>
  );
};
