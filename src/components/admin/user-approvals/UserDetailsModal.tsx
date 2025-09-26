/**
 * UserDetailsModal Component
 * Modal for displaying detailed user registration information
 */

import React from 'react';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Label } from '@/components/ui/label';
import type { UserDetailsModalProps } from './types';

export const UserDetailsModal: React.FC<UserDetailsModalProps> = ({
  user,
  isOpen,
  onClose,
  formatDate,
  getAccessLevelColor
}) => {

  if (!user) return null;

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>User Registration Details</DialogTitle>
          <DialogDescription>
            Complete information about the registration request
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label className="text-sm font-medium">User ID</Label>
              <p className="text-sm font-mono text-xs">{user.user_id || 'Not provided'}</p>
            </div>
            <div>
              <Label className="text-sm font-medium">Full Name</Label>
              <p className="text-sm">{user.full_name || 'Not provided'}</p>
            </div>
            <div>
              <Label className="text-sm font-medium">Username</Label>
              <p className="text-sm">{user.username || 'Not provided'}</p>
            </div>
            <div>
              <Label className="text-sm font-medium">Email</Label>
              <p className="text-sm">{user.email || 'Not provided'}</p>
            </div>
            <div>
              <Label className="text-sm font-medium">Phone</Label>
              <p className="text-sm">{user.phone_number || 'Not provided'}</p>
            </div>
            <div>
              <Label className="text-sm font-medium">Organization</Label>
              <p className="text-sm">{user.organization || 'Not provided'}</p>
            </div>
            <div>
              <Label className="text-sm font-medium">Role</Label>
              <p className="text-sm">{user.role_description || 'Not provided'}</p>
            </div>
            <div>
              <Label className="text-sm font-medium">Requested Access</Label>
              <Badge className={getAccessLevelColor(user.requested_access_level || 'read_only')}>
                {(user.requested_access_level || 'read_only').replace('_', ' ')}
              </Badge>
            </div>
            <div>
              <Label className="text-sm font-medium">Requested On</Label>
              <p className="text-sm">{(user.created_at || user.registration_requested_at) ? formatDate(user.created_at || user.registration_requested_at || '') : 'Invalid Date'}</p>
            </div>
          </div>

          {user.manager_email && (
            <div>
              <Label className="text-sm font-medium">Manager Email</Label>
              <p className="text-sm">{user.manager_email}</p>
            </div>
          )}

          <div>
            <Label className="text-sm font-medium">Justification</Label>
            <p className="text-sm bg-gray-50 p-3 rounded-lg">
              {user.registration_reason}
            </p>
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={onClose}>
            Close
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};
