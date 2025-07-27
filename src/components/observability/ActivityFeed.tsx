/**
 * Activity Feed Component
 * Real-time activity stream for agent activities and system events
 * Part of the Agent Observability Enhancement Phase 4B - Advanced Features
 */

import React from 'react'
import { useState, useRef } from 'react'
import { useEffect, useMemo } from 'react'
import { formatDistanceToNow } from 'date-fns';
import { Brain, Filter, Search } from 'lucide-react'
import { Activity, CheckCircle, XCircle, Clock, AlertTriangle, User, Zap, Play, Pause, RotateCcw, Volume2, VolumeX } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Badge } from '../ui/badge';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { Switch } from '../ui/switch';
import { agentObservabilityService } from '../../services/api/agentObservabilityService';

// Activity types and interfaces
export interface ActivityEvent {
  id: string;
  timestamp: string;
  type: 'task_started' | 'task_completed' | 'task_failed' | 'agent_error' | 'agent_status_change' | 'system_event' | 'user_interaction';
  severity: 'info' | 'success' | 'warning' | 'error';
  agentName?: string;
  title: string;
  description: string;
  metadata?: {
    taskId?: string;
    flowId?: string;
    duration?: number;
    errorCode?: string;
    userId?: string;
    previousStatus?: string;
    newStatus?: string;
    [key: string]: unknown;
  };
}

interface ActivityFeedProps {
  /** Maximum number of events to show */
  maxEvents?: number;
  /** Auto-refresh interval in milliseconds */
  refreshInterval?: number;
  /** Show only events for specific agent */
  agentFilter?: string;
  /** Height of the feed container */
  height?: string | number;
  /** Enable real-time updates */
  realTime?: boolean;
  /** Show filters and controls */
  showControls?: boolean;
  /** Compact view mode */
  compact?: boolean;
  /** Callback when event is clicked */
  onEventClick?: (event: ActivityEvent) => void;
  /** CSS class name */
  className?: string;
}

interface ActivityFilters {
  search: string;
  agent: string;
  type: string;
  severity: string;
  timeRange: string;
}

const ActivityEventIcon: React.FC<{ type: ActivityEvent['type']; severity: ActivityEvent['severity'] }> = ({ type, severity }) => {
  const iconClasses = "w-4 h-4";

  switch (type) {
    case 'task_started':
      return <Play className={`${iconClasses} text-blue-500`} />;
    case 'task_completed':
      return <CheckCircle className={`${iconClasses} text-green-500`} />;
    case 'task_failed':
      return <XCircle className={`${iconClasses} text-red-500`} />;
    case 'agent_error':
      return <AlertTriangle className={`${iconClasses} text-red-500`} />;
    case 'agent_status_change':
      return <Activity className={`${iconClasses} text-purple-500`} />;
    case 'system_event':
      return <Zap className={`${iconClasses} text-yellow-500`} />;
    case 'user_interaction':
      return <User className={`${iconClasses} text-indigo-500`} />;
    default:
      return <Activity className={`${iconClasses} text-gray-500`} />;
  }
};

