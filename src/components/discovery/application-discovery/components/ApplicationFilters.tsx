import React from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Label } from '@/components/ui/label';
import { X, SlidersHorizontal } from 'lucide-react';

export interface FilterState {
  validation_status: string;
  environment: string;
  business_criticality: string;
  technology_stack: string;
  component_count_min: string;
  component_count_max: string;
  confidence_min: string;
}

interface ApplicationFiltersProps {
  filters: FilterState;
  onFilterChange: (filters: FilterState) => void;
  showFilters: boolean;
  onToggleFilters: () => void;
  onClearFilters: () => void;
  environmentOptions: string[];
  criticalityOptions: string[];
  technologyOptions: string[];
}

export const ApplicationFilters: React.FC<ApplicationFiltersProps> = ({
  filters,
  onFilterChange,
  showFilters,
  onToggleFilters,
  onClearFilters,
  environmentOptions,
  criticalityOptions,
  technologyOptions
}) => {
  const handleFilterChange = (field: keyof FilterState, value: string) => {
    onFilterChange({
      ...filters,
      [field]: value
    });
  };

  const hasActiveFilters = () => {
    return Object.entries(filters).some(([key, value]) => {
      if (key.includes('_min') || key.includes('_max')) return value !== '';
      return value !== 'all';
    });
  };

  return (
    <div>
      <Button
        onClick={onToggleFilters}
        variant="outline"
        size="sm"
        className={`${hasActiveFilters() ? 'border-blue-500' : ''}`}
      >
        <SlidersHorizontal className="h-4 w-4 mr-2" />
        Filters {hasActiveFilters() && '•'}
      </Button>

      {showFilters && (
        <div className="mt-4 p-4 border rounded-lg bg-gray-50">
          <div className="flex justify-between items-center mb-4">
            <h3 className="font-semibold">Filter Applications</h3>
            <Button
              onClick={onClearFilters}
              variant="ghost"
              size="sm"
              disabled={!hasActiveFilters()}
            >
              <X className="h-4 w-4 mr-1" />
              Clear All
            </Button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Validation Status */}
            <div>
              <Label htmlFor="validation-status">Validation Status</Label>
              <Select
                value={filters.validation_status}
                onValueChange={(value) => handleFilterChange('validation_status', value)}
              >
                <SelectTrigger id="validation-status">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Status</SelectItem>
                  <SelectItem value="high_confidence">High Confidence</SelectItem>
                  <SelectItem value="medium_confidence">Medium Confidence</SelectItem>
                  <SelectItem value="needs_clarification">Needs Clarification</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Environment */}
            <div>
              <Label htmlFor="environment">Environment</Label>
              <Select
                value={filters.environment}
                onValueChange={(value) => handleFilterChange('environment', value)}
              >
                <SelectTrigger id="environment">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Environments</SelectItem>
                  {environmentOptions.map(env => (
                    <SelectItem key={env} value={env}>{env}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Business Criticality */}
            <div>
              <Label htmlFor="criticality">Business Criticality</Label>
              <Select
                value={filters.business_criticality}
                onValueChange={(value) => handleFilterChange('business_criticality', value)}
              >
                <SelectTrigger id="criticality">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Levels</SelectItem>
                  {criticalityOptions.map(level => (
                    <SelectItem key={level} value={level}>{level}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Technology Stack */}
            <div>
              <Label htmlFor="technology">Technology Stack</Label>
              <Select
                value={filters.technology_stack}
                onValueChange={(value) => handleFilterChange('technology_stack', value)}
              >
                <SelectTrigger id="technology">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Technologies</SelectItem>
                  {technologyOptions.map(tech => (
                    <SelectItem key={tech} value={tech}>{tech}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Component Count Range */}
            <div>
              <Label>Component Count</Label>
              <div className="flex gap-2">
                <Input
                  type="number"
                  placeholder="Min"
                  value={filters.component_count_min}
                  onChange={(e) => handleFilterChange('component_count_min', e.target.value)}
                  className="w-24"
                />
                <span className="self-center">-</span>
                <Input
                  type="number"
                  placeholder="Max"
                  value={filters.component_count_max}
                  onChange={(e) => handleFilterChange('component_count_max', e.target.value)}
                  className="w-24"
                />
              </div>
            </div>

            {/* Confidence Threshold */}
            <div>
              <Label htmlFor="confidence">Min Confidence (%)</Label>
              <Input
                id="confidence"
                type="number"
                placeholder="0-100"
                value={filters.confidence_min}
                onChange={(e) => handleFilterChange('confidence_min', e.target.value)}
                min="0"
                max="100"
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
};