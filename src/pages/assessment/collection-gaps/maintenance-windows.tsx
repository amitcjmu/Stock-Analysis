/**
 * Maintenance Windows UI
 *
 * Create/edit maintenance schedules with conflict detection visualization
 * Location: src/pages/assessment/collection-gaps/maintenance-windows.tsx
 */

import React, { useState, useCallback } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

// Layout components
import Sidebar from '@/components/Sidebar';
import ContextBreadcrumbs from '@/components/context/ContextBreadcrumbs';

// UI components
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';

// Icons
import {
  Calendar,
  ArrowLeft,
  Plus,
  AlertTriangle,
  Clock,
  Info,
  CalendarDays,
  MapPin
} from 'lucide-react';

// Existing components
import { MaintenanceWindowForm } from '@/components/collection/components/MaintenanceWindowForm';
import { MaintenanceWindowTable } from '@/components/collection/components/MaintenanceWindowTable';

// Services and hooks
import { collectionFlowApi } from '@/services/api/collection-flow';
import { useToast } from '@/components/ui/use-toast';

// Types
import type { MaintenanceWindow } from '@/components/collection/types';

interface ConflictDetection {
  window_id: string;
  conflicting_windows: Array<{
    id: string;
    name: string;
    start_time: string;
    end_time: string;
    scope: string;
    impact_level: string;
  }>;
  overlap_duration_minutes: number;
  risk_level: 'low' | 'medium' | 'high' | 'critical';
}

interface MaintenanceCalendarEvent {
  id: string;
  title: string;
  start: string;
  end: string;
  impact_level: string;
  scope: string;
  scope_id: string;
  approval_required: boolean;
  conflicts: ConflictDetection[];
}

