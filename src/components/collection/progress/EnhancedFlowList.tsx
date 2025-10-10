/**
 * Enhanced Flow List Component
 *
 * Searchable and filterable list of collection flows with advanced filtering
 * Replaces FlowListSidebar with better UX
 */

import React, { useState, useMemo } from 'react';
import { Search, Filter, X } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';

export interface CollectionFlow {
  id: string;
  name: string;
  type: 'adaptive' | 'bulk' | 'integration';
  status: 'running' | 'paused' | 'completed' | 'failed';
  progress: number;
  started_at: string;
  completed_at?: string;
  estimated_completion?: string;
  application_count: number;
  completed_applications: number;
  current_phase?: string;
}

export interface EnhancedFlowListProps {
  flows: CollectionFlow[];
  selectedFlow: string | null;
  onFlowSelect: (flowId: string) => void;
  className?: string;
}

type StatusFilter = 'all' | 'running' | 'paused' | 'completed' | 'failed';
type TypeFilter = 'all' | 'adaptive' | 'bulk' | 'integration';

const getStatusBadge = (status: CollectionFlow['status']): JSX.Element => {
  const variants: Record<CollectionFlow['status'], { variant: 'default' | 'secondary' | 'outline' | 'destructive'; className: string }> = {
    running: { variant: 'default', className: 'bg-blue-500 hover:bg-blue-600' },
    paused: { variant: 'secondary', className: 'bg-yellow-500 hover:bg-yellow-600 text-white' },
    completed: { variant: 'outline', className: 'bg-green-50 text-green-700 border-green-300' },
    failed: { variant: 'destructive', className: '' }
  };

  const config = variants[status];
  return (
    <Badge variant={config.variant} className={config.className}>
      {status.charAt(0).toUpperCase() + status.slice(1)}
    </Badge>
  );
};

