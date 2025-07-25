/**
 * BusinessContextCard component for ClientDetails
 * Generated with CC for UI modularization
 */

import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import type { Client } from '../types';
import { getProviderLabel, getPriorityLabel } from '../utils';

interface BusinessContextCardProps {
  client: Client;
}

export const BusinessContextCard: React.FC<BusinessContextCardProps> = ({ client }) => {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Business Context</CardTitle>
        <CardDescription>Strategic objectives and migration priorities</CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        <div>
          <h4 className="font-medium mb-3">Business Objectives</h4>
          <div className="flex flex-wrap gap-2">
            {(() => {
              // Handle different data structures from API
              let objectives = [];
              if (Array.isArray(client.business_objectives)) {
                objectives = client.business_objectives;
              } else if (client.business_objectives && typeof client.business_objectives === 'object' && client.business_objectives.primary_goals) {
                objectives = client.business_objectives.primary_goals;
              }

              return objectives && objectives.length > 0 ? (
                objectives.map((objective, index) => (
                  <Badge key={index} variant="secondary">
                    {objective}
                  </Badge>
                ))
              ) : (
                <p className="text-sm text-muted-foreground">No business objectives specified</p>
              );
            })()}
          </div>
        </div>

        <Separator />

        <div>
          <h4 className="font-medium mb-3">Target Cloud Providers</h4>
          <div className="flex flex-wrap gap-2">
            {client.target_cloud_providers && client.target_cloud_providers.length > 0 ? (
              client.target_cloud_providers.map((provider, index) => (
                <Badge key={index} variant="outline">
                  {getProviderLabel(provider)}
                </Badge>
              ))
            ) : (
              <p className="text-sm text-muted-foreground">No cloud providers specified</p>
            )}
          </div>
        </div>

        <Separator />

        <div>
          <h4 className="font-medium mb-3">Business Priorities</h4>
          <div className="flex flex-wrap gap-2">
            {client.business_priorities && client.business_priorities.length > 0 ? (
              client.business_priorities.map((priority, index) => (
                <Badge key={index} className="bg-blue-100 text-blue-800">
                  {getPriorityLabel(priority)}
                </Badge>
              ))
            ) : (
              <p className="text-sm text-muted-foreground">No business priorities specified</p>
            )}
          </div>
        </div>

        <Separator />

        <div>
          <h4 className="font-medium mb-3">Compliance Requirements</h4>
          <div className="flex flex-wrap gap-2">
            {client.compliance_requirements && client.compliance_requirements.length > 0 ? (
              client.compliance_requirements.map((requirement, index) => (
                <Badge key={index} className="bg-purple-100 text-purple-800">
                  {requirement}
                </Badge>
              ))
            ) : (
              <p className="text-sm text-muted-foreground">No compliance requirements specified</p>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
};
