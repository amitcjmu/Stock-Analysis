import React, { useState, useEffect, useCallback } from 'react';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Label } from '@/components/ui/label';
import { useToast } from '@/components/ui/use-toast';
import { Building2, Briefcase, Plus, Trash2, Save, X, Shield, AlertCircle } from 'lucide-react';
import { apiCall } from '@/config/api';

interface ActiveUser {
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

interface ClientAccess {
  id: string;
  client_account_id: string;
  client_name: string;
  access_level: 'read' | 'write' | 'admin';
  is_active: boolean;
  granted_at: string;
}

interface EngagementAccess {
  id: string;
  engagement_id: string;
  engagement_name: string;
  client_account_id: string;
  client_name: string;
  access_level: 'read' | 'write' | 'admin';
  is_active: boolean;
  granted_at: string;
}

interface Client {
  id: string;
  name: string;
}

interface Engagement {
  id: string;
  name: string;
  client_account_id: string;
}

interface UserAccessModalProps {
  user: ActiveUser | null;
  isOpen: boolean;
  onClose: () => void;
  onAccessUpdated?: () => void;
}

export const UserAccessModal: React.FC<UserAccessModalProps> = ({
  user,
  isOpen,
  onClose,
  onAccessUpdated
}) => {
  const { toast } = useToast();
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);

  // Current access state
  const [clientAccess, setClientAccess] = useState<ClientAccess[]>([]);
  const [engagementAccess, setEngagementAccess] = useState<EngagementAccess[]>([]);

  // Available options
  const [availableClients, setAvailableClients] = useState<Client[]>([]);
  const [availableEngagements, setAvailableEngagements] = useState<Engagement[]>([]);

  // New access form
  const [showAddClient, setShowAddClient] = useState(false);
  const [showAddEngagement, setShowAddEngagement] = useState(false);
  const [newClientId, setNewClientId] = useState<string>('');
  const [newClientAccessLevel, setNewClientAccessLevel] = useState<'read' | 'write' | 'admin'>('read');
  const [newEngagementId, setNewEngagementId] = useState<string>('');
  const [newEngagementAccessLevel, setNewEngagementAccessLevel] = useState<'read' | 'write' | 'admin'>('read');
  const [selectedClientForEngagement, setSelectedClientForEngagement] = useState<string>('');

  // Load user access data
  const loadUserAccess = useCallback(async () => {
    if (!user) return;

    try {
      setLoading(true);

      // Fetch user's client access
      const clientAccessResponse = await apiCall(`/api/v1/admin/user-access/clients/${user.user_id}`);
      if (clientAccessResponse.client_access) {
        setClientAccess(clientAccessResponse.client_access);
      }

      // Fetch user's engagement access
      const engagementAccessResponse = await apiCall(`/api/v1/admin/user-access/engagements/${user.user_id}`);
      if (engagementAccessResponse.engagement_access) {
        setEngagementAccess(engagementAccessResponse.engagement_access);
      }

      // Fetch all available clients
      const clientsResponse = await apiCall('/api/v1/admin/clients/?page_size=100');
      if (clientsResponse.items) {
        setAvailableClients(clientsResponse.items.map((c: any) => ({
          id: c.id,
          name: c.account_name
        })));
      }

      // Fetch all available engagements
      const engagementsResponse = await apiCall('/api/v1/admin/engagements/?page_size=100');
      if (engagementsResponse.items) {
        setAvailableEngagements(engagementsResponse.items.map((e: any) => ({
          id: e.id,
          name: e.engagement_name,
          client_account_id: e.client_account_id
        })));
      }
    } catch (error) {
      console.error('Error loading user access:', error);
      toast({
        title: "Error",
        description: "Failed to load user access data",
        variant: "destructive"
      });
    } finally {
      setLoading(false);
    }
  }, [user, toast]);

  useEffect(() => {
    if (isOpen && user) {
      loadUserAccess();
    }
  }, [isOpen, user, loadUserAccess]);

