import React, { useState } from 'react';
import { useSessions } from '@/contexts/SessionContext';
import { Button } from '@/components/ui/button';
import { SessionSelector } from './SessionSelector';
import { SessionMergeWizard } from './SessionMergeWizard';
import { GitMerge } from 'lucide-react';

export const SessionManager: React.FC = () => {
  const { data: sessions = [] } = useSessions();
  const [isMergeDialogOpen, setIsMergeDialogOpen] = useState(false);

  return (
    <div className="flex items-center gap-2">
      <SessionSelector />
      
      {sessions.length > 1 && (
        <Button
          variant="outline"
          size="icon"
          onClick={() => setIsMergeDialogOpen(true)}
          title="Merge sessions"
        >
          <GitMerge className="h-4 w-4" />
        </Button>
      )}

      {/* Merge Sessions Wizard */}
      <SessionMergeWizard
        open={isMergeDialogOpen}
        onOpenChange={setIsMergeDialogOpen}
      />
    </div>
  );
};

export default SessionManager;
