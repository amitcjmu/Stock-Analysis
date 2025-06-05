import React, { useState, useEffect } from 'react';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Label } from '@/components/ui/label';
import { Button } from '@/components/ui/button';
import { useToast } from '@/components/ui/use-toast';
import { apiCall } from '@/config/api';
import { useAuth } from '@/contexts/AuthContext';

import { UserStats } from './UserStats';
import { UserFilters } from './UserFilters';
import { UserList } from './UserList';
import { UserDetailsModal } from './UserDetailsModal';
import { ApprovalActions } from './ApprovalActions';
import { PendingUser, ActiveUser, ApprovalData, RejectionData } from './types';

export const UserApprovalsMain: React.FC = () => {
  const { getAuthHeaders } = useAuth();
  const { toast } = useToast();
  const [pendingUsers, setPendingUsers] = useState<PendingUser[]>([]);
  const [activeUsers, setActiveUsers] = useState<ActiveUser[]>([]);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [selectedUser, setSelectedUser] = useState<PendingUser | null>(null);
  const [showApprovalDialog, setShowApprovalDialog] = useState(false);
  const [showRejectionDialog, setShowRejectionDialog] = useState(false);
  const [showDetailsDialog, setShowDetailsDialog] = useState(false);
  const [activeTab, setActiveTab] = useState<'pending' | 'active'>('pending');

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

  useEffect(() => {
    fetchPendingUsers();
    fetchActiveUsers();
  }, []);

  useEffect(() => {
    // Listen for user creation events
    const handleUserCreated = (event: CustomEvent) => {
      console.log('User created event received:', event.detail);
      // Refresh the user lists
      fetchPendingUsers();
      fetchActiveUsers();
      
      toast({
        title: "User Created",
        description: "New user has been created successfully",
        variant: "default"
      });
    };

    // Add event listener
    window.addEventListener('userCreated', handleUserCreated as EventListener);

    // Cleanup
    return () => {
      window.removeEventListener('userCreated', handleUserCreated as EventListener);
    };
  }, [toast]);

  const fetchPendingUsers = async () => {
    try {
      setLoading(true);
      const response = await apiCall('/api/v1/auth/pending-approvals', {
        headers: getAuthHeaders()
      });

      if (response.status === 'success') {
        setPendingUsers(response.pending_approvals || []);
      } else {
        // Demo data fallback
        setPendingUsers([
          {
            user_id: 'user_001',
            email: 'john.analyst@techcorp.com',
            full_name: 'John Analyst',
            username: 'john.analyst',
            organization: 'TechCorp Solutions',
            role_description: 'Senior Data Analyst',
            registration_reason: 'Need access to analyze migration readiness for our application portfolio. Will be working on cloud migration assessment project.',
            requested_access_level: 'read_write',
            phone_number: '+1-555-0123',
            manager_email: 'manager@techcorp.com',
            registration_requested_at: '2025-01-02T10:30:00Z',
            status: 'pending_approval'
          },
          {
            user_id: 'user_002',
            email: 'sarah.pm@globalsystems.com',
            full_name: 'Sarah Project Manager',
            username: 'sarah.pm',
            organization: 'Global Systems Inc',
            role_description: 'Migration Project Manager',
            registration_reason: 'Leading enterprise cloud migration initiative. Need platform access to coordinate migration activities and track progress.',
            requested_access_level: 'admin',
            phone_number: '+1-555-0456',
            registration_requested_at: '2025-01-01T14:15:00Z',
            status: 'pending_approval'
          },
          {
            user_id: 'user_003',
            email: 'mike.consultant@cloudexperts.com',
            full_name: 'Mike Consultant',
            username: 'mike.consultant',
            organization: 'Cloud Experts Consulting',
            role_description: 'Senior Cloud Architect',
            registration_reason: 'External consultant supporting client migration project. Need access to review application assessments and provide recommendations.',
            requested_access_level: 'read_only',
            registration_requested_at: '2025-01-02T08:45:00Z',
            status: 'pending_approval'
          }
        ]);
      }
    } catch (error) {
      console.error('Error fetching pending users:', error);
      toast({
        title: "Error",
        description: "Failed to fetch pending user approvals",
        variant: "destructive"
      });
    } finally {
      setLoading(false);
    }
  };

  const fetchActiveUsers = async () => {
    try {
      const response = await apiCall('/api/v1/auth/active-users', {
        headers: getAuthHeaders()
      });

      if (response.status === 'success') {
        setActiveUsers(response.active_users || []);
      } else {
        // Enhanced demo active users with more realistic data
        setActiveUsers([
          {
            user_id: '2a0de3df-7484-4fab-98b9-2ca126e2ab21',
            email: 'admin@aiforce.com',
            full_name: 'Platform Administrator',
            username: 'admin',
            organization: 'AI Force Platform',
            role_description: 'System Administrator',
            access_level: 'admin',
            role_name: 'Administrator',
            is_active: true,
            approved_at: '2025-01-01T00:00:00Z',
            last_login: '2025-01-28T10:30:00Z'
          },
          {
            user_id: 'demo-user-12345678-1234-5678-9012-123456789012',
            email: 'user@demo.com',
            full_name: 'Demo User',
            username: 'demo_user',
            organization: 'Demo Organization',
            role_description: 'Demo Analyst',
            access_level: 'read_write',
            role_name: 'Analyst',
            is_active: true,
            approved_at: '2025-01-01T12:00:00Z',
            last_login: '2025-01-28T09:15:00Z'
          }
        ]);
      }
    } catch (error) {
      console.error('Error fetching active users:', error);
      toast({
        title: "Error",
        description: "Failed to fetch active users",
        variant: "destructive"
      });
    }
  };

  const handleApprove = async () => {
    if (!selectedUser) return;

    try {
      setActionLoading(selectedUser.user_id);
      
      const response = await apiCall('/api/v1/auth/approve-user', {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({
          user_id: selectedUser.user_id,
          access_level: approvalData.access_level,
          role_name: approvalData.role_name,
          client_access: approvalData.client_access,
          notes: approvalData.notes
        })
      });

      if (response.status === 'success') {
        toast({
          title: "User Approved",
          description: `${selectedUser.full_name} has been approved and granted access`,
          variant: "default"
        });

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
      } else {
        throw new Error(response.message || 'Failed to approve user');
      }
    } catch (error) {
      console.error('Error approving user:', error);
      toast({
        title: "Error",
        description: "Failed to approve user. Please try again.",
        variant: "destructive"
      });
    } finally {
      setActionLoading(null);
    }
  };

  const handleReject = async () => {
    if (!selectedUser || !rejectionData.rejection_reason || rejectionData.rejection_reason.length < 10) {
      return;
    }

    try {
      setActionLoading(selectedUser.user_id);
      
      const response = await apiCall('/api/v1/auth/reject-user', {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({
          user_id: selectedUser.user_id,
          rejection_reason: rejectionData.rejection_reason
        })
      });

      if (response.status === 'success') {
        toast({
          title: "User Rejected",
          description: `${selectedUser.full_name}'s request has been rejected`,
          variant: "default"
        });

        // Remove from pending users
        setPendingUsers(prev => prev.filter(u => u.user_id !== selectedUser.user_id));

        setShowRejectionDialog(false);
        setSelectedUser(null);
        setRejectionData({ rejection_reason: '' });
      } else {
        throw new Error(response.message || 'Failed to reject user');
      }
    } catch (error) {
      console.error('Error rejecting user:', error);
      toast({
        title: "Error",
        description: "Failed to reject user. Please try again.",
        variant: "destructive"
      });
    } finally {
      setActionLoading(null);
    }
  };

  const handleDeactivateUser = async (user: ActiveUser) => {
    try {
      setActionLoading(user.user_id);
      
      const response = await apiCall('/api/v1/auth/deactivate-user', {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({
          user_id: user.user_id
        })
      });

      if (response.status === 'success') {
        toast({
          title: "User Deactivated",
          description: `${user.full_name} has been deactivated`,
          variant: "default"
        });

        // Update user status
        setActiveUsers(prev => prev.map(u => 
          u.user_id === user.user_id ? { ...u, is_active: false } : u
        ));
      } else {
        throw new Error(response.message || 'Failed to deactivate user');
      }
    } catch (error) {
      console.error('Error deactivating user:', error);
      toast({
        title: "Error",
        description: "Failed to deactivate user. Please try again.",
        variant: "destructive"
      });
    } finally {
      setActionLoading(null);
    }
  };

  const handleActivateUser = async (user: ActiveUser) => {
    try {
      setActionLoading(user.user_id);
      
      const response = await apiCall('/api/v1/auth/activate-user', {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({
          user_id: user.user_id
        })
      });

      if (response.status === 'success') {
        toast({
          title: "User Activated",
          description: `${user.full_name} has been activated`,
          variant: "default"
        });

        // Update user status
        setActiveUsers(prev => prev.map(u => 
          u.user_id === user.user_id ? { ...u, is_active: true } : u
        ));
      } else {
        throw new Error(response.message || 'Failed to activate user');
      }
    } catch (error) {
      console.error('Error activating user:', error);
      toast({
        title: "Error",
        description: "Failed to activate user. Please try again.",
        variant: "destructive"
      });
    } finally {
      setActionLoading(null);
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

  const getAccessLevelColor = (level: string) => {
    switch (level) {
      case 'admin':
        return 'bg-red-100 text-red-800 hover:bg-red-200';
      case 'read_write':
        return 'bg-blue-100 text-blue-800 hover:bg-blue-200';
      case 'read_only':
        return 'bg-green-100 text-green-800 hover:bg-green-200';
      default:
        return 'bg-gray-100 text-gray-800 hover:bg-gray-200';
    }
  };

  const handleViewDetails = (user: PendingUser) => {
    setSelectedUser(user);
    setShowDetailsDialog(true);
  };

  const handleApproveUser = (user: PendingUser) => {
    setSelectedUser(user);
    setApprovalData({
      access_level: user.requested_access_level,
      role_name: user.role_description,
      client_access: [],
      notes: ''
    });
    setShowApprovalDialog(true);
  };

  const handleRejectUser = (user: PendingUser) => {
    setSelectedUser(user);
    setShowRejectionDialog(true);
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
      <UserFilters
        activeTab={activeTab}
        pendingUsersCount={pendingUsers.length}
        activeUsersCount={activeUsers.length}
        onTabChange={setActiveTab}
      />

      <UserStats
        pendingUsers={pendingUsers}
        activeUsers={activeUsers}
      />

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
        formatDate={formatDate}
        getAccessLevelColor={getAccessLevelColor}
      />

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