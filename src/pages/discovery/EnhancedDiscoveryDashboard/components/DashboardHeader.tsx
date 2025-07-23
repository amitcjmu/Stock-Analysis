import React from 'react';
import type { Filter, Settings } from 'lucide-react'
import { RefreshCw, Plus, Brain } from 'lucide-react'
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { 
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import type { DashboardFilters } from '../types';

interface DashboardHeaderProps {
  filters: DashboardFilters;
  onRefresh: () => void;
  onTimeRangeChange: (timeRange: string) => void;
  onNewFlow: () => void;
  isLoading: boolean;
  lastUpdated: Date;
  totalFlows: number;
  activeFlows: number;
}

export const DashboardHeader: React.FC<DashboardHeaderProps> = ({
  filters,
  onRefresh,
  onTimeRangeChange,
  onNewFlow,
  isLoading,
  lastUpdated,
  totalFlows,
  activeFlows
}) => {
  return (
    <div className="mb-8">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-3">
          <Brain className="h-8 w-8 text-blue-600" />
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Discovery Dashboard</h1>
            <p className="text-gray-600">
              AI-powered migration flows and real-time monitoring
            </p>
          </div>
        </div>
        
        <div className="flex items-center space-x-3">
          {/* Status badges */}
          <div className="flex items-center space-x-2">
            <Badge variant="outline" className="bg-blue-50 text-blue-700 border-blue-200">
              {totalFlows} Total Flows
            </Badge>
            <Badge variant="outline" className="bg-green-50 text-green-700 border-green-200">
              {activeFlows} Active
            </Badge>
          </div>
          
          {/* Time range selector */}
          <Select value={filters.timeRange} onValueChange={onTimeRangeChange}>
            <SelectTrigger className="w-40">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="1h">Last Hour</SelectItem>
              <SelectItem value="6h">Last 6 Hours</SelectItem>
              <SelectItem value="24h">Last 24 Hours</SelectItem>
              <SelectItem value="7d">Last 7 Days</SelectItem>
              <SelectItem value="30d">Last 30 Days</SelectItem>
              <SelectItem value="all">All Time</SelectItem>
            </SelectContent>
          </Select>
          
          {/* Action buttons */}
          <Button
            variant="outline"
            size="sm"
            onClick={onRefresh}
            disabled={isLoading}
            className="flex items-center space-x-2"
          >
            <RefreshCw className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
            <span>Refresh</span>
          </Button>
          
          <Button
            onClick={onNewFlow}
            className="flex items-center space-x-2 bg-blue-600 hover:bg-blue-700"
          >
            <Plus className="h-4 w-4" />
            <span>New Flow</span>
          </Button>
        </div>
      </div>
      
      {/* Last updated indicator */}
      <div className="flex items-center justify-between text-sm text-gray-500">
        <div className="flex items-center space-x-2">
          <Filter className="h-4 w-4" />
          <span>Showing {filters.timeRange === 'all' ? 'all' : filters.timeRange} data</span>
        </div>
        <div className="flex items-center space-x-2">
          <span>Last updated: {lastUpdated.toLocaleTimeString()}</span>
        </div>
      </div>
    </div>
  );
};