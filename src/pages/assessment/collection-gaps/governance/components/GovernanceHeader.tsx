/**
 * GovernanceHeader Component
 * Page header with navigation and approval request button
 */

import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { ArrowLeft, FileText } from 'lucide-react';

interface GovernanceHeaderProps {
  flowId: string;
  onRequestApproval: () => void;
}

export const GovernanceHeader: React.FC<GovernanceHeaderProps> = ({
  flowId,
  onRequestApproval
}) => {
  const navigate = useNavigate();

  return (
    <div className="flex items-center justify-between">
      <div className="flex items-center gap-4">
        <Button
          variant="outline"
          size="sm"
          onClick={() => navigate(`/assessment/collection-gaps?flowId=${flowId}`)}
          className="flex items-center gap-2"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to Dashboard
        </Button>
        <div>
          <h1 className="text-3xl font-bold">Governance & Exceptions</h1>
          <p className="text-muted-foreground">
            Submit approval requests and manage migration exceptions
          </p>
        </div>
      </div>
      <div className="flex gap-2">
        <Button
          variant="outline"
          className="flex items-center gap-2"
          onClick={onRequestApproval}
        >
          <FileText className="h-4 w-4" />
          Request Approval
        </Button>
      </div>
    </div>
  );
};
