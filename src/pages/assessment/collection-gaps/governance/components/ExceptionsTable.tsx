/**
 * ExceptionsTable Component
 * Display migration exceptions with status and approval history
 */

import React from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '@/components/ui/dropdown-menu';
import { AlertTriangle, User, Calendar, CheckCircle, MoreHorizontal, Eye, Edit } from 'lucide-react';
import type { MigrationException } from '../types';
import { getStatusBadgeVariant, getPriorityBadgeVariant } from '../utils/statusHelpers';

interface ExceptionsTableProps {
  exceptions: MigrationException[] | undefined;
  isLoading: boolean;
}

export const ExceptionsTable: React.FC<ExceptionsTableProps> = ({
  exceptions,
  isLoading
}) => {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <AlertTriangle className="h-5 w-5" />
          Migration Exceptions ({exceptions?.length || 0})
        </CardTitle>
      </CardHeader>
      <CardContent className="p-0">
        {isLoading ? (
          <div className="p-6">
            <div className="space-y-3">
              {[...Array(3)].map((_, i) => (
                <div key={i} className="h-20 bg-gray-100 rounded animate-pulse" />
              ))}
            </div>
          </div>
        ) : exceptions && exceptions.length > 0 ? (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Exception</TableHead>
                <TableHead>Priority</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Scope</TableHead>
                <TableHead>Requested By</TableHead>
                <TableHead>Created</TableHead>
                <TableHead>Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {exceptions.map((exception) => (
                <TableRow key={exception.id}>
                  <TableCell>
                    <div className="space-y-1">
                      <div className="font-medium">{exception.title}</div>
                      <div className="text-sm text-muted-foreground">
                        {exception.justification.substring(0, 100)}
                        {exception.justification.length > 100 && '...'}
                      </div>
                    </div>
                  </TableCell>
                  <TableCell>
                    <Badge variant={getPriorityBadgeVariant(exception.priority)}>
                      {exception.priority}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <div className="space-y-1">
                      <Badge variant={getStatusBadgeVariant(exception.status)}>
                        {exception.status}
                      </Badge>
                      {exception.status === 'approved' && exception.approval_history.length > 0 && (
                        <div className="text-xs text-green-600 flex items-center gap-1">
                          <CheckCircle className="h-3 w-3" />
                          {new Date(exception.approval_history[exception.approval_history.length - 1].timestamp).toLocaleDateString()}
                        </div>
                      )}
                    </div>
                  </TableCell>
                  <TableCell>
                    <div className="space-y-1">
                      <Badge variant="outline" className="capitalize">
                        {exception.scope}
                      </Badge>
                      <div className="text-xs text-muted-foreground">
                        {exception.scope_id}
                      </div>
                    </div>
                  </TableCell>
                  <TableCell>
                    <div className="flex items-center gap-1 text-sm">
                      <User className="h-3 w-3" />
                      {exception.requested_by}
                    </div>
                  </TableCell>
                  <TableCell>
                    <div className="flex items-center gap-1 text-sm">
                      <Calendar className="h-3 w-3" />
                      {new Date(exception.created_at).toLocaleDateString()}
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
                        <DropdownMenuItem>
                          <Eye className="mr-2 h-4 w-4" />
                          View Details
                        </DropdownMenuItem>
                        {exception.status === 'pending' && (
                          <DropdownMenuItem>
                            <Edit className="mr-2 h-4 w-4" />
                            Edit
                          </DropdownMenuItem>
                        )}
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        ) : (
          <div className="p-6 text-center">
            <AlertTriangle className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-sm font-medium text-gray-900">No exceptions found</h3>
            <p className="mt-1 text-sm text-gray-500">
              No migration exceptions have been submitted yet.
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  );
};
