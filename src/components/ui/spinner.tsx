import type React from 'react';
import { Loader2 } from 'lucide-react';

export const Spinner = () => {
  return (
    <div className="flex items-center justify-center">
      <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
    </div>
  );
};
