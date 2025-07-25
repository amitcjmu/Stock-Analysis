/**
 * PendingItemsList Component for Platform Admin Dashboard
 * Displays list of pending purge requests with actions
 */

import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  Building2,
  Briefcase,
  MessageSquare,
  User,
  Trash2,
  RotateCcw,
  Eye,
  CheckCircle
} from 'lucide-react';
import { getItemTypeColor } from '@/components/admin/shared/utils/adminFormatters'
import { formatDate, getItemTypeLabel } from '@/components/admin/shared/utils/adminFormatters'
import type { SoftDeletedItem } from './PlatformStats';

export interface PendingItemsListProps {
  pendingItems: SoftDeletedItem[];
  actionLoading: string | null;
  onViewDetails: (item: SoftDeletedItem) => void;
  onApprove: (item: SoftDeletedItem) => void;
  onReject: (item: SoftDeletedItem) => void;
  className?: string;
}

export const PendingItemsList: React.FC<PendingItemsListProps> = ({
  pendingItems,
  actionLoading,
  onViewDetails,
  onApprove,
  onReject,
  className = ''
}) => {
  const getItemTypeIcon = (itemType: string) => {
    switch (itemType) {
      case 'client_account':
        return <Building2 className="w-4 h-4" />;
      case 'engagement':
        return <Briefcase className="w-4 h-4" />;
      case 'data_import_session':
        return <MessageSquare className="w-4 h-4" />;
      case 'user_profile':
        return <User className="w-4 h-4" />;
      default:
        return <Trash2 className="w-4 h-4" />;
    }
  };

  return (
    <Card className={className}>
      <CardHeader>
        <CardTitle>Pending Purge Requests</CardTitle>
        <CardDescription>
          Review and approve or reject permanent deletion requests from client and engagement admins
        </CardDescription>
      </CardHeader>
      <CardContent>
        {pendingItems.length === 0 ? (
          <div className="text-center py-8">
            <CheckCircle className="w-12 h-12 text-green-500 mx-auto mb-4" />
            <h3 className="text-lg font-medium mb-2">No pending requests</h3>
            <p className="text-muted-foreground">
              All deletion requests have been processed. The platform is up to date.
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            {pendingItems.map((item) => (
              <div key={item.id} className="border rounded-lg p-4 space-y-4">
                <div className="flex items-start justify-between">
                  <div className="flex-1 space-y-2">
                    {/* Item Header */}
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 bg-gray-100 rounded-full flex items-center justify-center">
                        {getItemTypeIcon(item.item_type)}
                      </div>
                      <div>
                        <h4 className="font-medium">{item.item_name}</h4>
                        <div className="flex items-center gap-2">
                          <Badge className={getItemTypeColor(item.item_type)}>
                            {getItemTypeLabel(item.item_type)}
                          </Badge>
                          <span className="text-xs text-muted-foreground">
                            {formatDate(item.deleted_at)}
                          </span>
                        </div>
                      </div>
                    </div>

                    {/* Context Information */}
                    <div className="flex flex-wrap gap-4 text-sm text-muted-foreground">
                      {item.client_account_name && (
                        <div className="flex items-center gap-1">
                          <Building2 className="w-3 h-3" />
                          {item.client_account_name}
                        </div>
                      )}
                      {item.engagement_name && (
                        <div className="flex items-center gap-1">
                          <Briefcase className="w-3 h-3" />
                          {item.engagement_name}
                        </div>
                      )}
                      <div className="flex items-center gap-1">
                        <User className="w-3 h-3" />
                        {item.deleted_by_name} ({item.deleted_by_email})
                      </div>
                    </div>

                    {/* Deletion Reason */}
                    {item.delete_reason && (
                      <div className="bg-gray-50 rounded p-3">
                        <p className="text-sm">
                          <strong>Reason:</strong> {item.delete_reason}
                        </p>
                      </div>
                    )}
                  </div>

                  {/* Action Buttons */}
                  <div className="flex items-center gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => onViewDetails(item)}
                    >
                      <Eye className="w-4 h-4 mr-1" />
                      Details
                    </Button>

                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => onReject(item)}
                      disabled={actionLoading === item.id}
                    >
                      <RotateCcw className="w-4 h-4 mr-1" />
                      Restore
                    </Button>

                    <Button
                      variant="destructive"
                      size="sm"
                      onClick={() => onApprove(item)}
                      disabled={actionLoading === item.id}
                    >
                      {actionLoading === item.id ? (
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                      ) : (
                        <>
                          <Trash2 className="w-4 h-4 mr-1" />
                          Approve Purge
                        </>
                      )}
                    </Button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
};
