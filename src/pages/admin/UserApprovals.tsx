import React, { useState, useEffect } from 'react';
import { 
  UserCheck, 
  UserX, 
  Clock, 
  Mail, 
  Building2, 
  User, 
  Calendar,
  CheckCircle,
  XCircle,
  AlertCircle,
  Eye,
  Trash2
} from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Label } from '@/components/ui/label';
import { useToast } from '@/components/ui/use-toast';
import { apiCall } from '@/config/api';
import { useAuth } from '@/contexts/AuthContext';

interface PendingUser {
  user_id: string;
  email: string;
  full_name: string;
  username: string;
  organization: string;
  role_description: string;
  registration_reason: string;
  requested_access_level: string;
  phone_number?: string;
  manager_email?: string;
  linkedin_profile?: string;
  registration_requested_at: string;
  status: string;
}

interface ApprovalData {
  access_level: string;
  role_name: string;
  client_access: string[];
  notes?: string;
}

interface RejectionData {
  rejection_reason: string;
}

const UserApprovals: React.FC = () => {
  const { getAuthHeaders } = useAuth();
  const { toast } = useToast();
  const [pendingUsers, setPendingUsers] = useState<PendingUser[]>([]);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [selectedUser, setSelectedUser] = useState<PendingUser | null>(null);
  const [showApprovalDialog, setShowApprovalDialog] = useState(false);
  const [showRejectionDialog, setShowRejectionDialog] = useState(false);
  const [showDetailsDialog, setShowDetailsDialog] = useState(false);

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
  }, []);

  const fetchPendingUsers = async () => {
    try {
      setLoading(true);
      const response = await apiCall('/api/v1/auth/pending-approvals', {
        headers: getAuthHeaders()
      });

      if (response.status === 'success') {
        setPendingUsers(response.pending_users || []);
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

  const handleApprove = async () => {
    if (!selectedUser) return;

    try {
      setActionLoading(selectedUser.user_id);
      
      const response = await apiCall('/api/v1/auth/approve-user', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...getAuthHeaders()
        },
        body: JSON.stringify({
          user_id: selectedUser.user_id,
          ...approvalData
        })
      });

      if (response.status === 'success') {
        toast({
          title: "User Approved",
          description: `${selectedUser.full_name} has been approved and can now access the platform.`,
        });
        
        // Remove from pending list
        setPendingUsers(prev => prev.filter(u => u.user_id !== selectedUser.user_id));
        setShowApprovalDialog(false);
        setSelectedUser(null);
        
        // Reset form
        setApprovalData({
          access_level: 'read_only',
          role_name: 'Analyst',
          client_access: [],
          notes: ''
        });
      } else {
        throw new Error(response.message || 'Approval failed');
      }
    } catch (error) {
      console.error('Error approving user:', error);
      toast({
        title: "Approval Failed",
        description: (error as Error).message,
        variant: "destructive"
      });
    } finally {
      setActionLoading(null);
    }
  };

  const handleReject = async () => {
    if (!selectedUser) return;

    try {
      setActionLoading(selectedUser.user_id);
      
      const response = await apiCall('/api/v1/auth/reject-user', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...getAuthHeaders()
        },
        body: JSON.stringify({
          user_id: selectedUser.user_id,
          ...rejectionData
        })
      });

      if (response.status === 'success') {
        toast({
          title: "User Rejected",
          description: `${selectedUser.full_name}'s request has been rejected.`,
        });
        
        // Remove from pending list
        setPendingUsers(prev => prev.filter(u => u.user_id !== selectedUser.user_id));
        setShowRejectionDialog(false);
        setSelectedUser(null);
        
        // Reset form
        setRejectionData({ rejection_reason: '' });
      } else {
        throw new Error(response.message || 'Rejection failed');
      }
    } catch (error) {
      console.error('Error rejecting user:', error);
      toast({
        title: "Rejection Failed",
        description: (error as Error).message,
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
      case 'read_only': return 'bg-blue-100 text-blue-800';
      case 'read_write': return 'bg-green-100 text-green-800';
      case 'admin': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  if (loading) {
    return (
      <div className="container mx-auto p-6">
        <div className="flex items-center justify-center min-h-96">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">User Approvals</h1>
          <p className="text-muted-foreground">
            Review and approve pending user registration requests
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Clock className="w-4 h-4 text-orange-500" />
          <span className="text-sm font-medium">{pendingUsers.length} pending</span>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Pending Approvals</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{pendingUsers.length}</div>
            <p className="text-xs text-muted-foreground">awaiting review</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Admin Requests</CardTitle>
            <AlertCircle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {pendingUsers.filter(u => u.requested_access_level === 'admin').length}
            </div>
            <p className="text-xs text-muted-foreground">high privilege requests</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Average Wait Time</CardTitle>
            <Calendar className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">1.2</div>
            <p className="text-xs text-muted-foreground">days</p>
          </CardContent>
        </Card>
      </div>

      {/* Pending Users List */}
      <Card>
        <CardHeader>
          <CardTitle>Pending Registration Requests</CardTitle>
          <CardDescription>
            Review user registration requests and approve or reject access
          </CardDescription>
        </CardHeader>
        <CardContent>
          {pendingUsers.length === 0 ? (
            <div className="text-center py-8">
              <CheckCircle className="w-12 h-12 text-green-500 mx-auto mb-4" />
              <h3 className="text-lg font-medium mb-2">No pending approvals</h3>
              <p className="text-muted-foreground">All user registration requests have been processed.</p>
            </div>
          ) : (
            <div className="space-y-4">
              {pendingUsers.map((user) => (
                <div key={user.user_id} className="border rounded-lg p-4 space-y-4">
                  <div className="flex items-start justify-between">
                    <div className="flex-1 space-y-2">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 bg-gray-100 rounded-full flex items-center justify-center">
                          <User className="w-5 h-5 text-gray-600" />
                        </div>
                        <div>
                          <h4 className="font-medium">{user.full_name}</h4>
                          <div className="flex items-center gap-4 text-sm text-muted-foreground">
                            <div className="flex items-center gap-1">
                              <Mail className="w-3 h-3" />
                              {user.email}
                            </div>
                            <div className="flex items-center gap-1">
                              <Building2 className="w-3 h-3" />
                              {user.organization}
                            </div>
                          </div>
                        </div>
                      </div>
                      
                      <div className="flex items-center gap-2">
                        <Badge variant="outline">{user.role_description}</Badge>
                        <Badge className={getAccessLevelColor(user.requested_access_level)}>
                          {user.requested_access_level.replace('_', ' ')}
                        </Badge>
                        <span className="text-xs text-muted-foreground">
                          Requested {formatDate(user.registration_requested_at)}
                        </span>
                      </div>

                      <p className="text-sm text-gray-700 line-clamp-2">
                        {user.registration_reason}
                      </p>
                    </div>

                    <div className="flex items-center gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => {
                          setSelectedUser(user);
                          setShowDetailsDialog(true);
                        }}
                      >
                        <Eye className="w-4 h-4 mr-1" />
                        Details
                      </Button>
                      
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => {
                          setSelectedUser(user);
                          setShowRejectionDialog(true);
                        }}
                        disabled={actionLoading === user.user_id}
                      >
                        <XCircle className="w-4 h-4 mr-1" />
                        Reject
                      </Button>
                      
                      <Button
                        size="sm"
                        onClick={() => {
                          setSelectedUser(user);
                          setApprovalData({
                            access_level: user.requested_access_level,
                            role_name: user.role_description,
                            client_access: [],
                            notes: ''
                          });
                          setShowApprovalDialog(true);
                        }}
                        disabled={actionLoading === user.user_id}
                      >
                        <CheckCircle className="w-4 h-4 mr-1" />
                        Approve
                      </Button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* User Details Dialog */}
      <Dialog open={showDetailsDialog} onOpenChange={setShowDetailsDialog}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>User Registration Details</DialogTitle>
            <DialogDescription>
              Complete information about the registration request
            </DialogDescription>
          </DialogHeader>
          
          {selectedUser && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label className="text-sm font-medium">Full Name</Label>
                  <p className="text-sm">{selectedUser.full_name}</p>
                </div>
                <div>
                  <Label className="text-sm font-medium">Username</Label>
                  <p className="text-sm">{selectedUser.username}</p>
                </div>
                <div>
                  <Label className="text-sm font-medium">Email</Label>
                  <p className="text-sm">{selectedUser.email}</p>
                </div>
                <div>
                  <Label className="text-sm font-medium">Phone</Label>
                  <p className="text-sm">{selectedUser.phone_number || 'Not provided'}</p>
                </div>
                <div>
                  <Label className="text-sm font-medium">Organization</Label>
                  <p className="text-sm">{selectedUser.organization}</p>
                </div>
                <div>
                  <Label className="text-sm font-medium">Role</Label>
                  <p className="text-sm">{selectedUser.role_description}</p>
                </div>
                <div>
                  <Label className="text-sm font-medium">Requested Access</Label>
                  <Badge className={getAccessLevelColor(selectedUser.requested_access_level)}>
                    {selectedUser.requested_access_level.replace('_', ' ')}
                  </Badge>
                </div>
                <div>
                  <Label className="text-sm font-medium">Requested On</Label>
                  <p className="text-sm">{formatDate(selectedUser.registration_requested_at)}</p>
                </div>
              </div>
              
              {selectedUser.manager_email && (
                <div>
                  <Label className="text-sm font-medium">Manager Email</Label>
                  <p className="text-sm">{selectedUser.manager_email}</p>
                </div>
              )}
              
              <div>
                <Label className="text-sm font-medium">Justification</Label>
                <p className="text-sm bg-gray-50 p-3 rounded-lg">
                  {selectedUser.registration_reason}
                </p>
              </div>
            </div>
          )}
          
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowDetailsDialog(false)}>
              Close
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

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
                placeholder="Please explain why this request is being rejected..."
                value={rejectionData.rejection_reason}
                onChange={(e) => setRejectionData(prev => ({ ...prev, rejection_reason: e.target.value }))}
                required
              />
            </div>
          </div>
          
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowRejectionDialog(false)}>
              Cancel
            </Button>
            <Button 
              variant="destructive" 
              onClick={handleReject} 
              disabled={!rejectionData.rejection_reason || actionLoading === selectedUser?.user_id}
            >
              {actionLoading === selectedUser?.user_id ? 'Rejecting...' : 'Reject Request'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default UserApprovals; 