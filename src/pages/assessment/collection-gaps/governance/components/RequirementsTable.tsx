/**
 * RequirementsTable Component
 * Display governance requirements with action buttons
 */

import React from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Shield, FileText } from 'lucide-react';
import type { GovernanceRequirement } from '../types';
import { getStatusBadgeVariant, getPriorityBadgeVariant } from '../utils/statusHelpers';

interface RequirementsTableProps {
  requirements: GovernanceRequirement[] | undefined;
  isLoading: boolean;
  onRequestException: (requirement: GovernanceRequirement) => void;
}

export const RequirementsTable: React.FC<RequirementsTableProps> = ({
  requirements,
  isLoading,
  onRequestException
}) => {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Shield className="h-5 w-5" />
          Governance Requirements ({requirements?.length || 0})
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
        ) : requirements && requirements.length > 0 ? (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Requirement</TableHead>
                <TableHead>Category</TableHead>
                <TableHead>Priority</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Scope</TableHead>
                <TableHead>Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {requirements.map((requirement) => (
                <TableRow key={requirement.id}>
                  <TableCell>
                    <div className="space-y-1">
                      <div className="font-medium">{requirement.title}</div>
                      <div className="text-sm text-muted-foreground">
                        {requirement.description}
                      </div>
                    </div>
                  </TableCell>
                  <TableCell>
                    <Badge variant="outline" className="capitalize">
                      {requirement.category}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <Badge variant={getPriorityBadgeVariant(requirement.priority)}>
                      {requirement.priority}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <Badge variant={getStatusBadgeVariant(requirement.status)}>
                      {requirement.status}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <div className="flex flex-wrap gap-1">
                      {requirement.applicable_scopes.map((scope) => (
                        <Badge key={scope} variant="outline" className="text-xs">
                          {scope}
                        </Badge>
                      ))}
                    </div>
                  </TableCell>
                  <TableCell>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => onRequestException(requirement)}
                      className="flex items-center gap-1"
                    >
                      <FileText className="h-3 w-3" />
                      Request Exception
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        ) : (
          <div className="p-6 text-center">
            <Shield className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-sm font-medium text-gray-900">No requirements found</h3>
            <p className="mt-1 text-sm text-gray-500">
              No governance requirements are currently defined.
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  );
};