export const EnhancedFlowList: React.FC<EnhancedFlowListProps> = ({
  flows,
  selectedFlow,
  onFlowSelect,
  className = ''
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<StatusFilter>('all');
  const [typeFilter, setTypeFilter] = useState<TypeFilter>('all');
  const [showFilters, setShowFilters] = useState(false);

  // Filter flows based on search and filters
  const filteredFlows = useMemo(() => {
    return flows.filter(flow => {
      // Search filter
      const matchesSearch = flow.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                          flow.id.toLowerCase().includes(searchTerm.toLowerCase());

      // Status filter
      const matchesStatus = statusFilter === 'all' || flow.status === statusFilter;

      // Type filter
      const matchesType = typeFilter === 'all' || flow.type === typeFilter;

      return matchesSearch && matchesStatus && matchesType;
    });
  }, [flows, searchTerm, statusFilter, typeFilter]);

  // Count flows by status
  const statusCounts = useMemo(() => ({
    all: flows.length,
    running: flows.filter(f => f.status === 'running').length,
    paused: flows.filter(f => f.status === 'paused').length,
    completed: flows.filter(f => f.status === 'completed').length,
    failed: flows.filter(f => f.status === 'failed').length
  }), [flows]);

  const clearFilters = () => {
    setSearchTerm('');
    setStatusFilter('all');
    setTypeFilter('all');
  };

  const hasActiveFilters = searchTerm || statusFilter !== 'all' || typeFilter !== 'all';

  return (
    <div className={`space-y-3 ${className}`}>
      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="text-lg">Collection Flows</CardTitle>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setShowFilters(!showFilters)}
              className="h-8"
            >
              <Filter className="h-4 w-4" />
            </Button>
          </div>

          {/* Search Bar */}
          <div className="relative mt-2">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search flows..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-9 h-9"
            />
            {searchTerm && (
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setSearchTerm('')}
                className="absolute right-1 top-1/2 -translate-y-1/2 h-7 w-7 p-0"
              >
                <X className="h-3 w-3" />
              </Button>
            )}
          </div>

          {/* Filters */}
          {showFilters && (
            <div className="space-y-3 pt-3 border-t mt-3">
              {/* Status Filter */}
              <div>
                <p className="text-xs font-medium text-muted-foreground mb-2">Status</p>
                <div className="flex flex-wrap gap-1">
                  {(['all', 'running', 'paused', 'completed', 'failed'] as StatusFilter[]).map((status) => (
                    <Button
                      key={status}
                      variant={statusFilter === status ? 'default' : 'outline'}
                      size="sm"
                      onClick={() => setStatusFilter(status)}
                      className="h-7 text-xs"
                    >
                      {status.charAt(0).toUpperCase() + status.slice(1)}
                      {status !== 'all' && (
                        <span className="ml-1 opacity-70">
                          ({statusCounts[status]})
                        </span>
                      )}
                    </Button>
                  ))}
                </div>
              </div>

              {/* Type Filter */}
              <div>
                <p className="text-xs font-medium text-muted-foreground mb-2">Type</p>
                <div className="flex flex-wrap gap-1">
                  {(['all', 'adaptive', 'bulk', 'integration'] as TypeFilter[]).map((type) => (
                    <Button
                      key={type}
                      variant={typeFilter === type ? 'default' : 'outline'}
                      size="sm"
                      onClick={() => setTypeFilter(type)}
                      className="h-7 text-xs capitalize"
                    >
                      {type}
                    </Button>
                  ))}
                </div>
              </div>

              {/* Clear Filters */}
              {hasActiveFilters && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={clearFilters}
                  className="w-full h-7 text-xs"
                >
                  <X className="h-3 w-3 mr-1" />
                  Clear Filters
                </Button>
              )}
            </div>
          )}
        </CardHeader>

        <CardContent className="space-y-2 max-h-[600px] overflow-y-auto">
          {filteredFlows.length === 0 ? (
            <div className="text-center text-muted-foreground py-8">
              <p className="text-sm">
                {flows.length === 0
                  ? 'No collection flows found'
                  : 'No flows match your filters'}
              </p>
              {hasActiveFilters && (
                <Button
                  variant="link"
                  size="sm"
                  onClick={clearFilters}
                  className="mt-2"
                >
                  Clear filters
                </Button>
              )}
            </div>
          ) : (
            filteredFlows.map((flow) => (
              <div
                key={flow.id}
                className={`p-3 rounded-lg border cursor-pointer transition-all ${
                  selectedFlow === flow.id
                    ? 'border-primary bg-primary/5 shadow-sm'
                    : 'hover:bg-muted/50 hover:border-muted-foreground/20'
                }`}
                onClick={() => onFlowSelect(flow.id)}
              >
                <div className="mb-2">
                  <span className="font-medium text-sm line-clamp-2 block mb-2">
                    {flow.name}
                  </span>

                  {/* Status and Phase Badges */}
                  <div className="flex items-center gap-2 flex-wrap">
                    {getStatusBadge(flow.status)}
                    {flow.current_phase && (
                      <Badge variant="outline" className="text-xs bg-blue-50 text-blue-700 border-blue-300">
                        Phase: {flow.current_phase.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                      </Badge>
                    )}
                  </div>
                </div>

                <Progress value={flow.progress} className="h-1.5 mb-2" />

                <div className="flex items-center justify-between text-xs text-muted-foreground">
                  <span>
                    {flow.completed_applications}/{flow.application_count} apps
                  </span>
                  <span className="font-medium">
                    {Math.round(flow.progress)}%
                  </span>
                </div>
              </div>
            ))
          )}
        </CardContent>
      </Card>

      {/* Quick Stats */}
      <Card className="bg-muted/30">
        <CardContent className="p-3">
          <div className="grid grid-cols-2 gap-2 text-xs">
            <div>
              <span className="text-muted-foreground">Active:</span>
              <span className="ml-1 font-medium">{statusCounts.running}</span>
            </div>
            <div>
              <span className="text-muted-foreground">Completed:</span>
              <span className="ml-1 font-medium">{statusCounts.completed}</span>
            </div>
            <div>
              <span className="text-muted-foreground">Paused:</span>
              <span className="ml-1 font-medium">{statusCounts.paused}</span>
            </div>
            <div>
              <span className="text-muted-foreground">Failed:</span>
              <span className="ml-1 font-medium">{statusCounts.failed}</span>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default EnhancedFlowList;
