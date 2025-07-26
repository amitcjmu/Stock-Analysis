/**
 * Custom hook for Application Filters functionality
 * Extracted from ApplicationSelector.tsx for modularization
 */

import { useState } from 'react'
import { useMemo } from 'react'
import type { FilteredApplicationsResult } from '../types/ApplicationSelectorTypes'
import type { Application, ApplicationFilters } from '../types/ApplicationSelectorTypes'

interface UseApplicationFiltersResult extends FilteredApplicationsResult {
  filters: ApplicationFilters;
  setFilters: (filters: Partial<ApplicationFilters>) => void;
  clearFilters: () => void;
  showAdvancedFilters: boolean;
  setShowAdvancedFilters: (show: boolean) => void;
}

export const useApplicationFilters = (applications: Application[]): UseApplicationFiltersResult => {
  const [filters, setFiltersState] = useState<ApplicationFilters>({
    searchTerm: '',
    departmentFilter: 'all',
    criticalityFilter: 'all',
    statusFilter: 'all',
    technologyFilter: 'all'
  });

  const [showAdvancedFilters, setShowAdvancedFilters] = useState(false);

  const setFilters = (newFilters: Partial<ApplicationFilters>): unknown => {
    setFiltersState(prev => ({ ...prev, ...newFilters }));
  };

  const clearFilters = (): unknown => {
    setFiltersState({
      searchTerm: '',
      departmentFilter: 'all',
      criticalityFilter: 'all',
      statusFilter: 'all',
      technologyFilter: 'all'
    });
  };

  // Get unique filter values
  const departments = useMemo(() =>
    [...new Set(applications.map(app => app.department).filter(Boolean))].sort(),
    [applications]
  );

  const technologies = useMemo(() =>
    [...new Set(applications.flatMap(app => app.technology_stack || []))].sort(),
    [applications]
  );

  // Filter applications
  const filteredApplications = useMemo(() => {
    return applications.filter(app => {
      const matchesSearch = !filters.searchTerm ||
        app.name.toLowerCase().includes(filters.searchTerm.toLowerCase()) ||
        app.description?.toLowerCase().includes(filters.searchTerm.toLowerCase()) ||
        (app.technology_stack || []).some(tech => tech.toLowerCase().includes(filters.searchTerm.toLowerCase()));

      const matchesDepartment = filters.departmentFilter === 'all' || app.department === filters.departmentFilter;
      const matchesCriticality = filters.criticalityFilter === 'all' || app.criticality === filters.criticalityFilter;
      const matchesStatus = filters.statusFilter === 'all' || app.analysis_status === filters.statusFilter;
      const matchesTechnology = filters.technologyFilter === 'all' ||
        (app.technology_stack || []).includes(filters.technologyFilter);

      return matchesSearch && matchesDepartment && matchesCriticality &&
             matchesStatus && matchesTechnology;
    });
  }, [applications, filters]);

  return {
    filteredApplications,
    departments,
    technologies,
    filters,
    setFilters,
    clearFilters,
    showAdvancedFilters,
    setShowAdvancedFilters
  };
};
