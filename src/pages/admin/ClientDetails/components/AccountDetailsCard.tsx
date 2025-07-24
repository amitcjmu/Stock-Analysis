/**
 * AccountDetailsCard component for ClientDetails
 * Generated with CC for UI modularization
 */

import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import type { Client } from '../types';
import { formatDate } from '../utils';

interface AccountDetailsCardProps {
  client: Client;
}

export const AccountDetailsCard: React.FC<AccountDetailsCardProps> = ({ client }) => {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Account Details</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div>
          <p className="text-sm text-muted-foreground">Created</p>
          <p className="text-sm font-medium">{formatDate(client.created_at)}</p>
        </div>
        {client.updated_at && (
          <div>
            <p className="text-sm text-muted-foreground">Last Updated</p>
            <p className="text-sm font-medium">{formatDate(client.updated_at)}</p>
          </div>
        )}
        <div>
          <p className="text-sm text-muted-foreground">Status</p>
          <Badge variant={client.is_active ? "default" : "secondary"}>
            {client.is_active ? "Active" : "Inactive"}
          </Badge>
        </div>
      </CardContent>
    </Card>
  );
};