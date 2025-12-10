import React from 'react';
import { Link } from 'react-router-dom';
import {
  Calendar,
  Clock,
  Eye,
  Edit,
  Trash2,
  MoreHorizontal,
  Target,
  TrendingUp,
} from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import type { Engagement } from './types';

interface EngagementListProps {
  engagements: Engagement[];
  loading: boolean;
  onEditEngagement: (engagement: Engagement) => void;
  onDeleteEngagement: (engagementId: string, engagementName: string) => void;
  currentPage: number;
  totalPages: number;
  onPageChange: (page: number) => void;
  getPhaseColor: (phase: string) => string;
  formatCurrency: (amount: number, currency: string) => string;
  selectedEngagements: string[];
  onToggleSelection: (engagementId: string) => void;
  onSelectAll: (selected: boolean) => void;
  onBulkDelete: () => void;
  bulkDeleteLoading: boolean;
}

export const EngagementList: React.FC<EngagementListProps> = ({
  engagements,
  loading,
  onEditEngagement,
  onDeleteEngagement,
  currentPage,
  totalPages,
  onPageChange,
  getPhaseColor,
  formatCurrency,
  selectedEngagements,
  onToggleSelection,
  onSelectAll,
  onBulkDelete,
  bulkDeleteLoading,
}) => {
  const allSelected = engagements.length > 0 && selectedEngagements.length === engagements.length;
  const someSelected =
    selectedEngagements.length > 0 && selectedEngagements.length < engagements.length;

  return (
    <>
      {/* Engagements Table */}
      <Card>
        <CardHeader>
          <div className="flex justify-between items-center">
            <div>
              <CardTitle>Active Engagements</CardTitle>
              <CardDescription>
                {engagements.length} engagement{engagements.length !== 1 ? 's' : ''} found
              </CardDescription>
            </div>
            {selectedEngagements.length > 0 && (
              <Button
                variant="destructive"
                onClick={onBulkDelete}
                disabled={bulkDeleteLoading}
              >
                <Trash2 className="mr-2 h-4 w-4" />
                {bulkDeleteLoading
                  ? 'Deleting...'
                  : `Delete (${selectedEngagements.length})`}
              </Button>
            )}
          </div>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex items-center justify-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-12">
                    <Checkbox
                      checked={allSelected}
                      onCheckedChange={onSelectAll}
                      aria-label="Select all"
                      className={someSelected ? 'data-[state=checked]:bg-primary/50' : ''}
                    />
                  </TableHead>
                  <TableHead>Engagement</TableHead>
                  <TableHead>Client</TableHead>
                  <TableHead>Team</TableHead>
                  <TableHead>Timeline</TableHead>
                  <TableHead>Budget</TableHead>
                  <TableHead>Progress</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {engagements.map((engagement) => (
                  <TableRow
                    key={engagement.id}
                    className={selectedEngagements.includes(engagement.id) ? 'bg-muted/50' : ''}
                  >
                    <TableCell>
                      <Checkbox
                        checked={selectedEngagements.includes(engagement.id)}
                        onCheckedChange={() => onToggleSelection(engagement.id)}
                        aria-label={`Select ${engagement.engagement_name || engagement.name}`}
                      />
                    </TableCell>
                    <TableCell>
                      <div>
                        <div className="font-medium">
                          {engagement.engagement_name || engagement.name || 'Unnamed Engagement'}
                        </div>
                        <div className="text-sm text-muted-foreground flex items-center gap-2">
                          {(engagement.migration_phase ||
                            engagement.current_phase ||
                            engagement.status) && (
                            <Badge
                              className={getPhaseColor(
                                engagement.migration_phase ||
                                  engagement.current_phase ||
                                  engagement.status ||
                                  ''
                              )}
                            >
                              {engagement.migration_phase ||
                                engagement.current_phase ||
                                engagement.status ||
                                'Planning'}
                            </Badge>
                          )}
                          <span>
                            {Array.isArray(engagement.migration_scope)
                              ? engagement.migration_scope.join(', ')
                              : engagement.migration_scope || 'Not specified'}
                          </span>
                        </div>
                        <div className="text-sm text-muted-foreground flex items-center">
                          <Target className="w-3 h-3 mr-1" />
                          {engagement.target_cloud_provider
                            ? engagement.target_cloud_provider.toUpperCase()
                            : 'TBD'}
                        </div>
                      </div>
                    </TableCell>
                    <TableCell>
                      <div>
                        <div className="font-medium">{engagement.client_account_name}</div>
                        <div className="text-sm text-muted-foreground">
                          {engagement.total_sessions} sessions
                        </div>
                      </div>
                    </TableCell>
                    <TableCell>
                      <div>
                        <div className="text-sm">
                          <span className="font-medium">EM:</span> {engagement.engagement_manager}
                        </div>
                        <div className="text-sm">
                          <span className="font-medium">TL:</span> {engagement.technical_lead}
                        </div>
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="text-sm">
                        <div className="flex items-center">
                          <Calendar className="w-3 h-3 mr-1" />
                          {engagement.planned_start_date
                            ? new Date(engagement.planned_start_date).toLocaleDateString()
                            : 'Not set'}
                        </div>
                        <div className="flex items-center text-muted-foreground">
                          <Clock className="w-3 h-3 mr-1" />
                          {engagement.planned_end_date
                            ? new Date(engagement.planned_end_date).toLocaleDateString()
                            : 'Not set'}
                        </div>
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="text-sm">
                        <div className="font-medium">
                          {engagement.estimated_budget
                            ? formatCurrency(
                                engagement.estimated_budget,
                                engagement.budget_currency || 'USD'
                              )
                            : 'No budget set'}
                        </div>
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <div className="flex-1 bg-gray-200 rounded-full h-2">
                          <div
                            className="bg-blue-600 h-2 rounded-full"
                            style={{ width: `${engagement.completion_percentage}%` }}
                          ></div>
                        </div>
                        <span className="text-sm font-medium">
                          {engagement.completion_percentage.toFixed(1)}%
                        </span>
                      </div>
                    </TableCell>
                    <TableCell className="text-right">
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" className="h-8 w-8 p-0">
                            <MoreHorizontal className="h-4 w-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuItem asChild>
                            <Link to={`/admin/engagements/${engagement.id}`}>
                              <Eye className="w-4 h-4 mr-2" />
                              View Details
                            </Link>
                          </DropdownMenuItem>
                          <DropdownMenuItem onClick={() => onEditEngagement(engagement)}>
                            <Edit className="w-4 h-4 mr-2" />
                            Edit Engagement
                          </DropdownMenuItem>
                          <DropdownMenuItem asChild>
                            <Link to={`/discovery?engagement=${engagement.id}`}>
                              <TrendingUp className="w-4 h-4 mr-2" />
                              View Progress
                            </Link>
                          </DropdownMenuItem>
                          <DropdownMenuItem
                            onClick={() =>
                              onDeleteEngagement(engagement.id, engagement.engagement_name)
                            }
                            className="text-red-600"
                          >
                            <Trash2 className="w-4 h-4 mr-2" />
                            Delete Engagement
                          </DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex justify-center gap-2">
          <Button
            variant="outline"
            onClick={() => onPageChange(Math.max(1, currentPage - 1))}
            disabled={currentPage === 1}
          >
            Previous
          </Button>
          <span className="flex items-center px-4 text-sm">
            Page {currentPage} of {totalPages}
          </span>
          <Button
            variant="outline"
            onClick={() => onPageChange(Math.min(totalPages, currentPage + 1))}
            disabled={currentPage === totalPages}
          >
            Next
          </Button>
        </div>
      )}
    </>
  );
};