  const handleAddClientAccess = async () => {
    if (!user || !newClientId) return;

    try {
      setSaving(true);

      const response = await apiCall('/api/v1/admin/user-access/clients', {
        method: 'POST',
        body: JSON.stringify({
          user_id: user.user_id,
          client_account_id: newClientId,
          access_level: newClientAccessLevel
        })
      });

      if (response.status === 'success') {
        toast({
          title: "Access Granted",
          description: "Client access has been granted successfully"
        });

        // Reload access data
        await loadUserAccess();

        // Reset form
        setNewClientId('');
        setNewClientAccessLevel('read');
        setShowAddClient(false);

        onAccessUpdated?.();
      } else {
        throw new Error(response.message || 'Failed to grant access');
      }
    } catch (error: any) {
      console.error('Error granting client access:', error);
      toast({
        title: "Error",
        description: error.message || "Failed to grant client access",
        variant: "destructive"
      });
    } finally {
      setSaving(false);
    }
  };

  const handleAddEngagementAccess = async () => {
    if (!user || !newEngagementId) return;

    try {
      setSaving(true);

      const response = await apiCall('/api/v1/admin/user-access/engagements', {
        method: 'POST',
        body: JSON.stringify({
          user_id: user.user_id,
          engagement_id: newEngagementId,
          access_level: newEngagementAccessLevel
        })
      });

      if (response.status === 'success') {
        toast({
          title: "Access Granted",
          description: "Engagement access has been granted successfully"
        });

        // Reload access data
        await loadUserAccess();

        // Reset form
        setNewEngagementId('');
        setNewEngagementAccessLevel('read');
        setSelectedClientForEngagement('');
        setShowAddEngagement(false);

        onAccessUpdated?.();
      } else {
        throw new Error(response.message || 'Failed to grant access');
      }
    } catch (error: any) {
      console.error('Error granting engagement access:', error);
      toast({
        title: "Error",
        description: error.message || "Failed to grant engagement access",
        variant: "destructive"
      });
    } finally {
      setSaving(false);
    }
  };

  const handleRevokeClientAccess = async (accessId: string, clientName: string) => {
    if (!user) return;

    try {
      setSaving(true);

      const response = await apiCall(`/api/v1/admin/user-access/clients/${accessId}`, {
        method: 'DELETE'
      });

      if (response.status === 'success') {
        toast({
          title: "Access Revoked",
          description: `Access to ${clientName} has been revoked`
        });

        // Reload access data
        await loadUserAccess();

        onAccessUpdated?.();
      } else {
        throw new Error(response.message || 'Failed to revoke access');
      }
    } catch (error: any) {
      console.error('Error revoking client access:', error);
      toast({
        title: "Error",
        description: error.message || "Failed to revoke client access",
        variant: "destructive"
      });
    } finally {
      setSaving(false);
    }
  };

  const handleRevokeEngagementAccess = async (accessId: string, engagementName: string) => {
    if (!user) return;

    try {
      setSaving(true);

      const response = await apiCall(`/api/v1/admin/user-access/engagements/${accessId}`, {
        method: 'DELETE'
      });

      if (response.status === 'success') {
        toast({
          title: "Access Revoked",
          description: `Access to ${engagementName} has been revoked`
        });

        // Reload access data
        await loadUserAccess();

        onAccessUpdated?.();
      } else {
        throw new Error(response.message || 'Failed to revoke access');
      }
    } catch (error: any) {
      console.error('Error revoking engagement access:', error);
      toast({
        title: "Error",
        description: error.message || "Failed to revoke engagement access",
        variant: "destructive"
      });
    } finally {
      setSaving(false);
    }
  };

