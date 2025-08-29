import React from 'react'
import { useState } from 'react'
import { useEffect, useCallback } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { useToast } from '@/components/ui/use-toast';
import { Search, UserPlus, Shield, Building2, Briefcase, Trash2, Eye, Edit, Crown } from 'lucide-react';
import { apiCall } from '@/config/api';
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
}

interface Client {
  id: string;
  account_name: string;
  industry?: string;
  company_size?: string;
}

interface Engagement {
  id: string;
  name: string;
  engagement_name?: string; // Backend might send this
  client_account_id: string;
  status: string;
}

interface AccessGrant {
  id: string;
  user_id: string;
  resource_type: 'client' | 'engagement';
  resource_id: string;
  access_level: 'read_only' | 'read_write' | 'admin';
  granted_by: string;
  granted_at: string;
  resource_name?: string;
}

export const UserAccessManagement: React.FC = () => {
  const { getAuthHeaders } = useAuth();
  const { toast } = useToast();

  // State
  const [users, setUsers] = useState<User[]>([]);
  const [clients, setClients] = useState<Client[]>([]);
  const [engagements, setEngagements] = useState<Engagement[]>([]);
  const [accessGrants, setAccessGrants] = useState<AccessGrant[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');

  // Form state for granting access
  const [selectedUser, setSelectedUser] = useState('');
  const [selectedResourceType, setSelectedResourceType] = useState<'client' | 'engagement'>('client');
  const [selectedClient, setSelectedClient] = useState('');
  const [selectedResource, setSelectedResource] = useState('');
  const [selectedAccessLevel, setSelectedAccessLevel] = useState<'read_only' | 'read_write' | 'admin'>('read_only');

  // Load initial data
  useEffect(() => {
    loadUsers();
    loadClients();
    loadEngagements(); // Load all engagements initially
    loadAccessGrants();
  }, []); // Run only once on mount

  // Reload engagements when selected client changes
  useEffect(() => {
    if (selectedClient) {
      loadEngagements(selectedClient);
    }
  }, [selectedClient]); // Only depend on selectedClient

  const loadUsers = useCallback(async () => {
    try {
      const response = await apiCall('/auth/active-users');

      if (response.status === 'success') {
        setUsers(response.active_users || []);
      } else {
        console.warn('Failed to load users from API:', response.message);
        setUsers([]);
      }
    } catch (error) {
      console.error('Error loading users:', error);
      toast({
        title: "Error",
        description: "Failed to load users",
        variant: "destructive"
      });
    }
  }, []); // Remove toast dependency to prevent re-creation

  const loadClients = useCallback(async () => {
    try {
      const response = await apiCall('/api/v1/admin/clients/?page_size=100');

      if (response.items) {
        setClients(response.items.map((client: Record<string, unknown>) => ({
          id: client.id,
          account_name: client.account_name,
          industry: client.industry,
          company_size: client.company_size
        })));
      } else {
        console.warn('No client data received from API');
        setClients([]);
      }
    } catch (error) {
      console.error('Error loading clients:', error);
    }
  }, []); // Keep empty dependency array

  const loadEngagements = useCallback(async (clientId?: string) => {
    try {
      const queryParams = clientId
        ? `?page_size=100&client_account_id=${clientId}`
        : '?page_size=100';
      const response = await apiCall(`/api/v1/admin/engagements/${queryParams}`);

      if (response.items) {
        setEngagements(response.items.map((engagement: Record<string, unknown>) => ({
          id: engagement.id,
          name: engagement.engagement_name || engagement.name || 'Unnamed',
          client_account_id: engagement.client_account_id,
          status: engagement.status || engagement.migration_phase || 'active'
        })));
      } else {
        console.warn('No engagement data received from API');
        setEngagements([]);
      }
    } catch (error) {
      console.error('Error loading engagements:', error);
    }
  }, []); // Keep empty dependency array

  const loadAccessGrants = useCallback(async () => {
    try {
      // TODO: Implement real API call for access grants
      // const response = await apiCall('/api/v1/admin/access-grants/');
      // For now, start with empty array until backend endpoint is implemented
      setAccessGrants([]);
    } catch (error) {
      console.error('Error loading access grants:', error);
    }
  }, []); // Keep empty dependency array

  const handleGrantAccess = async (): void => {
    if (!selectedUser || !selectedResource || !selectedAccessLevel) {
      toast({
        title: "Validation Error",
        description: "Please fill in all required fields",
        variant: "destructive"
      });
      return;
    }

    try {
      setLoading(true);

      // In production, this would be a real API call
      const resourceName = selectedResourceType === 'client'
        ? clients.find(c => c.id === selectedResource)?.account_name
        : engagements.find(e => e.id === selectedResource)?.name;

      const newGrant: AccessGrant = {
        id: `grant_${Date.now()}`,
        user_id: selectedUser,
        resource_type: selectedResourceType,
        resource_id: selectedResource,
        access_level: selectedAccessLevel,
        granted_by: '2a0de3df-7484-4fab-98b9-2ca126e2ab21', // Current admin user
        granted_at: new Date().toISOString(),
        resource_name: resourceName
      };

      setAccessGrants(prev => [...prev, newGrant]);

      // Reset form
      setSelectedUser('');
      setSelectedResource('');
      setSelectedAccessLevel('read_only');

      toast({
        title: "Access Granted",
        description: `Successfully granted ${selectedAccessLevel} access to ${resourceName}`,
      });

    } catch (error) {
      console.error('Error granting access:', error);
      toast({
        title: "Error",
        description: "Failed to grant access",
        variant: "destructive"
      });
    } finally {
      setLoading(false);
    }
  };

  const handleRevokeAccess = async (grantId: string): void => {
    try {
      // In production, this would be a real API call
      setAccessGrants(prev => prev.filter(grant => grant.id !== grantId));

      toast({
        title: "Access Revoked",
        description: "Successfully revoked access",
      });

    } catch (error) {
      console.error('Error revoking access:', error);
      toast({
        title: "Error",
        description: "Failed to revoke access",
        variant: "destructive"
      });
    }
  };

  const getAccessLevelIcon = (level: string): JSX.Element => {
    switch (level) {
      case 'admin':
        return <Crown className="h-3 w-3" />;
      case 'read_write':
        return <Edit className="h-3 w-3" />;
      case 'read_only':
        return <Eye className="h-3 w-3" />;
      default:
        return <Shield className="h-3 w-3" />;
    }
  };

  const getAccessLevelColor = (level: string): unknown => {
    switch (level) {
      case 'admin':
        return 'bg-red-100 text-red-800 border-red-200';
      case 'read_write':
        return 'bg-blue-100 text-blue-800 border-blue-200';
      case 'read_only':
        return 'bg-green-100 text-green-800 border-green-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const filteredUsers = users.filter(user =>
    user.full_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    user.email.toLowerCase().includes(searchTerm.toLowerCase()) ||
    user.organization.toLowerCase().includes(searchTerm.toLowerCase())
  );

  // Filter resources based on type and selected client
  const getAvailableResources = (): unknown => {
    if (selectedResourceType === 'client') {
      return clients;
    } else {
      // For engagements, filter by selected client if one is chosen
      if (selectedClient) {
        return engagements.filter(engagement => engagement.client_account_id === selectedClient);
      }
      return engagements;
    }
  };

  const availableResources = getAvailableResources();

  return (
    <div className="space-y-6">
      {/* Grant Access Form */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <UserPlus className="h-5 w-5" />
            Grant User Access
          </CardTitle>
          <CardDescription>
            Grant users access to specific clients or engagements with appropriate permission levels
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="space-y-2">
              <Label htmlFor="user-select">Select User</Label>
              <Select value={selectedUser} onValueChange={setSelectedUser}>
                <SelectTrigger>
                  <SelectValue placeholder="Choose user..." />
                </SelectTrigger>
                <SelectContent>
                  {users.map(user => (
                    <SelectItem key={user.user_id} value={user.user_id}>
                      <div className="flex items-center gap-2">
                        <span>{user.full_name}</span>
                        <span className="text-xs text-gray-500">({user.email})</span>
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="resource-type-select">Resource Type</Label>
              <Select value={selectedResourceType} onValueChange={(value: 'client' | 'engagement') => {
                setSelectedResourceType(value);
                setSelectedClient(''); // Reset client selection
                setSelectedResource(''); // Reset resource selection
              }}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="client">
                    <div className="flex items-center gap-2">
                      <Building2 className="h-4 w-4" />
                      Client Account
                    </div>
                  </SelectItem>
                  <SelectItem value="engagement">
                    <div className="flex items-center gap-2">
                      <Briefcase className="h-4 w-4" />
                      Engagement
                    </div>
                  </SelectItem>
                </SelectContent>
              </Select>
            </div>

            {selectedResourceType === 'engagement' && (
              <div className="space-y-2">
                <Label htmlFor="client-select">Select Client First</Label>
                <Select value={selectedClient} onValueChange={(value) => {
                  setSelectedClient(value);
                  setSelectedResource(''); // Reset engagement selection when client changes
                }}>
                  <SelectTrigger>
                    <SelectValue placeholder="Choose client..." />
                  </SelectTrigger>
                  <SelectContent>
                    {clients.map(client => (
                      <SelectItem key={client.id} value={client.id}>
                        {client.account_name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            )}

            <div className="space-y-2">
              <Label htmlFor="resource-select">
                {selectedResourceType === 'client' ? 'Select Client' : 'Select Engagement'}
              </Label>
              <Select
                value={selectedResource}
                onValueChange={setSelectedResource}
                disabled={selectedResourceType === 'engagement' && !selectedClient}
              >
                <SelectTrigger>
                  <SelectValue placeholder={
                    selectedResourceType === 'engagement' && !selectedClient
                      ? 'Select client first...'
                      : `Choose ${selectedResourceType}...`
                  } />
                </SelectTrigger>
                <SelectContent>
                  {availableResources.map(resource => (
                    <SelectItem key={resource.id} value={resource.id}>
                      {'account_name' in resource ? resource.account_name : resource.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="access-level-select">Access Level</Label>
              <Select value={selectedAccessLevel} onValueChange={(value: 'read_only' | 'read_write' | 'admin') => setSelectedAccessLevel(value)}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="read_only">
                    <div className="flex items-center gap-2">
                      <Eye className="h-4 w-4" />
                      Read Only
                    </div>
                  </SelectItem>
                  <SelectItem value="read_write">
                    <div className="flex items-center gap-2">
                      <Edit className="h-4 w-4" />
                      Read & Write
                    </div>
                  </SelectItem>
                  <SelectItem value="admin">
                    <div className="flex items-center gap-2">
                      <Crown className="h-4 w-4" />
                      Admin
                    </div>
                  </SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          <Button
            onClick={handleGrantAccess}
            disabled={loading || !selectedUser || !selectedResource}
            className="w-full md:w-auto"
          >
            {loading ? 'Granting Access...' : 'Grant Access'}
          </Button>
        </CardContent>
      </Card>

      {/* Current Access Grants */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Shield className="h-5 w-5" />
            Current Access Grants
          </CardTitle>
          <CardDescription>
            View and manage existing user access permissions
          </CardDescription>
        </CardHeader>
        <CardContent>
          {/* Search */}
          <div className="mb-4">
            <div className="relative">
              <Search className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
              <Input
                placeholder="Search users..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10"
              />
            </div>
          </div>

          {/* Access Grants List */}
          <div className="space-y-3">
            {accessGrants.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                <Shield className="h-12 w-12 mx-auto mb-4 text-gray-300" />
                <p>No access grants found</p>
                <p className="text-sm">Grant users access to clients or engagements to see them here</p>
              </div>
            ) : (
              accessGrants.map(grant => {
                const user = users.find(u => u.user_id === grant.user_id);
                if (!user) return null;

                return (
                  <div key={grant.id} className="flex items-center justify-between p-4 border rounded-lg bg-gray-50">
                    <div className="flex items-center gap-4">
                      <div className="flex-shrink-0">
                        <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
                          <span className="text-blue-600 font-medium text-sm">
                            {user.full_name.split(' ').map(n => n[0]).join('')}
                          </span>
                        </div>
                      </div>

                      <div className="flex-grow">
                        <div className="flex items-center gap-2 mb-1">
                          <span className="font-medium">{user.full_name}</span>
                          <span className="text-sm text-gray-500">({user.email})</span>
                        </div>

                        <div className="flex items-center gap-2 text-sm text-gray-600">
                          {grant.resource_type === 'client' ? (
                            <Building2 className="h-4 w-4" />
                          ) : (
                            <Briefcase className="h-4 w-4" />
                          )}
                          <span>{grant.resource_name}</span>
                          <span className="text-gray-400">•</span>
                          <Badge className={`text-xs ${getAccessLevelColor(grant.access_level)}`}>
                            <div className="flex items-center gap-1">
                              {getAccessLevelIcon(grant.access_level)}
                              {grant.access_level.replace('_', ' ')}
                            </div>
                          </Badge>
                        </div>
                      </div>
                    </div>

                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleRevokeAccess(grant.id)}
                      className="text-red-600 hover:text-red-700 hover:bg-red-50"
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                );
              })
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};
