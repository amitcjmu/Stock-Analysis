/**
 * EngagementSummaryCard component for ClientDetails
 * Generated with CC for UI modularization
 */

import React from 'react';
import { Users } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Separator } from '@/components/ui/separator';
import type { Client } from '../types';

interface EngagementSummaryCardProps {
  client: Client;
}

export const EngagementSummaryCard: React.FC<EngagementSummaryCardProps> = ({ client }) => {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Engagement Summary</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex items-center justify-between">
          <span className="text-sm text-muted-foreground">Total Engagements</span>
          <span className="font-medium">{client.total_engagements}</span>
        </div>
        <div className="flex items-center justify-between">
          <span className="text-sm text-muted-foreground">Active Engagements</span>
          <span className="font-medium text-green-600">{client.active_engagements}</span>
        </div>
        <Separator />
        <Button className="w-full">
          <Users className="w-4 h-4 mr-2" />
          View Engagements
        </Button>
      </CardContent>
    </Card>
  );
};