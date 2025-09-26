import React from 'react';
import { Clock } from 'lucide-react'
import { UserCheck, UserX, Mail, Building2, User, CheckCircle, XCircle, Eye, Edit } from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import type { PendingUser, ActiveUser } from './types';

interface UserListProps {
  activeTab: 'pending' | 'active';
  pendingUsers: PendingUser[];
  activeUsers: ActiveUser[];
  actionLoading: string | null;
  onViewDetails: (user: PendingUser) => void;
  onApprove: (user: PendingUser) => void;
  onReject: (user: PendingUser) => void;
  onDeactivateUser: (user: ActiveUser) => void;
  onActivateUser: (user: ActiveUser) => void;
  onEditAccess: (user: ActiveUser) => void;
  formatDate: (dateString: string) => string;
  getAccessLevelColor: (level: string) => string;
}

export const UserList: React.FC<UserListProps> = ({
  activeTab,
  pendingUsers,
  activeUsers,
  actionLoading,
  onViewDetails,
  onApprove,
  onReject,
  onDeactivateUser,
  onActivateUser,
  onEditAccess,
  formatDate,
  getAccessLevelColor
}) => {
  if (activeTab === 'pending') {
    return (
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
                          <h4 className="font-medium">
                            {user.full_name || 'N/A'}
                            {user.username && <span className="text-sm text-muted-foreground ml-2">@{user.username}</span>}
                          </h4>
                          <div className="flex items-center gap-4 text-sm text-muted-foreground">
                            <div className="flex items-center gap-1">
                              <Mail className="w-3 h-3" />
                              {user.email || 'No email'}
                            </div>
                            <div className="flex items-center gap-1">
                              <Building2 className="w-3 h-3" />
                              {user.organization || 'No organization'}
                            </div>
                          </div>
                          <div className="text-xs text-muted-foreground mt-1">
                            ID: {user.user_id || 'No ID'}
                          </div>
                        </div>
                      </div>

                      <div className="flex items-center gap-2">
                        <Badge variant="outline">{user.role_description}</Badge>
                        <Badge className={getAccessLevelColor(user.requested_access_level)}>
                          {user.requested_access_level.replace('_', ' ')}
                        </Badge>
                        <span className="text-xs text-muted-foreground">
                          Requested {formatDate(user.created_at || user.registration_requested_at || '')}
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
                        onClick={() => onViewDetails(user)}
                      >
                        <Eye className="w-4 h-4 mr-1" />
                        Details
                      </Button>

                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => onReject(user)}
                        disabled={actionLoading === user.user_id}
                      >
                        <XCircle className="w-4 h-4 mr-1" />
                        Reject
                      </Button>

                      <Button
                        size="sm"
                        onClick={() => onApprove(user)}
                        disabled={actionLoading === user.user_id}
                      >
                        {actionLoading === user.user_id ? (
                          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                        ) : (
                          <>
                            <UserCheck className="w-4 h-4 mr-1" />
                            Approve
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
  }

  // Active Users Tab
  return (
    <Card>
      <CardHeader>
        <CardTitle>Active Platform Users</CardTitle>
        <CardDescription>
          View and manage users who have been approved and are active on the platform
        </CardDescription>
      </CardHeader>
      <CardContent>
        {activeUsers.length === 0 ? (
          <div className="text-center py-8">
            <UserX className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium mb-2">No active users</h3>
            <p className="text-muted-foreground">No users have been approved yet.</p>
          </div>
        ) : (
          <div className="space-y-4">
            {activeUsers.map((user) => (
              <div key={user.user_id} className="border rounded-lg p-4" data-testid="active-user-row">
                <div className="flex items-start justify-between">
                  <div className="flex-1 space-y-2">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 bg-green-100 rounded-full flex items-center justify-center">
                        <User className="w-5 h-5 text-green-600" />
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
                      <Badge variant="outline">{user.role_name}</Badge>
                      <Badge className={getAccessLevelColor(user.access_level)}>
                        {user.access_level.replace('_', ' ')}
                      </Badge>
                      <Badge variant={user.is_active ? "default" : "secondary"}>
                        {user.is_active ? "Active" : "Inactive"}
                      </Badge>
                    </div>

                    <div className="flex items-center gap-4 text-xs text-muted-foreground">
                      <span>Approved: {formatDate(user.approved_at)}</span>
                      {user.last_login && (
                        <span>Last login: {formatDate(user.last_login)}</span>
                      )}
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => onEditAccess(user)}
                    >
                      <Edit className="w-4 h-4 mr-1" />
                      Edit Access
                    </Button>
                    {user.is_active ? (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => onDeactivateUser(user)}
                        disabled={actionLoading === user.user_id}
                      >
                        <UserX className="w-4 h-4 mr-1" />
                        {actionLoading === user.user_id ? 'Deactivating...' : 'Deactivate'}
                      </Button>
                    ) : (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => onActivateUser(user)}
                        disabled={actionLoading === user.user_id}
                      >
                        <UserCheck className="w-4 h-4 mr-1" />
                        {actionLoading === user.user_id ? 'Activating...' : 'Activate'}
                      </Button>
                    )}
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
