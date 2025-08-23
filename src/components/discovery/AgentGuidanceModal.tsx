import React from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { CheckCircle2, AlertCircle, Info, ChevronRight, Upload, RefreshCcw } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import type { UserGuidance, RoutingContext } from '@/types/api/flow-continuation';

interface AgentGuidanceModalProps {
  isOpen: boolean;
  onClose: () => void;
  guidance: UserGuidance | null;
  routingContext?: RoutingContext | null;
  flowId?: string;
}

export const AgentGuidanceModal: React.FC<AgentGuidanceModalProps> = ({
  isOpen,
  onClose,
  guidance,
  routingContext,
  flowId,
}) => {
  const navigate = useNavigate();

  if (!guidance) return null;

  const handleNavigate = () => {
    if (routingContext?.target_page) {
      navigate(routingContext.target_page);
    } else if (routingContext?.recommended_page) {
      navigate(routingContext.recommended_page);
    }
    onClose();
  };

  const getActionIcon = (action: string) => {
    if (action.toLowerCase().includes('upload')) return <Upload className="h-4 w-4" />;
    if (action.toLowerCase().includes('retry') || action.toLowerCase().includes('restart')) return <RefreshCcw className="h-4 w-4" />;
    return <ChevronRight className="h-4 w-4" />;
  };

  const getPrimaryActionButton = () => {
    // Determine the primary action based on guidance
    if (guidance.primary_message.toLowerCase().includes('upload')) {
      return (
        <Button onClick={() => {
          navigate('/discovery/data-import');
          onClose();
        }} className="gap-2">
          <Upload className="h-4 w-4" />
          Go to Data Import
        </Button>
      );
    }

    if (routingContext?.target_page) {
      const phaseLabel = routingContext?.phase
        ? routingContext.phase.replace(/_/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase())
        : 'Next Step';
      return (
        <Button onClick={handleNavigate} className="gap-2">
          <ChevronRight className="h-4 w-4" />
          Continue to {phaseLabel}
        </Button>
      );
    }

    return (
      <Button onClick={onClose}>
        Understood
      </Button>
    );
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Info className="h-5 w-5 text-blue-500" />
            Agent Analysis & Guidance
          </DialogTitle>
          <DialogDescription>
            Our intelligent agent has analyzed your flow and provides the following guidance
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          {/* Primary Message */}
          <Alert>
            <AlertCircle className="h-4 w-4" />
            <AlertTitle>Current Status</AlertTitle>
            <AlertDescription className="mt-2 text-base">
              {guidance.primary_message}
            </AlertDescription>
          </Alert>

          {/* User Actions Required */}
          {guidance.user_actions && guidance.user_actions.length > 0 && (
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-medium">Required Actions</CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="space-y-2">
                  {guidance.user_actions.map((action, index) => (
                    <li key={index} className="flex items-start gap-2">
                      {getActionIcon(action)}
                      <span className="text-sm">{action}</span>
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          )}

          {/* Action Items */}
          {guidance.action_items && guidance.action_items.length > 0 && (
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-medium">Next Steps</CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="space-y-2">
                  {guidance.action_items.map((item, index) => (
                    <li key={index} className="flex items-start gap-2">
                      <CheckCircle2 className="h-4 w-4 text-green-500 mt-0.5" />
                      <span className="text-sm">{item}</span>
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          )}

          {/* System Actions (if any) */}
          {guidance.system_actions && guidance.system_actions.length > 0 && (
            <Card className="bg-gray-50">
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-medium text-gray-600">System Actions</CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="space-y-1">
                  {guidance.system_actions.map((action, index) => (
                    <li key={index} className="text-sm text-gray-600">
                      • {action}
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          )}

          {/* Estimated Time */}
          {guidance.estimated_completion_time && (
            <div className="text-sm text-gray-500">
              Estimated completion time: {guidance.estimated_completion_time} minutes
            </div>
          )}
        </div>

        <DialogFooter className="gap-2">
          <Button variant="outline" onClick={onClose}>
            Close
          </Button>
          {getPrimaryActionButton()}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};
