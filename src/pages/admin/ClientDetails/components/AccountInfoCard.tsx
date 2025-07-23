/**
 * AccountInfoCard component for ClientDetails
 * Generated with CC for UI modularization
 */

import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Client } from '../types';

interface AccountInfoCardProps {
  client: Client;
}

export const AccountInfoCard: React.FC<AccountInfoCardProps> = ({ client }) => {
  if (!client.description && !client.subscription_tier) {
    return null;
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Account Information</CardTitle>
        <CardDescription>Additional client account details</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {client.description && (
          <div>
            <h4 className="font-medium mb-2">Description</h4>
            <p className="text-sm text-muted-foreground">{client.description}</p>
          </div>
        )}
        {client.subscription_tier && (
          <div>
            <h4 className="font-medium mb-2">Subscription Tier</h4>
            <Badge variant="outline" className="capitalize">
              {client.subscription_tier}
            </Badge>
          </div>
        )}
      </CardContent>
    </Card>
  );
};