import { useState } from 'react'
import { useMemo } from 'react'
import type { FilterState } from '../types'
import type { AnalysisHistoryItem } from '../types'
import { matchesDateRange } from '../utils/dateUtils';

export const useAnalysisFilters = (analyses: AnalysisHistoryItem[]) => {
  const [filters, setFilters] = useState<FilterState>({
    searchTerm: '',
    statusFilter: 'all',
    strategyFilter: 'all',
    departmentFilter: 'all',
    dateRange: 'all'
  });

  const filteredAnalyses = useMemo(() => {
    return analyses.filter(analysis => {
      const matchesSearch = !filters.searchTerm ||
        analysis.application_name.toLowerCase().includes(filters.searchTerm.toLowerCase()) ||
        analysis.department.toLowerCase().includes(filters.searchTerm.toLowerCase()) ||
        analysis.analyst.toLowerCase().includes(filters.searchTerm.toLowerCase());

      const matchesStatus = filters.statusFilter === 'all' || analysis.status === filters.statusFilter;
      const matchesStrategy = filters.strategyFilter === 'all' || analysis.recommended_strategy === filters.strategyFilter;
      const matchesDepartment = filters.departmentFilter === 'all' || analysis.department === filters.departmentFilter;
      const matchesDate = matchesDateRange(analysis.analysis_date, filters.dateRange);

      return matchesSearch && matchesStatus && matchesStrategy && matchesDepartment && matchesDate;
    });
  }, [analyses, filters]);

  const departments = useMemo(() =>
    [...new Set(analyses.map(a => a.department))].sort(),
    [analyses]
  );

  const strategies = useMemo(() =>
    [...new Set(analyses.map(a => a.recommended_strategy))].sort(),
    [analyses]
  );

  const updateFilter = <K extends keyof FilterState>(key: K, value: FilterState[K]) => {
    setFilters(prev => ({ ...prev, [key]: value }));
  };

  const clearFilters = () => {
    setFilters({
      searchTerm: '',
      statusFilter: 'all',
      strategyFilter: 'all',
      departmentFilter: 'all',
      dateRange: 'all'
    });
  };

  return {
    filters,
    filteredAnalyses,
    departments,
    strategies,
    updateFilter,
    clearFilters
  };
};
