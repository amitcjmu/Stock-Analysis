import React, { useState, useMemo, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue
} from '@/components/ui/select';
import {
  Search,
  Filter,
  ArrowUpDown,
  CheckCircle,
  AlertCircle,
  Download,
  RefreshCw,
  LayoutGrid,
  List,
  X
} from 'lucide-react';
import { cn } from '@/lib/utils';
import {
  RecommendationCard,
  SIX_R_STRATEGIES,
  EFFORT_LEVELS,
  COST_RANGES,
  type SixRStrategyType,
  type EffortLevel,
  type CostRange,
  type AlternativeStrategy,
  type RecommendationCardProps
} from './RecommendationCard';

/**
 * Recommendation data structure
 */
export interface Recommendation {
  application_id: string;
  application_name: string;
  application_version?: string;
  recommended_strategy: SixRStrategyType;
  confidence: number;
  effort?: EffortLevel;
  cost_range?: CostRange;
  rationale: string;
  risk_factors?: string[];
  alternatives?: AlternativeStrategy[];
}

/**
 * Sort options
 */
type SortField = 'confidence' | 'effort' | 'cost' | 'name' | 'strategy';
type SortOrder = 'asc' | 'desc';

/**
 * Filter state
 */
interface FilterState {
  search: string;
  strategies: SixRStrategyType[];
  minConfidence: number | null;
  effort: EffortLevel[];
  costRange: CostRange[];
}

/**
 * TreatmentRecommendations Props
 */
export interface TreatmentRecommendationsProps {
  recommendations: Recommendation[];
  acceptedIds?: Set<string>;
  isLoading?: boolean;
  error?: string;
  onAccept?: (applicationId: string) => void;
  onAcceptAll?: () => void;
  onReviewAlternatives?: (applicationId: string) => void;
  onRequestSME?: (applicationId: string) => void;
  onExport?: (format: 'pdf' | 'excel' | 'json') => void;
  onRefresh?: () => void;
  className?: string;
}

/**
 * Effort level numeric values for sorting
 */
const EFFORT_SORT_VALUES: Record<EffortLevel, number> = {
  S: 1,
  M: 2,
  L: 3,
  XL: 4
};

/**
 * Cost range numeric values for sorting
 */
const COST_SORT_VALUES: Record<CostRange, number> = {
  low: 1,
  medium: 2,
  high: 3,
  very_high: 4
};

/**
 * TreatmentRecommendations Component
 *
 * Displays a list of 6R treatment recommendations with:
 * - Search functionality
 * - Multi-select filtering by strategy, effort, cost
 * - Sorting by confidence, effort, cost, name
 * - Grid/List view toggle
 * - Bulk accept functionality
 * - Export options
 */