const ActivityEventRow: React.FC<{
  event: ActivityEvent;
  compact?: boolean;
  onClick?: (event: ActivityEvent) => void;
}> = ({ event, compact = false, onClick }) => {
  const timeAgo = formatDistanceToNow(new Date(event.timestamp), { addSuffix: true });

  const severityColors = {
    info: 'border-l-blue-400 bg-blue-50',
    success: 'border-l-green-400 bg-green-50',
    warning: 'border-l-yellow-400 bg-yellow-50',
    error: 'border-l-red-400 bg-red-50'
  };

  const handleClick = (): void => {
    if (onClick) {
      onClick(event);
    }
  };

  return (
    <div
      className={`
        border-l-4 p-3 mb-2 rounded-r-md transition-all duration-200 hover:shadow-sm
        ${severityColors[event.severity]}
        ${onClick ? 'cursor-pointer hover:bg-opacity-80' : ''}
        ${compact ? 'py-2' : ''}
      `}
      onClick={handleClick}
    >
      <div className="flex items-start gap-3">
        <div className="flex-shrink-0 mt-1">
          <ActivityEventIcon type={event.type} severity={event.severity} />
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <h4 className={`font-medium text-gray-900 truncate ${compact ? 'text-sm' : ''}`}>
                {event.title}
              </h4>
              {event.agentName && (
                <Badge variant="secondary" className="text-xs">
                  {event.agentName}
                </Badge>
              )}
            </div>
            <span className={`text-gray-500 flex-shrink-0 ${compact ? 'text-xs' : 'text-sm'}`}>
              {timeAgo}
            </span>
          </div>

          <p className={`text-gray-600 mt-1 ${compact ? 'text-xs' : 'text-sm'}`}>
            {event.description}
          </p>

          {event.metadata && !compact && (
            <div className="flex flex-wrap gap-2 mt-2">
              {event.metadata.duration && (
                <Badge variant="outline" className="text-xs">
                  <Clock className="w-3 h-3 mr-1" />
                  {event.metadata.duration.toFixed(1)}s
                </Badge>
              )}
              {event.metadata.taskId && (
                <Badge variant="outline" className="text-xs">
                  Task: {event.metadata.taskId.slice(-8)}
                </Badge>
              )}
              {event.metadata.flowId && (
                <Badge variant="outline" className="text-xs">
                  Flow: {event.metadata.flowId.slice(-8)}
                </Badge>
              )}
              {event.metadata.errorCode && (
                <Badge variant="destructive" className="text-xs">
                  Error: {event.metadata.errorCode}
                </Badge>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

const ActivityFeed: React.FC<ActivityFeedProps> = ({
  maxEvents = 100,
  refreshInterval = 5000,
  agentFilter,
  height = '600px',
  realTime = true,
  showControls = true,
  compact = false,
  onEventClick,
  className = ''
}) => {
  const [events, setEvents] = useState<ActivityEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isPlaying, setIsPlaying] = useState(realTime);
  const [soundEnabled, setSoundEnabled] = useState(false);
  const [filters, setFilters] = useState<ActivityFilters>({
    search: '',
    agent: agentFilter || '',
    type: '',
    severity: '',
    timeRange: '1h'
  });

  const intervalRef = useRef<NodeJS.Timeout>();
  const eventContainerRef = useRef<HTMLDivElement>(null);
  const audioRef = useRef<HTMLAudioElement>(null);

  // Load activity feed data
  useEffect(() => {
    loadActivityData();

    if (isPlaying && realTime) {
      intervalRef.current = setInterval(loadActivityData, refreshInterval);
    }

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [isPlaying, realTime, refreshInterval, filters.agent, filters.timeRange]);

  const loadActivityData = async (): Promise<void> => {
    try {
      setError(null);

      // Get activity feed data from API
      const response = await agentObservabilityService.getAgentActivityFeed(
        filters.agent || undefined,
        true, // includeCompleted
        maxEvents
      );

      if (response.success && response.data) {
        // Transform API response to ActivityEvent format
        const transformedEvents: ActivityEvent[] = response.data.activities.map(activity => ({
          id: activity.id,
          timestamp: activity.timestamp,
          type: mapActivityType(activity.event_type),
          severity: mapSeverity(activity.severity),
          agentName: activity.agent_name,
          title: activity.title,
          description: activity.description,
          metadata: activity.metadata
        }));

        // Sort by timestamp (newest first)
        transformedEvents.sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());

        // Check for new events and play sound
        if (events.length > 0 && transformedEvents.length > events.length && soundEnabled) {
          playNotificationSound();
        }

        setEvents(transformedEvents);
      } else {
        // No activity data available - this is normal if no tasks have been executed yet
        setEvents([]);
      }
    } catch (err) {
      console.error('Failed to load activity data:', err);
      setError(err instanceof Error ? err.message : 'Failed to load activity data');
      // Set empty events to show "no data" state rather than error state
      setEvents([]);
    } finally {
      setLoading(false);
    }
  };

  // Helper functions
  const mapActivityType = (apiType: string): ActivityEvent['type'] => {
    const mapping: Record<string, ActivityEvent['type']> = {
      'task_started': 'task_started',
      'task_completed': 'task_completed',
      'task_failed': 'task_failed',
      'agent_error': 'agent_error',
      'agent_status_change': 'agent_status_change',
      'system_event': 'system_event',
      'user_interaction': 'user_interaction'
    };
    return mapping[apiType] || 'system_event';
  };

  const mapSeverity = (apiSeverity: string): ActivityEvent['severity'] => {
    const mapping: Record<string, ActivityEvent['severity']> = {
      'info': 'info',
      'success': 'success',
      'warning': 'warning',
      'error': 'error'
    };
    return mapping[apiSeverity] || 'info';
  };

  const playNotificationSound = (): unknown => {
    if (audioRef.current) {
      audioRef.current.play().catch(() => {
        // Ignore audio play errors (user interaction required)
      });
    }
  };

  // Filter events based on current filters
  const filteredEvents = useMemo(() => {
    return events.filter(event => {
      if (filters.search && !event.title.toLowerCase().includes(filters.search.toLowerCase()) &&
          !event.description.toLowerCase().includes(filters.search.toLowerCase())) {
        return false;
      }

      if (filters.agent && event.agentName !== filters.agent) {
        return false;
      }

      if (filters.type && event.type !== filters.type) {
        return false;
      }

      if (filters.severity && event.severity !== filters.severity) {
        return false;
      }

      // Time range filtering
      if (filters.timeRange) {
        const now = new Date();
        const eventTime = new Date(event.timestamp);
        const diffMs = now.getTime() - eventTime.getTime();

        const timeRanges: Record<string, number> = {
          '15m': 15 * 60 * 1000,
          '1h': 60 * 60 * 1000,
          '6h': 6 * 60 * 60 * 1000,
          '24h': 24 * 60 * 60 * 1000,
          '7d': 7 * 24 * 60 * 60 * 1000
        };

        if (timeRanges[filters.timeRange] && diffMs > timeRanges[filters.timeRange]) {
          return false;
        }
      }

      return true;
    });
  }, [events, filters]);

  const handleTogglePlayPause = (): void => {
    setIsPlaying(!isPlaying);
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
    }
  };

  const handleRefresh = (): void => {
    setLoading(true);
    loadActivityData();
  };

  const handleClearAll = (): void => {
    setEvents([]);
  };

  const getEventCounts = (): unknown => {
    const counts = {
      total: filteredEvents.length,
      success: filteredEvents.filter(e => e.severity === 'success').length,
      error: filteredEvents.filter(e => e.severity === 'error').length,
      warning: filteredEvents.filter(e => e.severity === 'warning').length,
      info: filteredEvents.filter(e => e.severity === 'info').length
    };
    return counts;
  };

  const eventCounts = getEventCounts();

  return (
    <Card className={className}>
      <CardHeader className="pb-4">
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <Activity className="w-5 h-5" />
              Activity Feed
              {!isPlaying && <Badge variant="secondary">Paused</Badge>}
            </CardTitle>
            <div className="flex items-center gap-4 mt-2 text-sm text-gray-600">
              <span>{eventCounts.total} events</span>
              <span className="text-green-600">{eventCounts.success} success</span>
              <span className="text-red-600">{eventCounts.error} errors</span>
              <span className="text-yellow-600">{eventCounts.warning} warnings</span>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <Button
              onClick={handleTogglePlayPause}
              variant="outline"
              size="sm"
            >
              {isPlaying ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
            </Button>
            <Button
              onClick={handleRefresh}
              variant="outline"
              size="sm"
              disabled={loading}
            >
              <RotateCcw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            </Button>
            <Button
              onClick={() => setSoundEnabled(!soundEnabled)}
              variant="outline"
              size="sm"
            >
              {soundEnabled ? <Volume2 className="w-4 h-4" /> : <VolumeX className="w-4 h-4" />}
            </Button>
          </div>
        </div>

        {showControls && (
          <div className="flex flex-wrap gap-3 mt-4">
            <div className="flex-1 min-w-64">
              <Input
                placeholder="Search events..."
                value={filters.search}
                onChange={(e) => setFilters(prev => ({ ...prev, search: e.target.value }))}
                className="w-full"
              />
            </div>

            <Select value={filters.agent} onValueChange={(value) => setFilters(prev => ({ ...prev, agent: value }))}>
              <SelectTrigger className="w-48">
                <SelectValue placeholder="All agents" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="">All agents</SelectItem>
                <SelectItem value="DataImportValidationAgent">Data Import Validation</SelectItem>
                <SelectItem value="AttributeMappingAgent">Attribute Mapping</SelectItem>
                <SelectItem value="DataCleansingAgent">Data Cleansing</SelectItem>
                <SelectItem value="AssetInventoryAgent">Asset Inventory</SelectItem>
                <SelectItem value="DependencyAnalysisAgent">Dependency Analysis</SelectItem>
                <SelectItem value="TechDebtAnalysisAgent">Tech Debt Analysis</SelectItem>
              </SelectContent>
            </Select>

            <Select value={filters.type} onValueChange={(value) => setFilters(prev => ({ ...prev, type: value }))}>
              <SelectTrigger className="w-40">
                <SelectValue placeholder="All types" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="">All types</SelectItem>
                <SelectItem value="task_started">Task Started</SelectItem>
                <SelectItem value="task_completed">Task Completed</SelectItem>
                <SelectItem value="task_failed">Task Failed</SelectItem>
                <SelectItem value="agent_error">Agent Error</SelectItem>
                <SelectItem value="system_event">System Event</SelectItem>
              </SelectContent>
            </Select>

            <Select value={filters.timeRange} onValueChange={(value) => setFilters(prev => ({ ...prev, timeRange: value }))}>
              <SelectTrigger className="w-32">
                <SelectValue placeholder="Time range" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="15m">Last 15min</SelectItem>
                <SelectItem value="1h">Last hour</SelectItem>
                <SelectItem value="6h">Last 6 hours</SelectItem>
                <SelectItem value="24h">Last 24 hours</SelectItem>
                <SelectItem value="7d">Last 7 days</SelectItem>
              </SelectContent>
            </Select>
          </div>
        )}
      </CardHeader>

      <CardContent className="p-0">
        <div
          ref={eventContainerRef}
          className="overflow-y-auto px-6 pb-6"
          style={{ height: typeof height === 'number' ? `${height}px` : height }}
        >
          {loading && events.length === 0 ? (
            <div className="flex items-center justify-center py-8">
              <div className="text-center">
                <Activity className="w-8 h-8 text-gray-400 mx-auto mb-2 animate-pulse" />
                <p className="text-gray-500">Loading activity feed...</p>
              </div>
            </div>
          ) : error ? (
            <div className="flex items-center justify-center py-8">
              <div className="text-center">
                <AlertTriangle className="w-8 h-8 text-red-400 mx-auto mb-2" />
                <p className="text-red-600">{error}</p>
                <Button onClick={handleRefresh} variant="outline" size="sm" className="mt-2">
                  Try Again
                </Button>
              </div>
            </div>
          ) : filteredEvents.length === 0 ? (
            <div className="flex items-center justify-center py-8">
              <div className="text-center">
                <Activity className="w-8 h-8 text-gray-400 mx-auto mb-2" />
                <p className="text-gray-500">No events found</p>
                <p className="text-gray-400 text-sm">Try adjusting your filters or wait for new activity</p>
              </div>
            </div>
          ) : (
            <div className="space-y-0">
              {filteredEvents.map((event) => (
                <ActivityEventRow
                  key={event.id}
                  event={event}
                  compact={compact}
                  onClick={onEventClick}
                />
              ))}
            </div>
          )}
        </div>
      </CardContent>

      {/* Audio element for notifications */}
      <audio ref={audioRef} preload="auto">
        <source src="data:audio/wav;base64,UklGRnoGAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQoGAACBhYqFbF1fdJivrJBhNjVgodDbq2EcBj+a2/LDciUFLIHO8tiJNwgZaLvt559NEAxQp+PwtmMcBjiR1/LMeSwFJHfH8N2QQAoUXrTp66hVFApGn+DyvWQdBTuJ0O3IdSkGJ4DJ69l/OwgYYrPn6q9GEgtOo9z0yW4eDC+L0eXIeC8HPnzH7OBxPx8XX6n..." type="audio/wav" />
      </audio>
    </Card>
  );
};

export default ActivityFeed;

// Export additional components for modular usage
export { ActivityEventRow, ActivityEventIcon };
export type { ActivityEvent, ActivityFeedProps, ActivityFilters };
