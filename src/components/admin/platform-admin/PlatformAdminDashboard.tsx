/**
 * Platform Admin Dashboard - Manages soft-deleted items and purge approvals
 * Only accessible by platform administrators
 */

import React, { useState, useEffect, useCallback } from 'react';
import { apiCall } from '@/config/api';
import { useAuth } from '@/contexts/AuthContext';
import { 
  AdminHeader,
  AdminLoadingState
} from '@/components/admin/shared/components';
import { 
  useAdminToasts
} from '@/components/admin/shared';
import {
  PlatformStats,
  PendingItemsList,
  PurgeActionDialog,
  ItemDetailsDialog,
  SoftDeletedItem,
  PurgeAction
} from './components';

// Interfaces moved to components folder

export const PlatformAdminDashboard: React.FC = () => {
  const { getAuthHeaders } = useAuth();
  const { 
    showPurgeApprovedToast, 
    showPurgeRejectedToast, 
    showGenericErrorToast 
  } = useAdminToasts();
  
  const [pendingItems, setPendingItems] = useState<SoftDeletedItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [selectedItem, setSelectedItem] = useState<SoftDeletedItem | null>(null);
  const [showPurgeDialog, setShowPurgeDialog] = useState(false);
  const [purgeAction, setPurgeAction] = useState<PurgeAction | null>(null);
  
  const fetchPendingItems = useCallback(async () => {
    try {
      setLoading(true);
      const response = await apiCall('admin/platform/platform-admin/pending-purge-items', {
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
      showGenericErrorToast('fetch pending purge items');
    } finally {
      setLoading(false);
    }
  }, [getAuthHeaders, showGenericErrorToast]);

  useEffect(() => {
    fetchPendingItems();
  }, [fetchPendingItems]);
  
  // fetchPendingItems moved above with useCallback
  
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
        ? 'admin/platform/platform-admin/approve-purge'
        : 'admin/platform/platform-admin/reject-purge';
      
      const response = await apiCall(endpoint, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({
          soft_delete_id: purgeAction.item.id,
          notes: purgeAction.notes
        })
      });
      
      if (response.status === 'success') {
        if (purgeAction.action === 'approve') {
          showPurgeApprovedToast(response.message);
        } else {
          showPurgeRejectedToast(response.message);
        }
        
        // Remove item from list
        setPendingItems(prev => prev.filter(item => item.id !== purgeAction.item.id));
        setShowPurgeDialog(false);
        setPurgeAction(null);
      } else {
        throw new Error(response.message || 'Action failed');
      }
    } catch (error) {
      console.error('Error executing purge action:', error);
      showGenericErrorToast(`${purgeAction.action} purge request`);
    } finally {
      setActionLoading(null);
    }
  };
  
  // Utility functions moved to shared/utils/adminFormatters
  
  if (loading) {
    return <AdminLoadingState message="Loading Platform Administration..." fullScreen />;
  }
  
  return (
    <div className="space-y-6">
      {/* Header */}
      <AdminHeader
        title="Platform Administration"
        description="Manage soft-deleted items and purge approvals"
        onRefresh={fetchPendingItems}
        refreshLoading={loading}
      />
      
      {/* Stats */}
      <PlatformStats pendingItems={pendingItems} />
      
      {/* Pending Items List */}
      <PendingItemsList
        pendingItems={pendingItems}
        actionLoading={actionLoading}
        onViewDetails={handleViewDetails}
        onApprove={handleApprovePurge}
        onReject={handleRejectPurge}
      />
      
      {/* Purge Action Dialog */}
      <PurgeActionDialog
        isOpen={showPurgeDialog}
        purgeAction={purgeAction}
        onClose={() => setShowPurgeDialog(false)}
        onExecute={executePurgeAction}
        onNotesChange={(notes) => setPurgeAction(prev => prev ? { ...prev, notes } : null)}
      />
      
      {/* Item Details Dialog */}
      <ItemDetailsDialog
        item={selectedItem}
        isOpen={!!selectedItem}
        onClose={() => setSelectedItem(null)}
      />
    </div>
  );
}; 