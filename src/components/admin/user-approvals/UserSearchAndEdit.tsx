import React from 'react'
import { useState, useEffect, useCallback } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { useToast } from '@/components/ui/use-toast';
import { Search, Edit, Save, X, User, Building2, Briefcase, Crown, Shield } from 'lucide-react';
import { apiCall, clearUserManagementCache } from '@/config/api';
import { useAuth } from '@/contexts/AuthContext';

interface User {
  user_id: string;
  email: string;
  full_name: string;
  username: string;
  organization: string;
  role_description: string;
  access_level: string;
  role_name: string;
  is_active: boolean;
  default_client_id?: string;
  default_engagement_id?: string;
  created_at?: string;
  last_login?: string;
}

interface Client {
  id: string;
  account_name: string;
  industry?: string;
  company_size?: string;
}

interface Engagement {
  id: string;
  engagement_name: string;
  client_account_id: string;
  current_phase?: string;
}

interface UserEditForm {
  full_name: string;
  email: string;
  organization: string;
  role_name: string;
  default_client_id: string;
  default_engagement_id: string;
  is_active: boolean;
}

export const UserSearchAndEdit: React.FC = () => {
  const { getAuthHeaders } = useAuth();
  const { toast } = useToast();

  // State
  const [users, setUsers] = useState<User[]>([]);
  const [clients, setClients] = useState<Client[]>([]);
  const [engagements, setEngagements] = useState<Engagement[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [includeInactive, setIncludeInactive] = useState(false);
  const [selectedUser, setSelectedUser] = useState<User | null>(null);
  const [showEditDialog, setShowEditDialog] = useState(false);
  const [editForm, setEditForm] = useState<UserEditForm>({
    full_name: '',
    email: '',
    organization: '',
    role_name: '',
    default_client_id: 'none',
    default_engagement_id: 'none',
    is_active: true
  });

  const loadUsers = useCallback(async (): Promise<void> => {
    try {
      setLoading(true);
      const endpoint = includeInactive
        ? '/auth/active-users?include_inactive=true'
        : '/auth/active-users';
      const response = await apiCall(endpoint);

      if (response.status === 'success') {
        setUsers(response.active_users || []);
      } else {
        throw new Error('Failed to load users');
      }
    } catch (error) {
      console.error('Error loading users:', error);
      toast({
        title: "Error",
        description: "Failed to load users",
        variant: "destructive"
      });
    } finally {
      setLoading(false);
    }
  }, [toast, includeInactive]); // Include toast and includeInactive dependencies

  const loadClients = useCallback(async (): Promise<void> => {
    try {
      const response = await apiCall('/api/v1/admin/clients/?page_size=100');
      if (response.items) {
        setClients(response.items.map((client: Record<string, unknown>) => ({
          id: client.id,
          account_name: client.account_name,
          industry: client.industry,
          company_size: client.company_size
        })));
      }
    } catch (error) {
      console.error('Error loading clients:', error);
    }
  }, []);

  const loadEngagements = useCallback(async (): Promise<void> => {
    try {
      const response = await apiCall('/api/v1/admin/engagements/?page_size=100');
      if (response.items) {
        setEngagements(response.items.map((engagement: Record<string, unknown>) => ({
          id: engagement.id,
          engagement_name: engagement.engagement_name,
          client_account_id: engagement.client_account_id,
          current_phase: engagement.current_phase
        })));
      }
    } catch (error) {
      console.error('Error loading engagements:', error);
    }
  }, []);

  // Filter engagements based on selected client
  const getFilteredEngagements = useCallback((): Engagement[] => {
    if (editForm.default_client_id === 'none') {
      return [];
    }
    return engagements.filter(engagement => engagement.client_account_id === editForm.default_client_id);
  }, [editForm.default_client_id, engagements]);

  // Load initial data
  useEffect(() => {
    loadUsers();
    loadClients();
    loadEngagements();
  }, [loadUsers, loadClients, loadEngagements]); // Include function dependencies

  // Reset engagement selection when client changes
  useEffect(() => {
    if (editForm.default_client_id === 'none') {
      setEditForm(prev => ({ ...prev, default_engagement_id: 'none' }));
    } else {
      // Check if current engagement still belongs to selected client
      const availableEngagements = getFilteredEngagements();
      const currentEngagementValid = availableEngagements.some(e => e.id === editForm.default_engagement_id);
      if (!currentEngagementValid) {
        setEditForm(prev => ({ ...prev, default_engagement_id: 'none' }));
      }
    }
  }, [editForm.default_client_id, editForm.default_engagement_id, getFilteredEngagements]);

  const handleEditUser = (user: User): void => {
    setSelectedUser(user);
    setEditForm({
      full_name: user.full_name,
      email: user.email,
      organization: user.organization,
      role_name: user.role_name,
      default_client_id: user.default_client_id || 'none',
      default_engagement_id: user.default_engagement_id || 'none',
      is_active: user.is_active
    });
    setShowEditDialog(true);
  };

  const handleSaveUser = async (): void => {
    if (!selectedUser) return;

    try {
      setLoading(true);

      // Call API to update user
      const response = await apiCall(`/auth/admin/users/${selectedUser.user_id}`, {
        method: 'PUT',
        body: JSON.stringify({
          full_name: editForm.full_name,
          organization: editForm.organization,
          role_name: editForm.role_name,
          default_client_id: editForm.default_client_id === 'none' ? null : editForm.default_client_id,
          default_engagement_id: editForm.default_engagement_id === 'none' ? null : editForm.default_engagement_id,
          is_active: editForm.is_active
        })
      });

      if (response.status === 'success') {
        // Clear cache to ensure fresh data
        clearUserManagementCache();

        // Update local state
        setUsers(prevUsers =>
          prevUsers.map(user =>
            user.user_id === selectedUser.user_id
              ? { ...user, ...editForm }
              : user
          )
        );

        toast({
          title: "Success",
          description: `User "${editForm.full_name}" updated successfully`
        });

        setShowEditDialog(false);
        setSelectedUser(null);

        // Reload users to ensure we have the latest data
        await loadUsers();
      } else {
        throw new Error(response.message || 'Failed to update user');
      }
    } catch (error: unknown) {
      console.error('Error updating user:', error);
      toast({
        title: "Error",
        description: error.message || "Failed to update user",
        variant: "destructive"
      });
    } finally {
      setLoading(false);
    }
  };

  const getClientName = (clientId: string): unknown => {
    const client = clients.find(c => c.id === clientId);
    return client ? client.account_name : 'Unknown Client';
  };

  const getEngagementName = (engagementId: string): unknown => {
    const engagement = engagements.find(e => e.id === engagementId);
    return engagement ? engagement.engagement_name : 'Unknown Engagement';
  };

  const getRoleIcon = (roleName: string): JSX.Element => {
    switch (roleName.toLowerCase()) {
      case 'platform administrator':
      case 'admin':
        return <Crown className="h-4 w-4" />;
      case 'architect':
        return <Shield className="h-4 w-4" />;
      default:
        return <User className="h-4 w-4" />;
    }
  };

  const getRoleColor = (roleName: string): unknown => {
    switch (roleName.toLowerCase()) {
      case 'platform administrator':
      case 'admin':
        return 'bg-red-100 text-red-800';
      case 'architect':
        return 'bg-purple-100 text-purple-800';
      default:
        return 'bg-blue-100 text-blue-800';
    }
  };

  // Filter users based on search term
  const filteredUsers = users.filter(user =>
    user.full_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    user.email.toLowerCase().includes(searchTerm.toLowerCase()) ||
    user.organization.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="space-y-6">
      {/* Search Section */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Search className="h-5 w-5" />
            User Search & Management
          </CardTitle>
          <CardDescription>
            Search for users and manage their details, default client assignments, and engagement access
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="relative">
              <Search className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
              <Input
                placeholder="Search users by name, email, or organization..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10"
              />
            </div>
            <div className="flex items-center space-x-2">
              <Switch
                id="include-inactive"
                checked={includeInactive}
                onCheckedChange={setIncludeInactive}
              />
              <Label htmlFor="include-inactive" className="text-sm text-gray-600">
                Show inactive users (for reactivation)
              </Label>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Users List */}
      <Card>
        <CardHeader>
          <CardTitle>Users ({filteredUsers.length})</CardTitle>
          <CardDescription>
            Click "Edit" to modify user details and default assignments
          </CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="text-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
              <p className="mt-2 text-gray-500">Loading users...</p>
            </div>
          ) : filteredUsers.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <User className="h-12 w-12 mx-auto mb-4 text-gray-300" />
              <p>No users found</p>
              <p className="text-sm">Try adjusting your search criteria</p>
            </div>
          ) : (
            <div className="space-y-4">
              {filteredUsers.map(user => (
                <div key={user.user_id} className="flex items-center justify-between p-4 border rounded-lg bg-gray-50 hover:bg-gray-100 transition-colors">
                  <div className="flex items-center gap-4">
                    <div className="flex-shrink-0">
                      <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center">
                        <span className="text-blue-600 font-medium">
                          {user.full_name.split(' ').map(n => n[0]).join('').slice(0, 2)}
                        </span>
                      </div>
                    </div>

                    <div className="flex-grow">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="font-medium text-lg">{user.full_name}</span>
                        <Badge className={`text-xs ${getRoleColor(user.role_name)}`}>
                          <div className="flex items-center gap-1">
                            {getRoleIcon(user.role_name)}
                            {user.role_name}
                          </div>
                        </Badge>
                        {!user.is_active && (
                          <Badge variant="secondary" className="text-xs">
                            Inactive
                          </Badge>
                        )}
                      </div>

                      <div className="text-sm text-gray-600 space-y-1">
                        <div>{user.email}</div>
                        <div>{user.organization}</div>

                        {user.default_client_id && (
                          <div className="flex items-center gap-1">
                            <Building2 className="h-3 w-3" />
                            <span>Default Client: {getClientName(user.default_client_id)}</span>
                          </div>
                        )}

                        {user.default_engagement_id && (
                          <div className="flex items-center gap-1">
                            <Briefcase className="h-3 w-3" />
                            <span>Default Engagement: {getEngagementName(user.default_engagement_id)}</span>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>

                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleEditUser(user)}
                    className="flex items-center gap-2"
                  >
                    <Edit className="h-4 w-4" />
                    Edit
                  </Button>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Edit User Dialog */}
      <Dialog open={showEditDialog} onOpenChange={setShowEditDialog}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Edit User Details</DialogTitle>
            <DialogDescription>
              Update user information and default client/engagement assignments
            </DialogDescription>
          </DialogHeader>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="full_name">Full Name</Label>
              <Input
                id="full_name"
                value={editForm.full_name}
                onChange={(e) => setEditForm(prev => ({ ...prev, full_name: e.target.value }))}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                value={editForm.email}
                disabled
                className="bg-gray-100"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="organization">Organization</Label>
              <Input
                id="organization"
                value={editForm.organization}
                onChange={(e) => setEditForm(prev => ({ ...prev, organization: e.target.value }))}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="role_name">Role</Label>
              <Select
                value={editForm.role_name}
                onValueChange={(value) => setEditForm(prev => ({ ...prev, role_name: value }))}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="Analyst">Analyst</SelectItem>
                  <SelectItem value="Architect">Architect</SelectItem>
                  <SelectItem value="Project Manager">Project Manager</SelectItem>
                  <SelectItem value="Platform Administrator">Platform Administrator</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="default_client">Default Client</Label>
              <Select
                value={editForm.default_client_id}
                onValueChange={(value) => setEditForm(prev => ({ ...prev, default_client_id: value }))}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select default client..." />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="none">No default client</SelectItem>
                  {clients.map(client => (
                    <SelectItem key={client.id} value={client.id}>
                      {client.account_name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="default_engagement">Default Engagement</Label>
              <Select
                value={editForm.default_engagement_id}
                onValueChange={(value) => setEditForm(prev => ({ ...prev, default_engagement_id: value }))}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select default engagement..." />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="none">No default engagement</SelectItem>
                  {getFilteredEngagements().map(engagement => (
                    <SelectItem key={engagement.id} value={engagement.id}>
                      {engagement.engagement_name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="col-span-2 space-y-2">
              <Label htmlFor="is_active">Status</Label>
              <Select
                value={editForm.is_active ? "active" : "inactive"}
                onValueChange={(value) => setEditForm(prev => ({ ...prev, is_active: value === "active" }))}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="active">Active</SelectItem>
                  <SelectItem value="inactive">Inactive</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setShowEditDialog(false)}>
              <X className="h-4 w-4 mr-2" />
              Cancel
            </Button>
            <Button onClick={handleSaveUser} disabled={loading}>
              <Save className="h-4 w-4 mr-2" />
              {loading ? 'Saving...' : 'Save Changes'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};