  const getAccessLevelColor = (level: string) => {
    switch (level) {
      case 'admin':
        return 'bg-red-100 text-red-800';
      case 'write':
        return 'bg-blue-100 text-blue-800';
      case 'read':
        return 'bg-gray-100 text-gray-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getFilteredClientsForAdd = () => {
    const existingClientIds = clientAccess.map(ca => ca.client_account_id);
    return availableClients.filter(c => !existingClientIds.includes(c.id));
  };

  const getFilteredEngagementsForAdd = () => {
    if (!selectedClientForEngagement) return [];
    const existingEngagementIds = engagementAccess.map(ea => ea.engagement_id);
    return availableEngagements.filter(
      e => e.client_account_id === selectedClientForEngagement && !existingEngagementIds.includes(e.id)
    );
  };

  if (!user) return null;

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-5xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Shield className="h-5 w-5 text-blue-600" />
            Manage Access - {user.full_name}
          </DialogTitle>
          <DialogDescription>
            View and manage client and engagement access permissions for this user
          </DialogDescription>
        </DialogHeader>

        {loading ? (
          <div className="text-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
            <p className="mt-2 text-gray-500">Loading access data...</p>
          </div>
        ) : (
          <div className="space-y-6 py-4">
            {/* User Info */}
            <Card>
              <CardHeader>
                <CardTitle className="text-sm">User Information</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="text-gray-500">Email:</span> {user.email}
                  </div>
                  <div>
                    <span className="text-gray-500">Organization:</span> {user.organization}
                  </div>
                  <div>
                    <span className="text-gray-500">Role:</span>{' '}
                    <Badge variant="outline">{user.role_name}</Badge>
                  </div>
                  <div>
                    <span className="text-gray-500">Global Access Level:</span>{' '}
                    <Badge className={getAccessLevelColor(user.access_level)}>
                      {user.access_level}
                    </Badge>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Client Access */}
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle className="flex items-center gap-2">
                      <Building2 className="h-4 w-4" />
                      Client Access ({clientAccess.length})
                    </CardTitle>
                    <CardDescription>Clients this user can access</CardDescription>
                  </div>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setShowAddClient(true)}
                    disabled={saving}
                  >
                    <Plus className="h-4 w-4 mr-2" />
                    Add Client
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                {clientAccess.length === 0 ? (
                  <div className="text-center py-8 text-gray-500">
                    <AlertCircle className="h-12 w-12 mx-auto mb-4 text-gray-300" />
                    <p>No client access granted</p>
                    <p className="text-sm">Click "Add Client" to grant access to a client</p>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {clientAccess.map(access => (
                      <div
                        key={access.id}
                        className="flex items-center justify-between p-4 border rounded-lg bg-gray-50"
                      >
                        <div className="flex items-center gap-4">
                          <Building2 className="h-5 w-5 text-blue-600" />
                          <div>
                            <div className="font-medium">{access.client_name}</div>
                            <div className="text-sm text-gray-500">
                              Granted on {new Date(access.granted_at).toLocaleDateString()}
                            </div>
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          <Badge className={getAccessLevelColor(access.access_level)}>
                            {access.access_level}
                          </Badge>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleRevokeClientAccess(access.id, access.client_name)}
                            disabled={saving}
                          >
                            <Trash2 className="h-4 w-4 text-red-600" />
                          </Button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}

                {/* Add Client Form */}
                {showAddClient && (
                  <div className="mt-4 p-4 border rounded-lg bg-blue-50 space-y-4">
                    <div className="flex items-center justify-between">
                      <h4 className="font-medium">Grant Client Access</h4>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => {
                          setShowAddClient(false);
                          setNewClientId('');
                          setNewClientAccessLevel('read');
                        }}
                      >
                        <X className="h-4 w-4" />
                      </Button>
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <Label>Client</Label>
                        <Select value={newClientId} onValueChange={setNewClientId}>
                          <SelectTrigger>
                            <SelectValue placeholder="Select client..." />
                          </SelectTrigger>
                          <SelectContent>
                            {getFilteredClientsForAdd().map(client => (
                              <SelectItem key={client.id} value={client.id}>
                                {client.name}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>
                      <div>
                        <Label>Access Level</Label>
                        <Select
                          value={newClientAccessLevel}
                          onValueChange={(val) => setNewClientAccessLevel(val as 'read' | 'write' | 'admin')}
                        >
                          <SelectTrigger>
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="read">Read</SelectItem>
                            <SelectItem value="write">Write</SelectItem>
                            <SelectItem value="admin">Admin</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                    </div>
                    <Button
                      onClick={handleAddClientAccess}
                      disabled={!newClientId || saving}
                      size="sm"
                    >
                      <Save className="h-4 w-4 mr-2" />
                      {saving ? 'Granting...' : 'Grant Access'}
                    </Button>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Engagement Access */}
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle className="flex items-center gap-2">
                      <Briefcase className="h-4 w-4" />
                      Engagement Access ({engagementAccess.length})
                    </CardTitle>
                    <CardDescription>Engagements this user can access</CardDescription>
                  </div>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setShowAddEngagement(true)}
                    disabled={saving}
                  >
                    <Plus className="h-4 w-4 mr-2" />
                    Add Engagement
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                {engagementAccess.length === 0 ? (
                  <div className="text-center py-8 text-gray-500">
                    <AlertCircle className="h-12 w-12 mx-auto mb-4 text-gray-300" />
                    <p>No engagement access granted</p>
                    <p className="text-sm">Click "Add Engagement" to grant access to an engagement</p>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {engagementAccess.map(access => (
                      <div
                        key={access.id}
                        className="flex items-center justify-between p-4 border rounded-lg bg-gray-50"
                      >
                        <div className="flex items-center gap-4">
                          <Briefcase className="h-5 w-5 text-green-600" />
                          <div>
                            <div className="font-medium">{access.engagement_name}</div>
                            <div className="text-sm text-gray-500">
                              Client: {access.client_name} • Granted on {new Date(access.granted_at).toLocaleDateString()}
                            </div>
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          <Badge className={getAccessLevelColor(access.access_level)}>
                            {access.access_level}
                          </Badge>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleRevokeEngagementAccess(access.id, access.engagement_name)}
                            disabled={saving}
                          >
                            <Trash2 className="h-4 w-4 text-red-600" />
                          </Button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}

                {/* Add Engagement Form */}
                {showAddEngagement && (
                  <div className="mt-4 p-4 border rounded-lg bg-green-50 space-y-4">
                    <div className="flex items-center justify-between">
                      <h4 className="font-medium">Grant Engagement Access</h4>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => {
                          setShowAddEngagement(false);
                          setNewEngagementId('');
                          setNewEngagementAccessLevel('read');
                          setSelectedClientForEngagement('');
                        }}
                      >
                        <X className="h-4 w-4" />
                      </Button>
                    </div>
                    <div className="grid grid-cols-3 gap-4">
                      <div>
                        <Label>Client</Label>
                        <Select
                          value={selectedClientForEngagement}
                          onValueChange={(val) => {
                            setSelectedClientForEngagement(val);
                            setNewEngagementId(''); // Reset engagement when client changes
                          }}
                        >
                          <SelectTrigger>
                            <SelectValue placeholder="Select client first..." />
                          </SelectTrigger>
                          <SelectContent>
                            {availableClients.map(client => (
                              <SelectItem key={client.id} value={client.id}>
                                {client.name}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>
                      <div>
                        <Label>Engagement</Label>
                        <Select
                          value={newEngagementId}
                          onValueChange={setNewEngagementId}
                          disabled={!selectedClientForEngagement}
                        >
                          <SelectTrigger>
                            <SelectValue placeholder={selectedClientForEngagement ? "Select engagement..." : "Select client first"} />
                          </SelectTrigger>
                          <SelectContent>
                            {getFilteredEngagementsForAdd().map(engagement => (
                              <SelectItem key={engagement.id} value={engagement.id}>
                                {engagement.name}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>
                      <div>
                        <Label>Access Level</Label>
                        <Select
                          value={newEngagementAccessLevel}
                          onValueChange={(val) => setNewEngagementAccessLevel(val as 'read' | 'write' | 'admin')}
                        >
                          <SelectTrigger>
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="read">Read</SelectItem>
                            <SelectItem value="write">Write</SelectItem>
                            <SelectItem value="admin">Admin</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                    </div>
                    <Button
                      onClick={handleAddEngagementAccess}
                      disabled={!newEngagementId || saving}
                      size="sm"
                    >
                      <Save className="h-4 w-4 mr-2" />
                      {saving ? 'Granting...' : 'Grant Access'}
                    </Button>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        )}

        <DialogFooter>
          <Button variant="outline" onClick={onClose}>
            <X className="h-4 w-4 mr-2" />
            Close
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};
