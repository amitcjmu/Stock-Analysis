import React, { useState, useEffect } from 'react';
import { 
  UserCheck, 
  UserX, 
  UserClock, 
  Shield, 
  Users,
  Building2,
  Mail,
  Calendar,
  CheckCircle,
  XCircle,
  Clock,
  MoreHorizontal,
  Eye,
  Settings
} from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Separator } from '@/components/ui/separator';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '@/components/ui/dropdown-menu';
import { useToast } from '@/components/ui/use-toast';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';

interface User {
  id: string;
  username: string;
  email: string;
  full_name: string;
  role: string;
  status: 'pending' | 'approved' | 'rejected' | 'suspended';
  registration_date: string;
  approval_date?: string;
  last_login?: string;
  requested_access: {
    client_accounts: string[];
    engagements: string[];
    access_level: string;
  };
  justification?: string;
}

interface ApprovalAction {
  user_id: string;
  action: 'approve' | 'reject';
  notes?: string;
  client_access?: string[];
  engagement_access?: string[];
}

const UserApprovals: React.FC = () => {
  const [pendingUsers, setPendingUsers] = useState<User[]>([]);
  const [allUsers, setAllUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedUser, setSelectedUser] = useState<User | null>(null);
  const [showApprovalDialog, setShowApprovalDialog] = useState(false);
  const [approvalAction, setApprovalAction] = useState<'approve' | 'reject'>('approve');
  const [approvalNotes, setApprovalNotes] = useState('');
  const [selectedClientAccess, setSelectedClientAccess] = useState<string[]>([]);
  const [selectedEngagementAccess, setSelectedEngagementAccess] = useState<string[]>([]);
  const { toast } = useToast();

  useEffect(() => {
    fetchUsers();
  }, []);

  const fetchUsers = async () => {
    try {
      setLoading(true);
      
      // Fetch pending users and all users
      const [pendingResponse, allUsersResponse] = await Promise.all([
        fetch('/api/v1/auth/rbac/pending-users'),
        fetch('/api/v1/auth/rbac/users')
      ]);

      if (!pendingResponse.ok || !allUsersResponse.ok) {
        throw new Error('Failed to fetch users');
      }

      const [pendingData, allUsersData] = await Promise.all([
        pendingResponse.json(),
        allUsersResponse.json()
      ]);

      setPendingUsers(pendingData.users || []);
      setAllUsers(allUsersData.users || []);
    } catch (error) {
      console.error('Error fetching users:', error);
      toast({
        title: "Error",
        description: "Failed to fetch users. Using demo data.",
        variant: "destructive"
      });
      
      // Demo data fallback
      const demoUsers = [
        {
          id: '1',
          username: 'john.doe',
          email: 'john.doe@techcorp.com',
          full_name: 'John Doe',
          role: 'user',
          status: 'pending' as const,
          registration_date: '2024-06-01T10:30:00Z',
          requested_access: {
            client_accounts: ['TechCorp Solutions'],
            engagements: ['Cloud Migration 2025'],
            access_level: 'read'
          },
          justification: 'I am the Cloud Infrastructure Manager at TechCorp and need access to monitor our migration progress and provide technical oversight for the Cloud Migration 2025 engagement.'
        },
        {
          id: '2',
          username: 'sarah.wilson',
          email: 'sarah.wilson@healthplus.com',
          full_name: 'Sarah Wilson',
          role: 'user',
          status: 'pending' as const,
          registration_date: '2024-06-01T14:45:00Z',
          requested_access: {
            client_accounts: ['HealthPlus Corp'],
            engagements: ['Healthcare Cloud Transformation'],
            access_level: 'read_write'
          },
          justification: 'As the IT Director, I need full access to our healthcare transformation project to manage compliance requirements and oversee technical decisions.'
        },
        {
          id: '3',
          username: 'admin.user',
          email: 'admin@aiforce.com',
          full_name: 'Admin User',
          role: 'admin',
          status: 'approved' as const,
          registration_date: '2024-01-15T08:00:00Z',
          approval_date: '2024-01-15T08:05:00Z',
          last_login: '2024-06-02T09:15:00Z',
          requested_access: {
            client_accounts: [],
            engagements: [],
            access_level: 'admin'
          }
        }
      ];
      
      setPendingUsers(demoUsers.filter(u => u.status === 'pending'));
      setAllUsers(demoUsers);
    } finally {
      setLoading(false);
    }
  };

  const handleApprovalAction = async () => {
    if (!selectedUser) return;

    try {
      const actionData: ApprovalAction = {
        user_id: selectedUser.id,
        action: approvalAction,
        notes: approvalNotes,
        client_access: selectedClientAccess,
        engagement_access: selectedEngagementAccess
      };

      const response = await fetch(`/api/v1/auth/rbac/users/${selectedUser.id}/${approvalAction}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(actionData)
      });

      if (!response.ok) {
        throw new Error(`Failed to ${approvalAction} user`);
      }

      toast({
        title: "Success",
        description: `User ${selectedUser.full_name} has been ${approvalAction === 'approve' ? 'approved' : 'rejected'} successfully.`,
      });

      setShowApprovalDialog(false);
      setSelectedUser(null);
      setApprovalNotes('');
      setSelectedClientAccess([]);
      setSelectedEngagementAccess([]);
      fetchUsers();
    } catch (error) {
      console.error(`Error ${approvalAction}ing user:`, error);
      toast({
        title: "Error",
        description: `Failed to ${approvalAction} user. Please try again.`,
        variant: "destructive"
      });
    }
  };

  const handleSuspendUser = async (userId: string, userName: string) => {
    if (!confirm(`Are you sure you want to suspend user "${userName}"?`)) {
      return;
    }

    try {
      const response = await fetch(`/api/v1/auth/rbac/users/${userId}/suspend`, {
        method: 'POST'
      });

      if (!response.ok) {
        throw new Error('Failed to suspend user');
      }

      toast({
        title: "Success",
        description: `User ${userName} has been suspended successfully.`,
      });

      fetchUsers();
    } catch (error) {
      console.error('Error suspending user:', error);
      toast({
        title: "Error",
        description: "Failed to suspend user. Please try again.",
        variant: "destructive"
      });
    }
  };

  const startApproval = (user: User, action: 'approve' | 'reject') => {
    setSelectedUser(user);
    setApprovalAction(action);
    setSelectedClientAccess(user.requested_access.client_accounts);
    setSelectedEngagementAccess(user.requested_access.engagements);
    setShowApprovalDialog(true);
  };

  const getStatusBadge = (status: User['status']) => {
    switch (status) {
      case 'pending':
        return (
          <Badge variant="secondary" className="bg-yellow-100 text-yellow-800 hover:bg-yellow-100">
            <UserClock className="w-3 h-3 mr-1" />
            Pending
          </Badge>
        );
      case 'approved':
        return (
          <Badge className="bg-green-100 text-green-800 hover:bg-green-100">
            <UserCheck className="w-3 h-3 mr-1" />
            Approved
          </Badge>
        );
      case 'rejected':
        return (
          <Badge variant="destructive">
            <UserX className="w-3 h-3 mr-1" />
            Rejected
          </Badge>
        );
      case 'suspended':
        return (
          <Badge variant="secondary" className="bg-red-100 text-red-800 hover:bg-red-100">
            <XCircle className="w-3 h-3 mr-1" />
            Suspended
          </Badge>
        );
      default:
        return <Badge variant="secondary">{status}</Badge>;
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

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">User Management</h1>
          <p className="text-muted-foreground">
            Manage user approvals and access controls
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" asChild>
            <a href="/admin/users/roles">
              <Shield className="w-4 h-4 mr-2" />
              Manage Roles
            </a>
          </Button>
          <Button variant="outline" asChild>
            <a href="/admin/users/audit">
              <Settings className="w-4 h-4 mr-2" />
              Audit Log
            </a>
          </Button>
        </div>
      </div>

      {/* Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Pending Approvals</CardTitle>
            <UserClock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{pendingUsers.length}</div>
            <p className="text-xs text-muted-foreground">
              users awaiting approval
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Approved Users</CardTitle>
            <UserCheck className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {allUsers.filter(u => u.status === 'approved').length}
            </div>
            <p className="text-xs text-muted-foreground">
              active platform users
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Users</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{allUsers.length}</div>
            <p className="text-xs text-muted-foreground">
              registered users
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Rejected/Suspended</CardTitle>
            <UserX className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {allUsers.filter(u => u.status === 'rejected' || u.status === 'suspended').length}
            </div>
            <p className="text-xs text-muted-foreground">
              inactive users
            </p>
          </CardContent>
        </Card>
      </div>

      {/* User Management Tabs */}
      <Tabs defaultValue="pending" className="space-y-4">
        <TabsList className="grid w-full grid-cols-2">
          <TabsTrigger value="pending">
            Pending Approvals ({pendingUsers.length})
          </TabsTrigger>
          <TabsTrigger value="all">
            All Users ({allUsers.length})
          </TabsTrigger>
        </TabsList>

        <TabsContent value="pending" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Pending User Approvals</CardTitle>
              <CardDescription>
                Users waiting for administrative approval to access the platform
              </CardDescription>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="flex items-center justify-center py-8">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
                </div>
              ) : pendingUsers.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground">
                  <UserCheck className="h-12 w-12 mx-auto mb-4 opacity-50" />
                  <p>No pending user approvals</p>
                </div>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>User</TableHead>
                      <TableHead>Requested Access</TableHead>
                      <TableHead>Justification</TableHead>
                      <TableHead>Registration Date</TableHead>
                      <TableHead className="text-right">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {pendingUsers.map((user) => (
                      <TableRow key={user.id}>
                        <TableCell>
                          <div>
                            <div className="font-medium">{user.full_name}</div>
                            <div className="text-sm text-muted-foreground flex items-center">
                              <Mail className="w-3 h-3 mr-1" />
                              {user.email}
                            </div>
                            <div className="text-sm text-muted-foreground">
                              @{user.username}
                            </div>
                          </div>
                        </TableCell>
                        <TableCell>
                          <div className="space-y-1">
                            <div className="text-sm">
                              <strong>Level:</strong> {user.requested_access.access_level}
                            </div>
                            {user.requested_access.client_accounts.length > 0 && (
                              <div className="text-sm">
                                <strong>Clients:</strong> {user.requested_access.client_accounts.join(', ')}
                              </div>
                            )}
                            {user.requested_access.engagements.length > 0 && (
                              <div className="text-sm">
                                <strong>Engagements:</strong> {user.requested_access.engagements.join(', ')}
                              </div>
                            )}
                          </div>
                        </TableCell>
                        <TableCell>
                          <div className="max-w-md">
                            <p className="text-sm line-clamp-3">
                              {user.justification || 'No justification provided'}
                            </p>
                          </div>
                        </TableCell>
                        <TableCell>
                          <div className="text-sm flex items-center">
                            <Calendar className="w-3 h-3 mr-1" />
                            {formatDate(user.registration_date)}
                          </div>
                        </TableCell>
                        <TableCell className="text-right">
                          <div className="flex gap-2 justify-end">
                            <Button
                              size="sm"
                              onClick={() => startApproval(user, 'approve')}
                            >
                              <UserCheck className="w-4 h-4 mr-1" />
                              Approve
                            </Button>
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => startApproval(user, 'reject')}
                            >
                              <UserX className="w-4 h-4 mr-1" />
                              Reject
                            </Button>
                          </div>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="all" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>All Platform Users</CardTitle>
              <CardDescription>
                Complete list of all registered users with their current status
              </CardDescription>
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
                      <TableHead>User</TableHead>
                      <TableHead>Role</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Registration</TableHead>
                      <TableHead>Last Login</TableHead>
                      <TableHead className="text-right">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {allUsers.map((user) => (
                      <TableRow key={user.id}>
                        <TableCell>
                          <div>
                            <div className="font-medium">{user.full_name}</div>
                            <div className="text-sm text-muted-foreground flex items-center">
                              <Mail className="w-3 h-3 mr-1" />
                              {user.email}
                            </div>
                            <div className="text-sm text-muted-foreground">
                              @{user.username}
                            </div>
                          </div>
                        </TableCell>
                        <TableCell>
                          <Badge variant="outline">
                            {user.role === 'admin' ? <Shield className="w-3 h-3 mr-1" /> : <Users className="w-3 h-3 mr-1" />}
                            {user.role}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          {getStatusBadge(user.status)}
                        </TableCell>
                        <TableCell>
                          <div className="text-sm flex items-center">
                            <Calendar className="w-3 h-3 mr-1" />
                            {formatDate(user.registration_date)}
                          </div>
                        </TableCell>
                        <TableCell>
                          <div className="text-sm">
                            {user.last_login ? (
                              <div className="flex items-center">
                                <Clock className="w-3 h-3 mr-1" />
                                {formatDate(user.last_login)}
                              </div>
                            ) : (
                              <span className="text-muted-foreground">Never</span>
                            )}
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
                              <DropdownMenuItem>
                                <Eye className="w-4 h-4 mr-2" />
                                View Details
                              </DropdownMenuItem>
                              <DropdownMenuItem>
                                <Settings className="w-4 h-4 mr-2" />
                                Edit Access
                              </DropdownMenuItem>
                              {user.status === 'approved' && (
                                <DropdownMenuItem 
                                  onClick={() => handleSuspendUser(user.id, user.full_name)}
                                  className="text-red-600"
                                >
                                  <UserX className="w-4 h-4 mr-2" />
                                  Suspend User
                                </DropdownMenuItem>
                              )}
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
        </TabsContent>
      </Tabs>

      {/* Approval Dialog */}
      <Dialog open={showApprovalDialog} onOpenChange={setShowApprovalDialog}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>
              {approvalAction === 'approve' ? 'Approve' : 'Reject'} User: {selectedUser?.full_name}
            </DialogTitle>
            <DialogDescription>
              {approvalAction === 'approve' 
                ? 'Configure access permissions and approve this user for platform access.'
                : 'Provide a reason for rejecting this user\'s access request.'
              }
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4">
            {selectedUser && (
              <div className="p-4 bg-muted rounded-lg">
                <h4 className="font-medium mb-2">User Information</h4>
                <div className="text-sm space-y-1">
                  <p><strong>Name:</strong> {selectedUser.full_name}</p>
                  <p><strong>Email:</strong> {selectedUser.email}</p>
                  <p><strong>Username:</strong> @{selectedUser.username}</p>
                  <p><strong>Requested Access:</strong> {selectedUser.requested_access.access_level}</p>
                  {selectedUser.justification && (
                    <div>
                      <strong>Justification:</strong>
                      <p className="mt-1 text-muted-foreground">{selectedUser.justification}</p>
                    </div>
                  )}
                </div>
              </div>
            )}

            {approvalAction === 'approve' && (
              <div className="space-y-4">
                <Separator />
                <div>
                  <Label htmlFor="client_access">Client Access (if different from requested)</Label>
                  <div className="text-sm text-muted-foreground mb-2">
                    Leave empty to grant requested access: {selectedUser?.requested_access.client_accounts.join(', ') || 'None'}
                  </div>
                  {/* In a real implementation, this would be a multi-select with available clients */}
                </div>
              </div>
            )}

            <div className="space-y-2">
              <Label htmlFor="approval_notes">
                {approvalAction === 'approve' ? 'Approval Notes (Optional)' : 'Rejection Reason *'}
              </Label>
              <Textarea
                id="approval_notes"
                placeholder={
                  approvalAction === 'approve' 
                    ? 'Add any notes about this approval...'
                    : 'Please provide a reason for rejecting this request...'
                }
                value={approvalNotes}
                onChange={(e) => setApprovalNotes(e.target.value)}
                required={approvalAction === 'reject'}
              />
            </div>
          </div>

          <div className="flex justify-end gap-2">
            <Button variant="outline" onClick={() => setShowApprovalDialog(false)}>
              Cancel
            </Button>
            <Button 
              onClick={handleApprovalAction}
              variant={approvalAction === 'approve' ? 'default' : 'destructive'}
              disabled={approvalAction === 'reject' && !approvalNotes.trim()}
            >
              {approvalAction === 'approve' ? (
                <>
                  <UserCheck className="w-4 h-4 mr-2" />
                  Approve User
                </>
              ) : (
                <>
                  <UserX className="w-4 h-4 mr-2" />
                  Reject User
                </>
              )}
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default UserApprovals; 