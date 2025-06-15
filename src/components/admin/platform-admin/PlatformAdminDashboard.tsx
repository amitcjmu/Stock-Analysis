/**
 * Platform Admin Dashboard - Manages soft-deleted items and purge approvals
 * Only accessible by platform administrators
 */

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Textarea } from '@/components/ui/textarea';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { useToast } from '@/components/ui/use-toast';
import { 
  Trash2, 
  RotateCcw, 
  Eye, 
  AlertTriangle, 
  Building2, 
  Briefcase, 
  User,
  Calendar,
  MessageSquare,
  CheckCircle,
  XCircle,
  Clock
} from 'lucide-react';
import { apiCall } from '@/config/api';
import { useAuth } from '@/contexts/AuthContext';

interface SoftDeletedItem {
  id: string;
  item_type: string;
  item_id: string;
  item_name: string;
  client_account_name?: string;
  engagement_name?: string;
  deleted_by_name: string;
  deleted_by_email: string;
  deleted_at: string;
  delete_reason?: string;
  status: string;
}

interface PurgeAction {
  action: 'approve' | 'reject';
  item: SoftDeletedItem;
  notes: string;
}

export const PlatformAdminDashboard: React.FC = () => {
  const { getAuthHeaders } = useAuth();
  const { toast } = useToast();
  
  const [pendingItems, setPendingItems] = useState<SoftDeletedItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [selectedItem, setSelectedItem] = useState<SoftDeletedItem | null>(null);
  const [showPurgeDialog, setShowPurgeDialog] = useState(false);
  const [purgeAction, setPurgeAction] = useState<PurgeAction | null>(null);
  
  useEffect(() => {
    fetchPendingItems();
  }, []);
  
  const fetchPendingItems = async () => {
    try {
      setLoading(true);
      const response = await apiCall('platform-admin/pending-purge-items', {
        headers: getAuthHeaders()
      });
      
      if (response.status === 'success') {
        setPendingItems(response.pending_items || []);
      } else {
        // Demo data fallback
        setPendingItems([
          {
            id: 'item_001',
            item_type: 'client_account',
            item_id: 'client_001',
            item_name: 'Legacy Systems Corp',
            client_account_name: 'Legacy Systems Corp',
            engagement_name: null,
            deleted_by_name: 'John Admin',
            deleted_by_email: 'john.admin@company.com',
            deleted_at: '2025-01-05T14:30:00Z',
            delete_reason: 'Client requested account closure after migration completion',
            status: 'pending_review'
          },
          {
            id: 'item_002',
            item_type: 'engagement',
            item_id: 'engagement_001',
            item_name: 'Cloud Migration Phase 1',
            client_account_name: 'TechCorp Solutions',
            engagement_name: 'Cloud Migration Phase 1',
            deleted_by_name: 'Sarah Manager',
            deleted_by_email: 'sarah.manager@techcorp.com',
            deleted_at: '2025-01-04T09:15:00Z',
            delete_reason: 'Project completed successfully, archiving engagement data',
            status: 'pending_review'
          },
          {
            id: 'item_003',
            item_type: 'data_import_session',
            item_id: 'session_001',
            item_name: 'Asset Discovery Import #15',
            client_account_name: 'Global Systems Inc',
            engagement_name: 'Infrastructure Modernization',
            deleted_by_name: 'Mike Analyst',
            deleted_by_email: 'mike.analyst@globalsystems.com',
            deleted_at: '2025-01-03T16:45:00Z',
            delete_reason: 'Duplicate data import, cleaned up incorrect session',
            status: 'pending_review'
          }
        ]);
      }
    } catch (error) {
      console.error('Error fetching pending items:', error);
      toast({
        title: "Error",
        description: "Failed to fetch pending purge items",
        variant: "destructive"
      });
    } finally {
      setLoading(false);
    }
  };
  
  const handleViewDetails = (item: SoftDeletedItem) => {
    setSelectedItem(item);
  };
  
  const handleApprovePurge = (item: SoftDeletedItem) => {
    setPurgeAction({
      action: 'approve',
      item: item,
      notes: ''
    });
    setShowPurgeDialog(true);
  };
  
  const handleRejectPurge = (item: SoftDeletedItem) => {
    setPurgeAction({
      action: 'reject',
      item: item,
      notes: ''
    });
    setShowPurgeDialog(true);
  };
  
  const executePurgeAction = async () => {
    if (!purgeAction) return;
    
    try {
      setActionLoading(purgeAction.item.id);
      
      const endpoint = purgeAction.action === 'approve' 
        ? '/api/v1/platform-admin/approve-purge'
        : '/api/v1/platform-admin/reject-purge';
      
      const response = await apiCall(endpoint, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({
          soft_delete_id: purgeAction.item.id,
          notes: purgeAction.notes
        })
      });
      
      if (response.status === 'success') {
        toast({
          title: purgeAction.action === 'approve' ? "Purge Approved" : "Purge Rejected",
          description: response.message,
          variant: "default"
        });
        
        // Remove item from list
        setPendingItems(prev => prev.filter(item => item.id !== purgeAction.item.id));
        setShowPurgeDialog(false);
        setPurgeAction(null);
      } else {
        throw new Error(response.message || 'Action failed');
      }
    } catch (error) {
      console.error('Error executing purge action:', error);
      toast({
        title: "Error",
        description: `Failed to ${purgeAction.action} purge request`,
        variant: "destructive"
      });
    } finally {
      setActionLoading(null);
    }
  };
  
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
  
  const getItemTypeLabel = (itemType: string) => {
    return itemType.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
  };
  
  const getItemTypeColor = (itemType: string) => {
    switch (itemType) {
      case 'client_account':
        return 'bg-red-100 text-red-800';
      case 'engagement':
        return 'bg-blue-100 text-blue-800';
      case 'data_import_session':
        return 'bg-green-100 text-green-800';
      case 'user_profile':
        return 'bg-purple-100 text-purple-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };
  
  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };
  
  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    );
  }
  
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Platform Administration</h1>
          <p className="text-muted-foreground">Manage soft-deleted items and purge approvals</p>
        </div>
        <Button onClick={fetchPendingItems} variant="outline">
          <RotateCcw className="w-4 h-4 mr-2" />
          Refresh
        </Button>
      </div>
      
      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Pending Reviews</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{pendingItems.length}</div>
            <p className="text-xs text-muted-foreground">awaiting your approval</p>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">High Priority</CardTitle>
            <AlertTriangle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {pendingItems.filter(item => item.item_type === 'client_account').length}
            </div>
            <p className="text-xs text-muted-foreground">client account deletions</p>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Recent Activity</CardTitle>
            <Calendar className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {pendingItems.filter(item => {
                const deletedDate = new Date(item.deleted_at);
                const yesterday = new Date();
                yesterday.setDate(yesterday.getDate() - 1);
                return deletedDate > yesterday;
              }).length}
            </div>
            <p className="text-xs text-muted-foreground">deleted in last 24h</p>
          </CardContent>
        </Card>
      </div>
      
      {/* Pending Items List */}
      <Card>
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
                        onClick={() => handleViewDetails(item)}
                      >
                        <Eye className="w-4 h-4 mr-1" />
                        Details
                      </Button>
                      
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleRejectPurge(item)}
                        disabled={actionLoading === item.id}
                      >
                        <RotateCcw className="w-4 h-4 mr-1" />
                        Restore
                      </Button>
                      
                      <Button
                        variant="destructive"
                        size="sm"
                        onClick={() => handleApprovePurge(item)}
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
      
      {/* Purge Action Dialog */}
      <Dialog open={showPurgeDialog} onOpenChange={setShowPurgeDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>
              {purgeAction?.action === 'approve' ? 'Approve Permanent Deletion' : 'Reject Deletion and Restore'}
            </DialogTitle>
            <DialogDescription>
              {purgeAction?.action === 'approve' 
                ? `You are about to permanently delete "${purgeAction?.item.item_name}". This action cannot be undone.`
                : `You are about to restore "${purgeAction?.item.item_name}" and reject the deletion request.`
              }
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4">
            {/* Item Summary */}
            <div className="bg-gray-50 rounded p-3 space-y-2">
              <div className="flex items-center gap-2">
                <Badge className={getItemTypeColor(purgeAction?.item.item_type || '')}>
                  {getItemTypeLabel(purgeAction?.item.item_type || '')}
                </Badge>
                <span className="font-medium">{purgeAction?.item.item_name}</span>
              </div>
              <p className="text-sm text-muted-foreground">
                Deleted by {purgeAction?.item.deleted_by_name} on {purgeAction?.item.deleted_at ? formatDate(purgeAction.item.deleted_at) : ''}
              </p>
              {purgeAction?.item.delete_reason && (
                <p className="text-sm">
                  <strong>Original reason:</strong> {purgeAction.item.delete_reason}
                </p>
              )}
            </div>
            
            {/* Admin Notes */}
            <div>
              <label htmlFor="admin-notes" className="block text-sm font-medium mb-2">
                Admin Notes {purgeAction?.action === 'approve' ? '(Optional)' : '(Required)'}
              </label>
              <Textarea
                id="admin-notes"
                placeholder={purgeAction?.action === 'approve' 
                  ? "Add any notes about this approval..."
                  : "Explain why this deletion is being rejected..."
                }
                value={purgeAction?.notes || ''}
                onChange={(e) => setPurgeAction(prev => prev ? { ...prev, notes: e.target.value } : null)}
                required={purgeAction?.action === 'reject'}
              />
            </div>
          </div>
          
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowPurgeDialog(false)}>
              Cancel
            </Button>
            <Button 
              variant={purgeAction?.action === 'approve' ? "destructive" : "default"}
              onClick={executePurgeAction}
              disabled={purgeAction?.action === 'reject' && !purgeAction?.notes?.trim()}
            >
              {purgeAction?.action === 'approve' ? (
                <>
                  <Trash2 className="w-4 h-4 mr-2" />
                  Permanently Delete
                </>
              ) : (
                <>
                  <RotateCcw className="w-4 h-4 mr-2" />
                  Restore Item
                </>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
      
      {/* Item Details Dialog */}
      {selectedItem && (
        <Dialog open={!!selectedItem} onOpenChange={() => setSelectedItem(null)}>
          <DialogContent className="max-w-2xl">
            <DialogHeader>
              <DialogTitle>Deletion Request Details</DialogTitle>
              <DialogDescription>
                Complete information about this deletion request
              </DialogDescription>
            </DialogHeader>
            
            <div className="space-y-4">
              {/* Item Information */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium">Item Type</label>
                  <p className="text-sm text-muted-foreground">
                    {getItemTypeLabel(selectedItem.item_type)}
                  </p>
                </div>
                <div>
                  <label className="text-sm font-medium">Item Name</label>
                  <p className="text-sm text-muted-foreground">{selectedItem.item_name}</p>
                </div>
                <div>
                  <label className="text-sm font-medium">Deleted By</label>
                  <p className="text-sm text-muted-foreground">
                    {selectedItem.deleted_by_name}<br />
                    <span className="text-xs">{selectedItem.deleted_by_email}</span>
                  </p>
                </div>
                <div>
                  <label className="text-sm font-medium">Deletion Date</label>
                  <p className="text-sm text-muted-foreground">
                    {formatDate(selectedItem.deleted_at)}
                  </p>
                </div>
              </div>
              
              {/* Context */}
              {(selectedItem.client_account_name || selectedItem.engagement_name) && (
                <div>
                  <label className="text-sm font-medium">Context</label>
                  <div className="space-y-1 text-sm text-muted-foreground">
                    {selectedItem.client_account_name && (
                      <p>Client: {selectedItem.client_account_name}</p>
                    )}
                    {selectedItem.engagement_name && (
                      <p>Engagement: {selectedItem.engagement_name}</p>
                    )}
                  </div>
                </div>
              )}
              
              {/* Deletion Reason */}
              {selectedItem.delete_reason && (
                <div>
                  <label className="text-sm font-medium">Deletion Reason</label>
                  <div className="bg-gray-50 rounded p-3 mt-1">
                    <p className="text-sm">{selectedItem.delete_reason}</p>
                  </div>
                </div>
              )}
            </div>
            
            <DialogFooter>
              <Button variant="outline" onClick={() => setSelectedItem(null)}>
                Close
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      )}
    </div>
  );
}; 