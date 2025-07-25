import React from 'react';
import { Search } from 'lucide-react';
import { Input } from '../../ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../ui/select';
import { Switch } from '../../ui/switch';
import { Label } from '../../ui/label';

interface DependencyControlsProps {
  showGraph: boolean;
  setShowGraph: (show: boolean) => void;
  selectedFilter: string;
  setSelectedFilter: (filter: string) => void;
  selectedStrength: string;
  setSelectedStrength: (strength: string) => void;
  searchTerm: string;
  handleSearchChange: (value: string) => void;
  isLoading: boolean;
}

export const DependencyControls: React.FC<DependencyControlsProps> = ({
  showGraph,
  setShowGraph,
  selectedFilter,
  setSelectedFilter,
  selectedStrength,
  setSelectedStrength,
  searchTerm,
  handleSearchChange,
  isLoading
}) => {
  return (
    <div className="space-y-4">
      <div className="flex flex-wrap gap-4">
        {/* Search */}
        <div className="flex-1 min-w-[200px]">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
            <Input
              type="text"
              placeholder="Search dependencies..."
              value={searchTerm}
              onChange={(e) => handleSearchChange(e.target.value)}
              className="pl-10"
              disabled={isLoading}
            />
          </div>
        </div>

        {/* Filters */}
        <div className="flex items-center space-x-4">
          <Select
            value={selectedFilter}
            onValueChange={setSelectedFilter}
            disabled={isLoading}
          >
            <SelectTrigger className="w-[180px]">
              <SelectValue placeholder="Filter by type" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Types</SelectItem>
              <SelectItem value="application">Applications</SelectItem>
              <SelectItem value="server">Servers</SelectItem>
            </SelectContent>
          </Select>

          <Select
            value={selectedStrength}
            onValueChange={setSelectedStrength}
            disabled={isLoading}
          >
            <SelectTrigger className="w-[180px]">
              <SelectValue placeholder="Filter by strength" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Strengths</SelectItem>
              <SelectItem value="critical">Critical</SelectItem>
              <SelectItem value="high">High</SelectItem>
              <SelectItem value="medium">Medium</SelectItem>
              <SelectItem value="low">Low</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* View Toggle */}
        <div className="flex items-center space-x-2">
          <Switch
            id="show-graph"
            checked={showGraph}
            onCheckedChange={setShowGraph}
            disabled={isLoading}
          />
          <Label htmlFor="show-graph">Show Graph View</Label>
        </div>
      </div>
    </div>
  );
};
