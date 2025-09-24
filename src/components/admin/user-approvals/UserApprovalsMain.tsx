import React from 'react'
import { useState } from 'react'
import { useEffect, useCallback } from 'react'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Label } from '@/components/ui/label';
import { Button } from '@/components/ui/button';
import { useToast } from '@/components/ui/use-toast';
import { apiCall, clearUserManagementCache } from '@/config/api';
import { useAuth } from '@/contexts/AuthContext';
import { AdminLoadingState, getAccessLevelColor } from '@/components/admin/shared'
import { useAdminToasts, formatDate } from '@/components/admin/shared'

import { UserStats } from './UserStats';
import { UserFilters } from './UserFilters';
import { UserList } from './UserList';
import { UserDetailsModal } from './UserDetailsModal';
import { ApprovalActions } from './ApprovalActions';
import { UserManagementTabs } from './UserManagementTabs';
import type { ApprovalData, RejectionData } from './types'
import type { PendingUser, ActiveUser } from './types'

export const UserApprovalsMain: React.FC = () => {
  const { getAuthHeaders } = useAuth();
  const { toast } = useToast();
  const {
    showUserApprovedToast,
    showUserRejectedToast,
    showUserDeactivatedToast,
    showUserActivatedToast,
    showGenericErrorToast,
    showDataFetchErrorToast
  } = useAdminToasts();
  const [pendingUsers, setPendingUsers] = useState<PendingUser[]>([]);
  const [activeUsers, setActiveUsers] = useState<ActiveUser[]>([]);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [selectedUser, setSelectedUser] = useState<PendingUser | null>(null);
  const [showApprovalDialog, setShowApprovalDialog] = useState(false);
  const [showRejectionDialog, setShowRejectionDialog] = useState(false);
  const [showDetailsDialog, setShowDetailsDialog] = useState(false);
  const [activeTab, setActiveTab] = useState<'pending' | 'active' | 'access'>('pending');

  // Approval form state
  const [approvalData, setApprovalData] = useState<ApprovalData>({
    access_level: 'read_only',
    role_name: 'Analyst',
    client_access: [],
    notes: ''
  });

  // Rejection form state
  const [rejectionData, setRejectionData] = useState<RejectionData>({
    rejection_reason: ''
  });

  // Define fetch functions before they're used to avoid temporal dead zone
  const fetchPendingUsers = useCallback(async () => {
    try {
      setLoading(true);
      const response = await apiCall('/auth/pending-approvals', {}, false);

      if (response.status === 'success') {
        setPendingUsers(response.pending_approvals || []);
      } else {
        console.warn('Failed to load pending users from API:', response.message);
        setPendingUsers([]);
      }
    } catch (error) {
      console.error('Error fetching pending users:', error);
      showDataFetchErrorToast();
    } finally {
      setLoading(false);
    }
  }, []); // Remove showDataFetchErrorToast dependency - it's memoized in useAdminToasts

  const fetchActiveUsers = useCallback(async () => {
    try {
      const response = await apiCall('/auth/active-users', {}, false);

      if (response.status === 'success') {
        setActiveUsers(response.active_users || []);
      } else {
        console.warn('Failed to load active users from API:', response.message);
        setActiveUsers([]);
      }
    } catch (error) {
      console.error('Error fetching active users:', error);
      showDataFetchErrorToast();
    }
  }, []); // Remove showDataFetchErrorToast dependency - it's memoized in useAdminToasts

  // Initialize data on component mount
  useEffect(() => {
    fetchPendingUsers();
    fetchActiveUsers();
  }, [fetchPendingUsers, fetchActiveUsers]); // Include function dependencies

  useEffect(() => {
    // Listen for user creation events
    const handleUserCreated = (event: CustomEvent): void => {
      console.log('User created event received:', event.detail);
      // Refresh the user lists
      fetchPendingUsers();
      fetchActiveUsers();

      toast({
        title: "User Created",
        description: "New user has been created successfully",
        variant: "default"
      }, false);
    };

    // Add event listener
    window.addEventListener('userCreated', handleUserCreated as EventListener);

    // Cleanup
    return () => {
      window.removeEventListener('userCreated', handleUserCreated as EventListener);
    };
  }, [toast, fetchPendingUsers, fetchActiveUsers]);

  const handleApprove = async (): void => {
    if (!selectedUser) return;

    try {
      setActionLoading(selectedUser.user_id);

      const response = await apiCall('/auth/approve-user', {
        method: 'POST',
        body: JSON.stringify({
          user_id: selectedUser.user_id,
          access_level: approvalData.access_level,
          role_name: approvalData.role_name,
          client_access: approvalData.client_access,
          notes: approvalData.notes
        })
      }, false);

      if (response.status === 'success') {
        showUserApprovedToast(selectedUser.full_name);

        // Clear cache to ensure fresh data
        clearUserManagementCache();

        // Remove from pending users
        setPendingUsers(prev => prev.filter(u => u.user_id !== selectedUser.user_id));

        // Add to active users
        const newActiveUser: ActiveUser = {
          user_id: selectedUser.user_id,
          email: selectedUser.email,
          full_name: selectedUser.full_name,
          username: selectedUser.username,
          organization: selectedUser.organization,
          role_description: selectedUser.role_description,
          access_level: approvalData.access_level,
          role_name: approvalData.role_name,
          is_active: true,
          approved_at: new Date().toISOString(),
          last_login: undefined
        };
        setActiveUsers(prev => [...prev, newActiveUser]);

        setShowApprovalDialog(false);
        setSelectedUser(null);
        setApprovalData({
          access_level: 'read_only',
          role_name: 'Analyst',
          client_access: [],
          notes: ''
        });

        // Reload data to ensure consistency
        await Promise.all([fetchPendingUsers(), fetchActiveUsers()]);
      } else {
        throw new Error(response.message || 'Failed to approve user');
      }
    } catch (error) {
      console.error('Error approving user:', error);
      showGenericErrorToast('approve user');
    } finally {
      setActionLoading(null);
    }
  };

  const handleReject = async (): Promise<void> => {
    if (!selectedUser || !rejectionData.rejection_reason || rejectionData.rejection_reason.length < 10) {
      return;
    }

    try {
      setActionLoading(selectedUser.user_id);

      const response = await apiCall('/auth/reject-user', {
        method: 'POST',
        body: JSON.stringify({
          user_id: selectedUser.user_id,
          rejection_reason: rejectionData.rejection_reason
        })
      }, false);

      if (response.status === 'success') {
        showUserRejectedToast(selectedUser.full_name);

        // Clear cache to ensure fresh data
        clearUserManagementCache();

        // Remove from pending users
        setPendingUsers(prev => prev.filter(u => u.user_id !== selectedUser.user_id));

        setShowRejectionDialog(false);
        setSelectedUser(null);
        setRejectionData({ rejection_reason: '' });

        // Reload data to ensure consistency
        await fetchPendingUsers();
      } else {
        throw new Error(response.message || 'Failed to reject user');
      }
    } catch (error) {
      console.error('Error rejecting user:', error);
      showGenericErrorToast('reject user');
    } finally {
      setActionLoading(null);
    }
  };

  const handleDeactivateUser = async (user: ActiveUser): void => {
    try {
      setActionLoading(user.user_id);

      const response = await apiCall('/auth/deactivate-user', {
        method: 'POST',
        body: JSON.stringify({
          user_id: user.user_id,
          reason: "Deactivated by admin"
        })
      }, false);

      if (response.status === 'success') {
        showUserDeactivatedToast(user.full_name);

        // Clear cache to ensure fresh data
        clearUserManagementCache();

        // Update user status
        setActiveUsers(prev => prev.map(u =>
          u.user_id === user.user_id ? { ...u, is_active: false } : u
        ));

        // Reload data to ensure consistency
        await fetchActiveUsers();
      } else {
        throw new Error(response.message || 'Failed to deactivate user');
      }
    } catch (error) {
      console.error('Error deactivating user:', error);
      showGenericErrorToast('deactivate user');
    } finally {
      setActionLoading(null);
    }
  };

  const handleActivateUser = async (user: ActiveUser): void => {
    try {
      setActionLoading(user.user_id);

      const response = await apiCall('/auth/activate-user', {
        method: 'POST',
        body: JSON.stringify({
          user_id: user.user_id
        })
      }, false);

      if (response.status === 'success') {
        showUserActivatedToast(user.full_name);

        // Clear cache to ensure fresh data
        clearUserManagementCache();

        // Update user status
        setActiveUsers(prev => prev.map(u =>
          u.user_id === user.user_id ? { ...u, is_active: true } : u
        ));

        // Reload data to ensure consistency
        await fetchActiveUsers();
      } else {
        throw new Error(response.message || 'Failed to activate user');
      }
    } catch (error) {
      console.error('Error activating user:', error);
      showGenericErrorToast('activate user');
    } finally {
      setActionLoading(null);
    }
  };

  // formatDate and getAccessLevelColor functions moved to shared utilities

  const handleViewDetails = (user: PendingUser): void => {
    setSelectedUser(user);
    setShowDetailsDialog(true);
  };

  const handleApproveUser = (user: PendingUser): void => {
    setSelectedUser(user);
    setApprovalData({
      access_level: user.requested_access_level,
      role_name: user.role_description,
      client_access: [],
      notes: ''
    });
    setShowApprovalDialog(true);
  };

  const handleRejectUser = (user: PendingUser): void => {
    setSelectedUser(user);
    setShowRejectionDialog(true);
  };

  const handleEditAccess = (user: ActiveUser): void => {
    // For now, show a toast indicating this feature is coming soon
    // In a full implementation, this would open a modal to edit user permissions
    toast({
      title: "Edit Access",
      description: `Edit access for ${user.full_name} - Feature coming soon`,
      variant: "default"
    });
  };

  if (loading) {
    return <AdminLoadingState message="Loading User Management..." fullScreen />;
  }

  return (
    <div className="space-y-6">
      <UserFilters
        activeTab={activeTab}
        pendingUsersCount={pendingUsers.length}
        activeUsersCount={activeUsers.length}
        onTabChange={setActiveTab}
      />

      {activeTab !== 'access' && (
        <UserStats
          pendingUsers={pendingUsers}
          activeUsers={activeUsers}
        />
      )}

      {activeTab === 'access' ? (
        <UserManagementTabs />
      ) : (
        <UserList
          activeTab={activeTab}
          pendingUsers={pendingUsers}
          activeUsers={activeUsers}
          actionLoading={actionLoading}
          onViewDetails={handleViewDetails}
          onApprove={handleApproveUser}
          onReject={handleRejectUser}
          onDeactivateUser={handleDeactivateUser}
          onActivateUser={handleActivateUser}
          onEditAccess={handleEditAccess}
          formatDate={formatDate}
          getAccessLevelColor={getAccessLevelColor}
        />
      )}

      {/* User Details Dialog */}
      <UserDetailsModal
        user={selectedUser}
        isOpen={showDetailsDialog}
        onClose={() => setShowDetailsDialog(false)}
        formatDate={formatDate}
        getAccessLevelColor={getAccessLevelColor}
      />

      {/* Approval Dialog */}
      <Dialog open={showApprovalDialog} onOpenChange={setShowApprovalDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Approve User Access</DialogTitle>
            <DialogDescription>
              Configure access settings for {selectedUser?.full_name}
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4">
            <div>
              <Label htmlFor="access-level">Access Level</Label>
              <Select value={approvalData.access_level} onValueChange={(value) =>
                setApprovalData(prev => ({ ...prev, access_level: value }))
              }>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="read_only">Read Only</SelectItem>
                  <SelectItem value="read_write">Read & Write</SelectItem>
                  <SelectItem value="admin">Administrator</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div>
              <Label htmlFor="role-name">Role Name</Label>
              <Select value={approvalData.role_name} onValueChange={(value) =>
                setApprovalData(prev => ({ ...prev, role_name: value }))
              }>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="Analyst">Analyst</SelectItem>
                  <SelectItem value="Project Manager">Project Manager</SelectItem>
                  <SelectItem value="Architect">Architect</SelectItem>
                  <SelectItem value="Administrator">Administrator</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div>
              <Label htmlFor="notes">Approval Notes (Optional)</Label>
              <Textarea
                id="notes"
                placeholder="Add any notes about this approval..."
                value={approvalData.notes}
                onChange={(e) => setApprovalData(prev => ({ ...prev, notes: e.target.value }))}
              />
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setShowApprovalDialog(false)}>
              Cancel
            </Button>
            <Button onClick={handleApprove} disabled={actionLoading === selectedUser?.user_id}>
              {actionLoading === selectedUser?.user_id ? 'Approving...' : 'Approve User'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Rejection Dialog */}
      <Dialog open={showRejectionDialog} onOpenChange={setShowRejectionDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Reject User Access</DialogTitle>
            <DialogDescription>
              Provide a reason for rejecting {selectedUser?.full_name}'s request
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4">
            <div>
              <Label htmlFor="rejection-reason">Rejection Reason *</Label>
              <Textarea
                id="rejection-reason"
                placeholder="Please explain why this request is being rejected (minimum 10 characters)..."
                value={rejectionData.rejection_reason}
                onChange={(e) => setRejectionData(prev => ({ ...prev, rejection_reason: e.target.value }))}
                required
              />
              {rejectionData.rejection_reason && rejectionData.rejection_reason.length < 10 && (
                <p className="text-sm text-red-500 mt-1">
                  Rejection reason must be at least 10 characters ({rejectionData.rejection_reason.length}/10)
                </p>
              )}
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setShowRejectionDialog(false)}>
              Cancel
            </Button>
            <Button
              variant="destructive"
              onClick={handleReject}
              disabled={!rejectionData.rejection_reason || rejectionData.rejection_reason.length < 10 || actionLoading === selectedUser?.user_id}
            >
              {actionLoading === selectedUser?.user_id ? 'Rejecting...' : 'Reject Request'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};
