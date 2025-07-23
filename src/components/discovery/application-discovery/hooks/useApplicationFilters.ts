import { useState } from 'react'
import { useMemo, useCallback } from 'react'

interface Application {
  id: string;
  name: string;
  confidence: number;
  validation_status: 'high_confidence' | 'medium_confidence' | 'needs_clarification';
  component_count: number;
  technology_stack: string[];
  environment: string;
  business_criticality: string;
  dependencies: {
    internal: string[];
    external: string[];
    infrastructure: string[];
  };
  components: Array<{
    name: string;
    asset_type: string;
    environment: string;
  }>;
  confidence_factors: {
    discovery_confidence: number;
    component_count: number;
    naming_clarity: number;
    dependency_clarity: number;
    technology_consistency: number;
  };
}

export interface FilterState {
  validation_status: string;
  environment: string;
  business_criticality: string;
  technology_stack: string;
  component_count_min: string;
  component_count_max: string;
  confidence_min: string;
}

const initialFilters: FilterState = {
  validation_status: 'all',
  environment: 'all',
  business_criticality: 'all',
  technology_stack: 'all',
  component_count_min: '',
  component_count_max: '',
  confidence_min: ''
};

export const useApplicationFilters = (applications: Application[]) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [filters, setFilters] = useState<FilterState>(initialFilters);
  const [showFilters, setShowFilters] = useState(false);

  const getFilteredApplications = useCallback(() => {
    if (!applications) return [];

    let filtered = applications;

    // Text search
    if (searchTerm.trim()) {
      const search = searchTerm.toLowerCase();
      filtered = filtered.filter(app => 
        app.name.toLowerCase().includes(search) ||
        app.technology_stack.some(tech => tech.toLowerCase().includes(search)) ||
        app.environment.toLowerCase().includes(search) ||
        app.business_criticality.toLowerCase().includes(search) ||
        app.components.some(comp => comp.name.toLowerCase().includes(search))
      );
    }

    // Validation status filter
    if (filters.validation_status !== 'all') {
      filtered = filtered.filter(app => app.validation_status === filters.validation_status);
    }

    // Environment filter
    if (filters.environment !== 'all') {
      filtered = filtered.filter(app => app.environment === filters.environment);
    }

    // Business criticality filter
    if (filters.business_criticality !== 'all') {
      filtered = filtered.filter(app => app.business_criticality === filters.business_criticality);
    }

    // Technology stack filter
    if (filters.technology_stack !== 'all') {
      filtered = filtered.filter(app => 
        app.technology_stack.some(tech => tech.toLowerCase().includes(filters.technology_stack.toLowerCase()))
      );
    }

    // Component count filters
    if (filters.component_count_min) {
      filtered = filtered.filter(app => app.component_count >= parseInt(filters.component_count_min));
    }
    if (filters.component_count_max) {
      filtered = filtered.filter(app => app.component_count <= parseInt(filters.component_count_max));
    }

    // Confidence filter
    if (filters.confidence_min) {
      filtered = filtered.filter(app => app.confidence >= parseFloat(filters.confidence_min) / 100);
    }

    return filtered;
  }, [applications, searchTerm, filters]);

  const clearFilters = useCallback(() => {
    setFilters(initialFilters);
    setSearchTerm('');
  }, []);

  // Get unique values for filter options
  const environmentOptions = useMemo(() => {
    if (!applications) return [];
    return [...new Set(applications.map(app => app.environment).filter(Boolean))];
  }, [applications]);

  const criticalityOptions = useMemo(() => {
    if (!applications) return [];
    return [...new Set(applications.map(app => app.business_criticality).filter(Boolean))];
  }, [applications]);

  const technologyOptions = useMemo(() => {
    if (!applications) return [];
    const allTechs = applications.flatMap(app => app.technology_stack);
    return [...new Set(allTechs)].filter(Boolean);
  }, [applications]);

  return {
    searchTerm,
    setSearchTerm,
    filters,
    setFilters,
    showFilters,
    setShowFilters,
    filteredApplications: getFilteredApplications(),
    clearFilters,
    filterOptions: {
      environments: environmentOptions,
      criticalities: criticalityOptions,
      technologies: technologyOptions
    }
  };
};