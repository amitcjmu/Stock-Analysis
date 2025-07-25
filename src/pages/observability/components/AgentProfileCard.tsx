/**
 * AgentProfileCard Component
 * Extracted from AgentDetailPage.tsx for modularization
 */

import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../../../components/ui/card';
import { Badge } from '../../../components/ui/badge';
import type { AgentDetailData } from '../types/AgentDetailTypes';

interface AgentProfileCardProps {
  agentData: AgentDetailData;
}

export const AgentProfileCard: React.FC<AgentProfileCardProps> = ({ agentData }) => {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Agent Profile</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          <div>
            <h4 className="font-medium text-gray-900">Specialization</h4>
            <p className="text-gray-600">{agentData.profile.specialization}</p>
          </div>
          <div>
            <h4 className="font-medium text-gray-900">Key Capabilities</h4>
            <div className="flex flex-wrap gap-2 mt-2">
              {agentData.profile.capabilities.map((capability, index) => (
                <Badge key={index} variant="secondary">
                  {capability}
                </Badge>
              ))}
            </div>
          </div>
          <div>
            <h4 className="font-medium text-gray-900">API Endpoints</h4>
            <div className="space-y-1 mt-2">
              {agentData.profile.endpoints.map((endpoint, index) => (
                <code key={index} className="block text-xs bg-gray-100 p-2 rounded">
                  {endpoint}
                </code>
              ))}
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};
