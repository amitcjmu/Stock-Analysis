/**
 * SearchFilters Component
 * Search and filter controls for applications
 */

import React from "react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Search } from "lucide-react";

interface SearchFiltersProps {
  searchTerm: string;
  setSearchTerm: (value: string) => void;
  environmentFilter: string;
  setEnvironmentFilter: (value: string) => void;
  criticalityFilter: string;
  setCriticalityFilter: (value: string) => void;
  environmentOptions: string[];
  criticalityOptions: string[];
  filteredCount: number;
  totalCount: number;
  onClearFilters: () => void;
}

export const SearchFilters: React.FC<SearchFiltersProps> = ({
  searchTerm,
  setSearchTerm,
  environmentFilter,
  setEnvironmentFilter,
  criticalityFilter,
  setCriticalityFilter,
  environmentOptions,
  criticalityOptions,
  filteredCount,
  totalCount,
  onClearFilters,
}) => {
  const hasFilters = searchTerm || environmentFilter || criticalityFilter;

  return (
    <div className="space-y-4 pb-4 border-b">
      <div className="flex flex-col sm:flex-row gap-4">
        {/* Search */}
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
          <Input
            type="text"
            placeholder="Search assets..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-10"
          />
        </div>

        {/* Environment Filter */}
        <div className="sm:w-48">
          <select
            value={environmentFilter}
            onChange={(e) => setEnvironmentFilter(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="">All Environments</option>
            {environmentOptions.map((env) => (
              <option key={env} value={env}>
                {env}
              </option>
            ))}
          </select>
        </div>

        {/* Criticality Filter */}
        <div className="sm:w-48">
          <select
            value={criticalityFilter}
            onChange={(e) => setCriticalityFilter(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="">All Criticalities</option>
            {criticalityOptions.map((crit) => (
              <option key={crit} value={crit}>
                {crit}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Results Summary */}
      <div className="flex justify-between items-center text-sm text-gray-600">
        <span>
          Showing {filteredCount} of {totalCount} applications
          {hasFilters && " (filtered)"}
        </span>
        {hasFilters && (
          <Button variant="ghost" size="sm" onClick={onClearFilters}>
            Clear Filters
          </Button>
        )}
      </div>
    </div>
  );
};
