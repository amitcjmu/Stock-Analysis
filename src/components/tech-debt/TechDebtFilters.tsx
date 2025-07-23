import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Filter as FilterIcon, Search, X } from 'lucide-react'
import type { TechDebtCategory, RiskLevel, StatusFilter } from '@/types/tech-debt';

interface TechDebtFiltersProps {
  searchQuery: string;
  selectedCategory: TechDebtCategory;
  selectedRisk: RiskLevel;
  selectedStatus: StatusFilter;
  hasActiveFilters: boolean;
  onSearchChange: (value: string) => void;
  onCategoryChange: (value: TechDebtCategory) => void;
  onRiskChange: (value: RiskLevel) => void;
  onStatusChange: (value: StatusFilter) => void;
  onResetFilters: () => void;
}

export function TechDebtFilters({
  searchQuery,
  selectedCategory,
  selectedRisk,
  selectedStatus,
  hasActiveFilters,
  onSearchChange,
  onCategoryChange,
  onRiskChange,
  onStatusChange,
  onResetFilters,
}: TechDebtFiltersProps) {
  return (
    <div className="flex flex-col space-y-4 md:flex-row md:items-center md:justify-between md:space-y-0 md:space-x-4">
      <div className="relative flex-1">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
        <Input
          type="search"
          placeholder="Search by name or description..."
          className="pl-10"
          value={searchQuery}
          onChange={(e) => onSearchChange(e.target.value)}
        />
      </div>

      <div className="flex items-center space-x-2">
        <Select
          value={selectedCategory}
          onValueChange={(value: TechDebtCategory) => onCategoryChange(value)}
        >
          <SelectTrigger className="w-[180px]">
            <FilterIcon className="mr-2 h-4 w-4" />
            <SelectValue placeholder="Category" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Categories</SelectItem>
            <SelectItem value="security">Security</SelectItem>
            <SelectItem value="performance">Performance</SelectItem>
            <SelectItem value="maintainability">Maintainability</SelectItem>
            <SelectItem value="compliance">Compliance</SelectItem>
          </SelectContent>
        </Select>

        <Select
          value={selectedRisk}
          onValueChange={(value: RiskLevel) => onRiskChange(value)}
        >
          <SelectTrigger className="w-[150px]">
            <FilterIcon className="mr-2 h-4 w-4" />
            <SelectValue placeholder="Risk Level" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Risks</SelectItem>
            <SelectItem value="critical">Critical</SelectItem>
            <SelectItem value="high">High</SelectItem>
            <SelectItem value="medium">Medium</SelectItem>
            <SelectItem value="low">Low</SelectItem>
          </SelectContent>
        </Select>

        <Select
          value={selectedStatus}
          onValueChange={(value: StatusFilter) => onStatusChange(value)}
        >
          <SelectTrigger className="w-[150px]">
            <FilterIcon className="mr-2 h-4 w-4" />
            <SelectValue placeholder="Status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Statuses</SelectItem>
            <SelectItem value="active">Active</SelectItem>
            <SelectItem value="mitigated">Mitigated</SelectItem>
            <SelectItem value="planned">Planned</SelectItem>
          </SelectContent>
        </Select>

        {hasActiveFilters && (
          <Button variant="ghost" onClick={onResetFilters} className="h-10 px-3">
            <X className="mr-1 h-4 w-4" />
            Reset
          </Button>
        )}
      </div>
    </div>
  );
}
