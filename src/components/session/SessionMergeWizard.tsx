import React, { useState, useMemo } from 'react';
import { useSessions, useMergeSessions } from '@/contexts/SessionContext';
import { useAuth } from '@/contexts/AuthContext';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { Label } from '@/components/ui/label';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { AlertCircle, GitMerge } from 'lucide-react';

type MergeStrategy = 'preserve_target' | 'overwrite' | 'merge';

const mergeStrategyDescriptions: Record<MergeStrategy, string> = {
  preserve_target: 'Keep all data from the target session, only add new items from source',
  overwrite: 'Replace all data in target with data from source',
  merge: 'Combine data from both sessions, resolving conflicts in favor of the target',
};

interface SessionMergeWizardProps {
    open: boolean;
    onOpenChange: (open: boolean) => void;
}

export const SessionMergeWizard: React.FC<SessionMergeWizardProps> = ({
  open,
  onOpenChange,
}) => {
  const { currentSessionId } = useAuth();
  const { data: sessions = [] } = useSessions();
  const mergeSessionsMutation = useMergeSessions();

  const [sourceSessionId, setSourceSessionId] = useState<string>('');
  const [targetSessionId, setTargetSessionId] = useState<string>('');
  const [strategy, setStrategy] = useState<MergeStrategy>('preserve_target');

  const availableSessions = useMemo(() => {
    return sessions.filter(session => session.id !== currentSessionId);
  }, [sessions, currentSessionId]);

  const handleMerge = async () => {
    if (!sourceSessionId || !targetSessionId) return;
    
    try {
      await mergeSessionsMutation.mutateAsync({ sourceSessionId, targetSessionId, strategy });
      onOpenChange(false);
    } catch (error) {
      // Error is handled by the hook's onError callback
    }
  };

  const resetForm = () => {
    setSourceSessionId('');
    setTargetSessionId('');
    setStrategy('preserve_target');
  };

  return (
    <Dialog open={open} onOpenChange={(open) => {
      if (!open) resetForm();
      onOpenChange(open);
    }}>
      <DialogContent className="sm:max-w-[600px]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <GitMerge className="h-5 w-5" />
            Merge Sessions
          </DialogTitle>
          <DialogDescription>
            Combine data from two sessions. Select a source and target session, then choose a merge strategy.
          </DialogDescription>
        </DialogHeader>

        <div className="grid gap-6 py-4">
          <Alert>
            <AlertCircle className="h-4 w-4" />
            <AlertTitle>Heads up!</AlertTitle>
            <AlertDescription className="mt-2">
              Merging sessions cannot be undone. The target session will be modified with data from the source session.
            </AlertDescription>
          </Alert>

          <div className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="source-session">Source Session</Label>
                <select
                  id="source-session"
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                  value={sourceSessionId}
                  onChange={(e) => setSourceSessionId(e.target.value)}
                  disabled={mergeSessionsMutation.isPending}
                >
                  <option value="">Select a session</option>
                  {availableSessions.map((session) => (
                    <option key={session.id} value={session.id}>
                      {session.name}
                    </option>
                  ))}
                </select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="target-session">Target Session</Label>
                <select
                  id="target-session"
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                  value={targetSessionId}
                  onChange={(e) => setTargetSessionId(e.target.value)}
                  disabled={mergeSessionsMutation.isPending || !sourceSessionId}
                >
                  <option value="">Select a session</option>
                  {availableSessions
                    .filter(session => session.id !== sourceSessionId)
                    .map((session) => (
                      <option key={session.id} value={session.id}>
                        {session.name}
                      </option>
                    ))}
                </select>
              </div>
            </div>

            {sourceSessionId && targetSessionId && (
              <div className="space-y-4 pt-4 border-t">
                <h4 className="font-medium">Merge Strategy</h4>
                <RadioGroup
                  value={strategy}
                  onValueChange={(value) => setStrategy(value as MergeStrategy)}
                  className="space-y-2"
                >
                  {Object.entries(mergeStrategyDescriptions).map(([value, description]) => (
                    <div key={value} className="flex items-start space-x-3 space-y-0">
                      <RadioGroupItem value={value} id={value} />
                      <div className="space-y-1">
                        <Label htmlFor={value} className="capitalize">
                          {value.replace('_', ' ')}
                        </Label>
                        <p className="text-sm text-muted-foreground">
                          {description}
                        </p>
                      </div>
                    </div>
                  ))}
                </RadioGroup>
              </div>
            )}
          </div>
        </div>

        <DialogFooter>
          <Button
            variant="outline"
            onClick={() => {
              resetForm();
              onOpenChange(false);
            }}
            disabled={mergeSessionsMutation.isPending}
          >
            Cancel
          </Button>
          <Button
            type="button"
            onClick={handleMerge}
            disabled={!sourceSessionId || !targetSessionId || mergeSessionsMutation.isPending}
          >
            {mergeSessionsMutation.isPending ? 'Merging...' : 'Merge Sessions'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};
