import React from 'react';
import { Brain } from 'lucide-react';

/**
 * Stock analysis uses Anthropic Claude only; this is a read-only indicator.
 */
export const ModelSelector: React.FC<{ className?: string }> = ({
  className = '',
}) => {
  return (
    <div
      className={`flex items-center gap-2 text-sm text-muted-foreground ${className}`}
    >
      <Brain className="h-4 w-4 shrink-0" />
      <span>Claude (Anthropic)</span>
    </div>
  );
};
