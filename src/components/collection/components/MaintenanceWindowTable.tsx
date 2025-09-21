/**
 * Maintenance Window Table Component
 *
 * Table view to display existing maintenance windows with actions
 */

import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '@/components/ui/dropdown-menu';
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle } from '@/components/ui/alert-dialog';
import { Calendar, Clock, MoreHorizontal, Edit, Trash2, Copy, AlertTriangle } from 'lucide-react';
import { cn } from '@/lib/utils';
import type { MaintenanceWindow } from '../types';

interface MaintenanceWindowTableProps {
  windows: MaintenanceWindow[];
  onEdit?: (window: MaintenanceWindow) => void;
  onDelete?: (windowId: string) => Promise<void>;
  onDuplicate?: (window: MaintenanceWindow) => void;
  loading?: boolean;
  className?: string;
}

export const MaintenanceWindowTable: React.FC<MaintenanceWindowTableProps> = ({
  windows,
  onEdit,
  onDelete,
  onDuplicate,
  loading = false,
  className
}) => {
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [windowToDelete, setWindowToDelete] = useState<MaintenanceWindow | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);

  const formatDateTime = (dateStr: string) => {
    try {
      return new Date(dateStr).toLocaleString();
    } catch {
      return dateStr;
    }
  };

  const formatDuration = (startTime: string, endTime: string) => {
    try {
      const start = new Date(startTime);
      const end = new Date(endTime);
      const durationMs = end.getTime() - start.getTime();
      const hours = Math.floor(durationMs / (1000 * 60 * 60));
      const minutes = Math.floor((durationMs % (1000 * 60 * 60)) / (1000 * 60));

      if (hours > 0) {
        return `${hours}h ${minutes}m`;
      }
      return `${minutes}m`;
    } catch {
      return 'N/A';
    }
  };

  const getStatusColor = (window: MaintenanceWindow) => {
    const now = new Date();
    const start = new Date(window.start_time);
    const end = new Date(window.end_time);

    if (now < start) {
      return 'bg-blue-100 text-blue-800'; // Scheduled
    } else if (now >= start && now <= end) {
      return 'bg-red-100 text-red-800'; // Active
    } else {
      return 'bg-gray-100 text-gray-800'; // Completed
    }
  };

  const getStatus = (window: MaintenanceWindow) => {
    const now = new Date();
    const start = new Date(window.start_time);
    const end = new Date(window.end_time);

    if (now < start) {
      return 'Scheduled';
    } else if (now >= start && now <= end) {
      return 'Active';
    } else {
      return 'Completed';
    }
  };

  const getImpactColor = (level: string) => {
    switch (level) {
      case 'low': return 'bg-green-100 text-green-800';
      case 'medium': return 'bg-yellow-100 text-yellow-800';
      case 'high': return 'bg-orange-100 text-orange-800';
      case 'critical': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const handleDeleteClick = (window: MaintenanceWindow) => {
    setWindowToDelete(window);
    setDeleteDialogOpen(true);
  };

  const handleDeleteConfirm = async () => {
    if (!windowToDelete?.id || !onDelete) return;

    setIsDeleting(true);
    try {
      await onDelete(windowToDelete.id);
      setDeleteDialogOpen(false);
      setWindowToDelete(null);
    } catch (error) {
      console.error('Failed to delete maintenance window:', error);
    } finally {
      setIsDeleting(false);
    }
  };

  if (loading) {
    return (
      <Card className={className}>
        <CardContent className="p-6">
          <div className="space-y-2">
            {[...Array(3)].map((_, i) => (
              <div key={i} className="h-12 bg-gray-100 rounded animate-pulse" />
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  if (windows.length === 0) {
    return (
      <Card className={className}>
        <CardContent className="p-6">
          <div className="text-center py-8">
            <Calendar className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-sm font-medium text-gray-900">No maintenance windows</h3>
            <p className="mt-1 text-sm text-gray-500">
              Get started by creating your first maintenance window.
            </p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <>
      <Card className={className}>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Calendar className="h-5 w-5" />
            Maintenance Windows ({windows.length})
          </CardTitle>
        </CardHeader>

        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Name</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Impact</TableHead>
                <TableHead>Scope</TableHead>
                <TableHead>Schedule</TableHead>
                <TableHead>Duration</TableHead>
                <TableHead>Recurrence</TableHead>
                <TableHead className="w-12"></TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {windows.map((window) => (
                <TableRow key={window.id || window.name}>
                  <TableCell>
                    <div className="space-y-1">
                      <div className="font-medium">{window.name}</div>
                      {window.description && (
                        <div className="text-xs text-muted-foreground">
                          {window.description.substring(0, 50)}
                          {window.description.length > 50 && '...'}
                        </div>
                      )}
                      {window.approval_required && (
                        <div className="flex items-center gap-1 text-xs text-amber-600">
                          <AlertTriangle className="h-3 w-3" />
                          Approval Required
                        </div>
                      )}
                    </div>
                  </TableCell>
                  <TableCell>
                    <Badge className={getStatusColor(window)}>
                      {getStatus(window)}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <Badge className={getImpactColor(window.impact_level)}>
                      {window.impact_level.charAt(0).toUpperCase() + window.impact_level.slice(1)}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <div className="text-sm">
                      <div className="capitalize">{window.scope}</div>
                      <div className="text-xs text-muted-foreground">{window.scope_id}</div>
                    </div>
                  </TableCell>
                  <TableCell>
                    <div className="text-sm space-y-1">
                      <div className="flex items-center gap-1">
                        <Clock className="h-3 w-3 text-muted-foreground" />
                        {formatDateTime(window.start_time)}
                      </div>
                      <div className="text-xs text-muted-foreground">
                        to {formatDateTime(window.end_time)}
                      </div>
                    </div>
                  </TableCell>
                  <TableCell>
                    <div className="text-sm">
                      {formatDuration(window.start_time, window.end_time)}
                    </div>
                  </TableCell>
                  <TableCell>
                    <div className="text-sm capitalize">
                      {window.recurrence_pattern === 'none' ? 'One-time' : window.recurrence_pattern}
                    </div>
                  </TableCell>
                  <TableCell>
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
                          <MoreHorizontal className="h-4 w-4" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        {onEdit && (
                          <DropdownMenuItem onClick={() => onEdit(window)}>
                            <Edit className="mr-2 h-4 w-4" />
                            Edit
                          </DropdownMenuItem>
                        )}
                        {onDuplicate && (
                          <DropdownMenuItem onClick={() => onDuplicate(window)}>
                            <Copy className="mr-2 h-4 w-4" />
                            Duplicate
                          </DropdownMenuItem>
                        )}
                        {onDelete && (
                          <DropdownMenuItem
                            onClick={() => handleDeleteClick(window)}
                            className="text-red-600"
                          >
                            <Trash2 className="mr-2 h-4 w-4" />
                            Delete
                          </DropdownMenuItem>
                        )}
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* Delete Confirmation Dialog */}
      <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Maintenance Window</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to delete "{windowToDelete?.name}"? This action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={isDeleting}>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDeleteConfirm}
              disabled={isDeleting}
              className="bg-red-600 hover:bg-red-700"
            >
              {isDeleting ? 'Deleting...' : 'Delete'}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
};
