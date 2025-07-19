/**
 * Status Icon Component
 * 
 * Renders appropriate icon based on task status.
 */

import React from 'react';
import { 
  CheckCircle, 
  AlertCircle, 
  Clock, 
  PlayCircle 
} from 'lucide-react';

interface StatusIconProps {
  status: string;
}

const StatusIcon: React.FC<StatusIconProps> = ({ status }) => {
  switch (status) {
    case 'completed': return <CheckCircle className="h-4 w-4" />;
    case 'in_progress': return <PlayCircle className="h-4 w-4" />;
    case 'planned': return <Clock className="h-4 w-4" />;
    case 'blocked': return <AlertCircle className="h-4 w-4" />;
    case 'failed': return <AlertCircle className="h-4 w-4" />;
    default: return <Clock className="h-4 w-4" />;
  }
};

export default StatusIcon;