export const TreatmentRecommendations: React.FC<TreatmentRecommendationsProps> = ({
  recommendations,
  acceptedIds = new Set(),
  isLoading = false,
  error,
  onAccept,
  onAcceptAll,
  onReviewAlternatives,
  onRequestSME,
  onExport,
  onRefresh,
  className
}) => {
  // View state
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const [expandedCards, setExpandedCards] = useState<Set<string>>(new Set());

  // Filter state
  const [filters, setFilters] = useState<FilterState>({
    search: '',
    strategies: [],
    minConfidence: null,
    effort: [],
    costRange: []
  });

  // Sort state
  const [sortField, setSortField] = useState<SortField>('confidence');
  const [sortOrder, setSortOrder] = useState<SortOrder>('desc');

  // Show/hide filter panel
  const [showFilters, setShowFilters] = useState(false);

  // Handle filter changes
  const updateFilter = useCallback(<K extends keyof FilterState>(
    key: K,
    value: FilterState[K]
  ) => {
    setFilters(prev => ({ ...prev, [key]: value }));
  }, []);

  // Toggle strategy filter
  const toggleStrategyFilter = useCallback((strategy: SixRStrategyType) => {
    setFilters(prev => ({
      ...prev,
      strategies: prev.strategies.includes(strategy)
        ? prev.strategies.filter(s => s !== strategy)
        : [...prev.strategies, strategy]
    }));
  }, []);

  // Toggle effort filter
  const toggleEffortFilter = useCallback((effort: EffortLevel) => {
    setFilters(prev => ({
      ...prev,
      effort: prev.effort.includes(effort)
        ? prev.effort.filter(e => e !== effort)
        : [...prev.effort, effort]
    }));
  }, []);

  // Toggle cost range filter
  const toggleCostFilter = useCallback((cost: CostRange) => {
    setFilters(prev => ({
      ...prev,
      costRange: prev.costRange.includes(cost)
        ? prev.costRange.filter(c => c !== cost)
        : [...prev.costRange, cost]
    }));
  }, []);

  // Clear all filters
  const clearFilters = useCallback(() => {
    setFilters({
      search: '',
      strategies: [],
      minConfidence: null,
      effort: [],
      costRange: []
    });
  }, []);

  // Toggle card expansion
  const toggleCardExpand = useCallback((appId: string) => {
    setExpandedCards(prev => {
      const next = new Set(prev);
      if (next.has(appId)) {
        next.delete(appId);
      } else {
        next.add(appId);
      }
      return next;
    });
  }, []);

  // Filter and sort recommendations
  const filteredAndSortedRecommendations = useMemo(() => {
    let result = [...recommendations];

    // Apply search filter
    if (filters.search) {
      const searchLower = filters.search.toLowerCase();
      result = result.filter(rec =>
        rec.application_name.toLowerCase().includes(searchLower) ||
        rec.rationale.toLowerCase().includes(searchLower)
      );
    }

    // Apply strategy filter
    if (filters.strategies.length > 0) {
      result = result.filter(rec =>
        filters.strategies.includes(rec.recommended_strategy)
      );
    }

    // Apply minimum confidence filter
    if (filters.minConfidence !== null) {
      const minConf = filters.minConfidence;
      result = result.filter(rec => rec.confidence >= minConf);
    }

    // Apply effort filter
    if (filters.effort.length > 0) {
      result = result.filter(rec =>
        rec.effort && filters.effort.includes(rec.effort)
      );
    }

    // Apply cost range filter
    if (filters.costRange.length > 0) {
      result = result.filter(rec =>
        rec.cost_range && filters.costRange.includes(rec.cost_range)
      );
    }

    // Apply sorting
    result.sort((a, b) => {
      let comparison = 0;

      switch (sortField) {
        case 'confidence':
          comparison = a.confidence - b.confidence;
          break;
        case 'effort': {
          const effortA = a.effort ? EFFORT_SORT_VALUES[a.effort] : 0;
          const effortB = b.effort ? EFFORT_SORT_VALUES[b.effort] : 0;
          comparison = effortA - effortB;
          break;
        }
        case 'cost': {
          const costA = a.cost_range ? COST_SORT_VALUES[a.cost_range] : 0;
          const costB = b.cost_range ? COST_SORT_VALUES[b.cost_range] : 0;
          comparison = costA - costB;
          break;
        }
        case 'name':
          comparison = a.application_name.localeCompare(b.application_name);
          break;
        case 'strategy':
          comparison = a.recommended_strategy.localeCompare(b.recommended_strategy);
          break;
      }

      return sortOrder === 'asc' ? comparison : -comparison;
    });

    return result;
  }, [recommendations, filters, sortField, sortOrder]);

  // Count accepted vs pending
  const acceptedCount = recommendations.filter(r => acceptedIds.has(r.application_id)).length;
  const pendingCount = recommendations.length - acceptedCount;

  // Check if any filters are active
  const hasActiveFilters = filters.search ||
    filters.strategies.length > 0 ||
    filters.minConfidence !== null ||
    filters.effort.length > 0 ||
    filters.costRange.length > 0;

  // Loading state
  if (isLoading) {
    return (
      <Card className={className}>
        <CardContent className="p-12">
          <div className="flex flex-col items-center justify-center space-y-4">
            <RefreshCw className="h-8 w-8 animate-spin text-blue-500" />
            <p className="text-gray-600">Loading recommendations...</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  // Error state
  if (error) {
    return (
      <Card className={cn('border-red-200', className)}>
        <CardContent className="p-12">
          <div className="flex flex-col items-center justify-center space-y-4">
            <AlertCircle className="h-8 w-8 text-red-500" />
            <p className="text-red-600">{error}</p>
            {onRefresh && (
              <Button variant="outline" onClick={onRefresh}>
                <RefreshCw className="h-4 w-4 mr-2" />
                Retry
              </Button>
            )}
          </div>
        </CardContent>
      </Card>
    );
  }

  // Empty state
  if (recommendations.length === 0) {
    return (
      <Card className={className}>
        <CardContent className="p-12">
          <div className="flex flex-col items-center justify-center space-y-4">
            <AlertCircle className="h-8 w-8 text-gray-400" />
            <p className="text-gray-600">No recommendations available yet.</p>
            <p className="text-sm text-gray-500">
              Complete the assessment flow to generate 6R recommendations.
            </p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className={cn('space-y-4', className)}>
      {/* Header with stats */}
      <Card>
        <CardHeader className="pb-3">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <div>
              <CardTitle className="text-xl">Treatment Recommendations</CardTitle>
              <CardDescription>
                Review and accept migration strategy recommendations for your applications
              </CardDescription>
            </div>
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2">
                <Badge variant="outline" className="bg-green-50 text-green-700">
                  <CheckCircle className="h-3 w-3 mr-1" />
                  {acceptedCount} Accepted
                </Badge>
                <Badge variant="outline" className="bg-yellow-50 text-yellow-700">
                  {pendingCount} Pending
                </Badge>
              </div>
            </div>
          </div>
        </CardHeader>

        <CardContent className="space-y-4">
          {/* Toolbar */}
          <div className="flex flex-col sm:flex-row gap-3">
            {/* Search */}
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
              <Input
                placeholder="Search applications..."
                value={filters.search}
                onChange={(e) => updateFilter('search', e.target.value)}
                className="pl-9"
              />
            </div>

            {/* Sort */}
            <div className="flex items-center gap-2">
              <Select
                value={sortField}
                onValueChange={(value) => setSortField(value as SortField)}
              >
                <SelectTrigger className="w-[140px]">
                  <SelectValue placeholder="Sort by" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="confidence">Confidence</SelectItem>
                  <SelectItem value="effort">Effort</SelectItem>
                  <SelectItem value="cost">Cost</SelectItem>
                  <SelectItem value="name">Name</SelectItem>
                  <SelectItem value="strategy">Strategy</SelectItem>
                </SelectContent>
              </Select>

              <Button
                variant="outline"
                size="icon"
                onClick={() => setSortOrder(prev => prev === 'asc' ? 'desc' : 'asc')}
                title={sortOrder === 'asc' ? 'Ascending' : 'Descending'}
              >
                <ArrowUpDown className={cn(
                  'h-4 w-4 transition-transform',
                  sortOrder === 'asc' && 'rotate-180'
                )} />
              </Button>
            </div>

            {/* Filter toggle */}
            <Button
              variant={showFilters ? 'default' : 'outline'}
              onClick={() => setShowFilters(prev => !prev)}
            >
              <Filter className="h-4 w-4 mr-2" />
              Filters
              {hasActiveFilters && (
                <Badge className="ml-2 h-5 w-5 p-0 flex items-center justify-center">
                  {[
                    filters.strategies.length,
                    filters.effort.length,
                    filters.costRange.length,
                    filters.minConfidence ? 1 : 0
                  ].reduce((a, b) => a + b, 0)}
                </Badge>
              )}
            </Button>

            {/* View toggle */}
            <div className="flex items-center border rounded-md">
              <Button
                variant={viewMode === 'grid' ? 'default' : 'ghost'}
                size="icon"
                onClick={() => setViewMode('grid')}
                className="rounded-r-none"
              >
                <LayoutGrid className="h-4 w-4" />
              </Button>
              <Button
                variant={viewMode === 'list' ? 'default' : 'ghost'}
                size="icon"
                onClick={() => setViewMode('list')}
                className="rounded-l-none"
              >
                <List className="h-4 w-4" />
              </Button>
            </div>

            {/* Actions */}
            <div className="flex items-center gap-2">
              {onRefresh && (
                <Button variant="outline" size="icon" onClick={onRefresh}>
                  <RefreshCw className="h-4 w-4" />
                </Button>
              )}
              {onExport && (
                <Select onValueChange={(value) => onExport(value as 'pdf' | 'excel' | 'json')}>
                  <SelectTrigger className="w-[100px]">
                    <Download className="h-4 w-4 mr-2" />
                    Export
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="pdf">PDF</SelectItem>
                    <SelectItem value="excel">Excel</SelectItem>
                    <SelectItem value="json">JSON</SelectItem>
                  </SelectContent>
                </Select>
              )}
            </div>
          </div>

          {/* Filter Panel */}
          {showFilters && (
            <div className="p-4 bg-gray-50 rounded-lg border space-y-4">
              <div className="flex items-center justify-between">
                <h4 className="font-medium text-sm text-gray-700">Filter Options</h4>
                {hasActiveFilters && (
                  <Button variant="ghost" size="sm" onClick={clearFilters}>
                    <X className="h-3 w-3 mr-1" />
                    Clear all
                  </Button>
                )}
              </div>

              {/* Strategy filters */}
              <div className="space-y-2">
                <label className="text-sm font-medium text-gray-600">Strategy</label>
                <div className="flex flex-wrap gap-2">
                  {(Object.keys(SIX_R_STRATEGIES) as SixRStrategyType[]).map(strategyKey => {
                    const strategy = SIX_R_STRATEGIES[strategyKey];
                    const Icon = strategy.icon;
                    const isSelected = filters.strategies.includes(strategyKey);
                    return (
                      <Button
                        key={strategyKey}
                        variant={isSelected ? 'default' : 'outline'}
                        size="sm"
                        onClick={() => toggleStrategyFilter(strategyKey)}
                        className={cn(
                          'gap-1.5',
                          isSelected && strategy.badgeColor
                        )}
                      >
                        <Icon className="h-3 w-3" />
                        {strategy.label}
                      </Button>
                    );
                  })}
                </div>
              </div>

              {/* Effort filters */}
              <div className="space-y-2">
                <label className="text-sm font-medium text-gray-600">Effort Level</label>
                <div className="flex flex-wrap gap-2">
                  {Object.entries(EFFORT_LEVELS).map(([key, config]) => {
                    const isSelected = filters.effort.includes(key as EffortLevel);
                    return (
                      <Button
                        key={key}
                        variant={isSelected ? 'default' : 'outline'}
                        size="sm"
                        onClick={() => toggleEffortFilter(key as EffortLevel)}
                      >
                        {config.shortLabel} ({config.days})
                      </Button>
                    );
                  })}
                </div>
              </div>

              {/* Cost range filters */}
              <div className="space-y-2">
                <label className="text-sm font-medium text-gray-600">Cost Range</label>
                <div className="flex flex-wrap gap-2">
                  {Object.entries(COST_RANGES).map(([key, config]) => {
                    const isSelected = filters.costRange.includes(key as CostRange);
                    return (
                      <Button
                        key={key}
                        variant={isSelected ? 'default' : 'outline'}
                        size="sm"
                        onClick={() => toggleCostFilter(key as CostRange)}
                      >
                        {config.range}
                      </Button>
                    );
                  })}
                </div>
              </div>

              {/* Minimum confidence filter */}
              <div className="space-y-2">
                <label className="text-sm font-medium text-gray-600">Minimum Confidence</label>
                <div className="flex flex-wrap gap-2">
                  {[60, 70, 80, 90].map(threshold => {
                    const isSelected = filters.minConfidence === threshold / 100;
                    return (
                      <Button
                        key={threshold}
                        variant={isSelected ? 'default' : 'outline'}
                        size="sm"
                        onClick={() => updateFilter(
                          'minConfidence',
                          isSelected ? null : threshold / 100
                        )}
                      >
                        {threshold}%+
                      </Button>
                    );
                  })}
                </div>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Results info */}
      {hasActiveFilters && (
        <div className="flex items-center justify-between text-sm text-gray-600">
          <span>
            Showing {filteredAndSortedRecommendations.length} of {recommendations.length} recommendations
          </span>
          <Button variant="ghost" size="sm" onClick={clearFilters}>
            Clear filters
          </Button>
        </div>
      )}

      {/* Recommendation Cards */}
      {filteredAndSortedRecommendations.length === 0 ? (
        <Card>
          <CardContent className="p-8 text-center">
            <AlertCircle className="h-8 w-8 mx-auto text-gray-400 mb-2" />
            <p className="text-gray-600">No recommendations match your filters.</p>
            <Button variant="link" onClick={clearFilters}>
              Clear filters
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className={cn(
          viewMode === 'grid'
            ? 'grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4'
            : 'space-y-4'
        )}>
          {filteredAndSortedRecommendations.map(rec => (
            <RecommendationCard
              key={rec.application_id}
              application_id={rec.application_id}
              application_name={rec.application_name}
              application_version={rec.application_version}
              recommended_strategy={rec.recommended_strategy}
              confidence={rec.confidence}
              effort={rec.effort}
              cost_range={rec.cost_range}
              rationale={rec.rationale}
              risk_factors={rec.risk_factors}
              alternatives={rec.alternatives}
              is_accepted={acceptedIds.has(rec.application_id)}
              is_expanded={expandedCards.has(rec.application_id)}
              onAccept={onAccept}
              onReviewAlternatives={onReviewAlternatives}
              onRequestSME={onRequestSME}
              onToggleExpand={toggleCardExpand}
            />
          ))}
        </div>
      )}

      {/* Bulk actions */}
      {pendingCount > 0 && onAcceptAll && (
        <Card>
          <CardContent className="p-4">
            <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
              <p className="text-sm text-gray-600">
                {pendingCount} recommendation{pendingCount !== 1 ? 's' : ''} pending review
              </p>
              <Button onClick={onAcceptAll}>
                <CheckCircle className="h-4 w-4 mr-2" />
                Accept All Recommendations
              </Button>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default TreatmentRecommendations;