const MaintenanceWindowsPage: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { toast } = useToast();
  const queryClient = useQueryClient();

  const flowId = searchParams.get('flowId') || '';

  // State
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [editingWindow, setEditingWindow] = useState<MaintenanceWindow | null>(null);
  const [selectedScope, setSelectedScope] = useState<'tenant' | 'application' | 'asset'>('tenant');

  // Fetch maintenance windows
  const { data: maintenanceWindows, isLoading, error } = useQuery({
    queryKey: ['maintenance-windows', selectedScope],
    queryFn: async (): Promise<MaintenanceWindow[]> => {
      // This will be replaced with: collectionFlowApi.getMaintenanceWindows(selectedScope)
      await new Promise(resolve => setTimeout(resolve, 1000));

      const mockWindows: MaintenanceWindow[] = [
        {
          id: '1',
          name: 'Monthly Patching Window',
          description: 'Regular monthly security patches and updates',
          scope: 'tenant',
          scope_id: 'tenant-123',
          start_time: '2024-02-15T02:00:00Z',
          end_time: '2024-02-15T06:00:00Z',
          recurrence_pattern: 'monthly',
          timezone: 'UTC',
          impact_level: 'medium',
          approval_required: true,
          created_at: '2024-01-01T00:00:00Z'
        },
        {
          id: '2',
          name: 'Database Maintenance',
          description: 'Weekly database backup and optimization',
          scope: 'application',
          scope_id: 'app-456',
          start_time: '2024-02-18T01:00:00Z',
          end_time: '2024-02-18T03:00:00Z',
          recurrence_pattern: 'weekly',
          timezone: 'UTC',
          impact_level: 'low',
          approval_required: false,
          created_at: '2024-01-05T00:00:00Z'
        },
        {
          id: '3',
          name: 'Critical Security Update',
          description: 'Emergency security patch deployment',
          scope: 'asset',
          scope_id: 'asset-789',
          start_time: '2024-02-16T03:00:00Z',
          end_time: '2024-02-16T05:00:00Z',
          recurrence_pattern: 'none',
          timezone: 'UTC',
          impact_level: 'critical',
          approval_required: true,
          created_at: '2024-02-10T00:00:00Z'
        }
      ];

      return mockWindows.filter(window =>
        selectedScope === 'tenant' ? true : window.scope === selectedScope
      );
    },
    refetchInterval: 30000,
    staleTime: 10000
  });

  // Fetch scope options for form
  const { data: scopeOptions } = useQuery({
    queryKey: ['scope-targets', selectedScope],
    queryFn: async () => {
      // This will be replaced with: collectionFlowApi.getScopeTargets(selectedScope)
      await new Promise(resolve => setTimeout(resolve, 500));

      const mockOptions = {
        tenant: [
          { value: 'tenant-123', label: 'Main Tenant', type: 'tenant' as const }
        ],
        application: [
          { value: 'app-456', label: 'Customer Portal', type: 'application' as const },
          { value: 'app-789', label: 'Payment Service', type: 'application' as const },
          { value: 'app-101', label: 'Analytics Platform', type: 'application' as const }
        ],
        asset: [
          { value: 'asset-789', label: 'DB Server 01', type: 'asset' as const },
          { value: 'asset-012', label: 'Web Server 01', type: 'asset' as const },
          { value: 'asset-345', label: 'Cache Server 01', type: 'asset' as const }
        ]
      };

      return mockOptions[selectedScope] || [];
    },
    enabled: !!selectedScope
  });

  // Fetch conflict detection
  const { data: conflicts } = useQuery({
    queryKey: ['maintenance-conflicts'],
    queryFn: async (): Promise<ConflictDetection[]> => {
      // This will be replaced with: apiCall('/api/v1/collection/maintenance-windows/conflicts')
      await new Promise(resolve => setTimeout(resolve, 800));

      return [
        {
          window_id: '1',
          conflicting_windows: [
            {
              id: '3',
              name: 'Critical Security Update',
              start_time: '2024-02-16T03:00:00Z',
              end_time: '2024-02-16T05:00:00Z',
              scope: 'asset',
              impact_level: 'critical'
            }
          ],
          overlap_duration_minutes: 120,
          risk_level: 'medium'
        }
      ];
    },
    refetchInterval: 60000,
    staleTime: 30000
  });

  // Create maintenance window mutation
  const createWindowMutation = useMutation({
    mutationFn: async (data: MaintenanceWindow): Promise<MaintenanceWindow> => {
      // This will be replaced with: collectionFlowApi.createMaintenanceWindow(data)
      await new Promise(resolve => setTimeout(resolve, 1000));
      return {
        ...data,
        id: Date.now().toString(),
        created_at: new Date().toISOString()
      };
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['maintenance-windows'] });
      queryClient.invalidateQueries({ queryKey: ['maintenance-conflicts'] });
      setShowCreateForm(false);
      toast({
        title: 'Maintenance Window Created',
        description: 'The maintenance window has been successfully created.'
      });
    },
    onError: (error) => {
      console.error('Failed to create maintenance window:', error);
      toast({
        title: 'Creation Failed',
        description: 'Failed to create maintenance window. Please try again.',
        variant: 'destructive'
      });
    }
  });

  // Update maintenance window mutation
  const updateWindowMutation = useMutation({
    mutationFn: async (data: MaintenanceWindow): Promise<MaintenanceWindow> => {
      // This will be replaced with: collectionFlowApi.updateMaintenanceWindow(data.id!, data)
      await new Promise(resolve => setTimeout(resolve, 1000));
      return {
        ...data,
        updated_at: new Date().toISOString()
      };
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['maintenance-windows'] });
      queryClient.invalidateQueries({ queryKey: ['maintenance-conflicts'] });
      setEditingWindow(null);
      toast({
        title: 'Maintenance Window Updated',
        description: 'The maintenance window has been successfully updated.'
      });
    },
    onError: (error) => {
      console.error('Failed to update maintenance window:', error);
      toast({
        title: 'Update Failed',
        description: 'Failed to update maintenance window. Please try again.',
        variant: 'destructive'
      });
    }
  });

  // Delete maintenance window mutation
  const deleteWindowMutation = useMutation({
    mutationFn: async (windowId: string): Promise<void> => {
      // This will be replaced with: collectionFlowApi.deleteMaintenanceWindow(windowId)
      await new Promise(resolve => setTimeout(resolve, 1000));
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['maintenance-windows'] });
      queryClient.invalidateQueries({ queryKey: ['maintenance-conflicts'] });
      toast({
        title: 'Maintenance Window Deleted',
        description: 'The maintenance window has been successfully deleted.'
      });
    },
    onError: (error) => {
      console.error('Failed to delete maintenance window:', error);
      toast({
        title: 'Deletion Failed',
        description: 'Failed to delete maintenance window. Please try again.',
        variant: 'destructive'
      });
    }
  });

  const handleCreateWindow = useCallback(async (data: MaintenanceWindow) => {
    createWindowMutation.mutate(data);
  }, [createWindowMutation]);

  const handleUpdateWindow = useCallback(async (data: MaintenanceWindow) => {
    updateWindowMutation.mutate(data);
  }, [updateWindowMutation]);

  const handleDeleteWindow = useCallback(async (windowId: string) => {
    deleteWindowMutation.mutate(windowId);
  }, [deleteWindowMutation]);

  const handleEditWindow = useCallback((window: MaintenanceWindow) => {
    setEditingWindow(window);
  }, []);

  const handleDuplicateWindow = useCallback((window: MaintenanceWindow) => {
    const duplicated = {
      ...window,
      id: undefined,
      name: `${window.name} (Copy)`,
      created_at: undefined,
      updated_at: undefined
    };
    setEditingWindow(duplicated);
  }, []);

  const getConflictForWindow = (windowId: string): ConflictDetection | undefined => {
    return conflicts?.find(conflict => conflict.window_id === windowId);
  };

  const getConflictBadgeVariant = (riskLevel: string) => {
    switch (riskLevel) {
      case 'critical': return 'destructive';
      case 'high': return 'destructive';
      case 'medium': return 'secondary';
      case 'low': return 'outline';
      default: return 'outline';
    }
  };

  if (!flowId) {
    return (
      <div className="flex min-h-screen bg-gray-50">
        <div className="hidden lg:block w-64 border-r bg-white">
          <Sidebar />
        </div>
        <div className="flex-1 overflow-y-auto">
          <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-4 sm:py-6 lg:py-8 max-w-7xl">
            <Alert>
              <Info className="h-4 w-4" />
              <AlertDescription>
                Flow ID is required to manage maintenance windows. Please navigate from an active collection flow.
              </AlertDescription>
            </Alert>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen bg-gray-50">
      <div className="hidden lg:block w-64 border-r bg-white">
        <Sidebar />
      </div>
      <div className="flex-1 overflow-y-auto">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-4 sm:py-6 lg:py-8 max-w-7xl">
          <div className="mb-6">
            <ContextBreadcrumbs />
          </div>

          <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => navigate(`/assessment/collection-gaps?flowId=${flowId}`)}
                  className="flex items-center gap-2"
                >
                  <ArrowLeft className="h-4 w-4" />
                  Back to Dashboard
                </Button>
                <div>
                  <h1 className="text-3xl font-bold">Maintenance Windows</h1>
                  <p className="text-muted-foreground">
                    Create and manage maintenance schedules with conflict detection
                  </p>
                </div>
              </div>
              <Button
                onClick={() => setShowCreateForm(true)}
                className="flex items-center gap-2"
              >
                <Plus className="h-4 w-4" />
                Create Window
              </Button>
            </div>

            {/* Error handling */}
            {error && (
              <Alert variant="destructive">
                <AlertTriangle className="h-4 w-4" />
                <AlertDescription>
                  Failed to load maintenance windows. Please try refreshing the page.
                </AlertDescription>
              </Alert>
            )}

            {/* Conflict Alerts */}
            {conflicts && conflicts.length > 0 && (
              <Alert>
                <AlertTriangle className="h-4 w-4" />
                <AlertDescription>
                  <div className="space-y-2">
                    <div className="font-medium">
                      {conflicts.length} maintenance window conflict{conflicts.length > 1 ? 's' : ''} detected
                    </div>
                    {conflicts.map((conflict) => {
                      const window = maintenanceWindows?.find(w => w.id === conflict.window_id);
                      return (
                        <div key={conflict.window_id} className="text-sm">
                          <span className="font-medium">{window?.name}</span> conflicts with{' '}
                          {conflict.conflicting_windows.map(cw => cw.name).join(', ')}
                          <Badge className={`ml-2 ${getConflictBadgeVariant(conflict.risk_level)}`}>
                            {conflict.risk_level} risk
                          </Badge>
                        </div>
                      );
                    })}
                  </div>
                </AlertDescription>
              </Alert>
            )}

            {/* Create/Edit Form */}
            {(showCreateForm || editingWindow) && (
              <MaintenanceWindowForm
                initialData={editingWindow || undefined}
                onSave={editingWindow ? handleUpdateWindow : handleCreateWindow}
                onCancel={() => {
                  setShowCreateForm(false);
                  setEditingWindow(null);
                }}
                scopeOptions={scopeOptions}
              />
            )}

            {/* Main Content */}
            <Tabs defaultValue="list" className="space-y-6">
              <TabsList>
                <TabsTrigger value="list" className="flex items-center gap-2">
                  <Calendar className="h-4 w-4" />
                  List View
                </TabsTrigger>
                <TabsTrigger value="calendar" className="flex items-center gap-2">
                  <CalendarDays className="h-4 w-4" />
                  Calendar View
                </TabsTrigger>
                <TabsTrigger value="conflicts" className="flex items-center gap-2">
                  <AlertTriangle className="h-4 w-4" />
                  Conflicts
                </TabsTrigger>
              </TabsList>

              <TabsContent value="list" className="space-y-6">
                {/* Scope Filter */}
                <div className="flex gap-2">
                  <Button
                    variant={selectedScope === 'tenant' ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => setSelectedScope('tenant')}
                  >
                    Tenant-wide
                  </Button>
                  <Button
                    variant={selectedScope === 'application' ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => setSelectedScope('application')}
                  >
                    Application
                  </Button>
                  <Button
                    variant={selectedScope === 'asset' ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => setSelectedScope('asset')}
                  >
                    Asset
                  </Button>
                </div>

                {/* Maintenance Windows Table */}
                <MaintenanceWindowTable
                  windows={maintenanceWindows || []}
                  onEdit={handleEditWindow}
                  onDelete={handleDeleteWindow}
                  onDuplicate={handleDuplicateWindow}
                  loading={isLoading}
                />
              </TabsContent>

              <TabsContent value="calendar" className="space-y-6">
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <CalendarDays className="h-5 w-5" />
                      Maintenance Calendar
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-center py-12">
                      <CalendarDays className="mx-auto h-16 w-16 text-gray-400" />
                      <h3 className="mt-4 text-lg font-medium">Calendar View</h3>
                      <p className="mt-2 text-sm text-gray-500">
                        Calendar visualization will be implemented with a calendar component
                        showing maintenance windows and conflicts
                      </p>
                    </div>
                  </CardContent>
                </Card>
              </TabsContent>

              <TabsContent value="conflicts" className="space-y-6">
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <AlertTriangle className="h-5 w-5" />
                      Conflict Detection
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    {conflicts && conflicts.length > 0 ? (
                      <div className="space-y-4">
                        {conflicts.map((conflict) => {
                          const window = maintenanceWindows?.find(w => w.id === conflict.window_id);
                          return (
                            <div key={conflict.window_id} className="border rounded-lg p-4">
                              <div className="flex items-start justify-between">
                                <div className="space-y-2">
                                  <div className="flex items-center gap-2">
                                    <h4 className="font-medium">{window?.name}</h4>
                                    <Badge variant={getConflictBadgeVariant(conflict.risk_level)}>
                                      {conflict.risk_level} risk
                                    </Badge>
                                  </div>
                                  <div className="text-sm text-muted-foreground flex items-center gap-2">
                                    <Clock className="h-4 w-4" />
                                    Overlap: {Math.floor(conflict.overlap_duration_minutes / 60)}h {conflict.overlap_duration_minutes % 60}m
                                  </div>
                                </div>
                                <div className="text-right">
                                  <div className="text-sm font-medium">
                                    {conflict.conflicting_windows.length} conflict{conflict.conflicting_windows.length > 1 ? 's' : ''}
                                  </div>
                                </div>
                              </div>

                              <div className="mt-4 space-y-2">
                                <div className="text-sm font-medium">Conflicting Windows:</div>
                                {conflict.conflicting_windows.map((cw) => (
                                  <div key={cw.id} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                                    <div>
                                      <div className="font-medium">{cw.name}</div>
                                      <div className="text-xs text-muted-foreground flex items-center gap-1">
                                        <MapPin className="h-3 w-3" />
                                        {cw.scope}
                                      </div>
                                    </div>
                                    <div className="text-right">
                                      <Badge variant={
                                        cw.impact_level === 'critical' ? 'destructive' :
                                        cw.impact_level === 'high' ? 'destructive' :
                                        cw.impact_level === 'medium' ? 'secondary' : 'outline'
                                      }>
                                        {cw.impact_level}
                                      </Badge>
                                      <div className="text-xs text-muted-foreground mt-1">
                                        {new Date(cw.start_time).toLocaleString()} - {new Date(cw.end_time).toLocaleString()}
                                      </div>
                                    </div>
                                  </div>
                                ))}
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    ) : (
                      <div className="text-center py-8">
                        <AlertTriangle className="mx-auto h-12 w-12 text-green-400" />
                        <h3 className="mt-2 text-lg font-medium text-green-800">No Conflicts Detected</h3>
                        <p className="mt-1 text-sm text-green-600">
                          All maintenance windows are properly scheduled without overlaps.
                        </p>
                      </div>
                    )}
                  </CardContent>
                </Card>
              </TabsContent>
            </Tabs>
          </div>
        </div>
      </div>
    </div>
  );
};

export default MaintenanceWindowsPage;
