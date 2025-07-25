import React from 'react';
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';

interface ApplicationTabsProps {
  applications: string[];
  selectedApp: string;
  onAppSelect: (appId: string) => void;
  getApplicationName: (appId: string) => string;
}

export const ApplicationTabs: React.FC<ApplicationTabsProps> = ({
  applications,
  selectedApp,
  onAppSelect,
  getApplicationName
}) => {
  if (applications.length <= 1) {
    return null;
  }

  return (
    <div className="space-y-2">
      <div className="flex items-center space-x-2">
        <h3 className="text-sm font-medium text-gray-700">Application:</h3>
        <Badge variant="outline">{applications.length} applications selected</Badge>
      </div>

      <Tabs value={selectedApp} onValueChange={onAppSelect}>
        <TabsList className="grid w-full" style={{ gridTemplateColumns: `repeat(${Math.min(applications.length, 4)}, 1fr)` }}>
          {applications.slice(0, 4).map((appId) => (
            <TabsTrigger
              key={appId}
              value={appId}
              className="truncate text-xs px-2"
            >
              {getApplicationName(appId)}
            </TabsTrigger>
          ))}
        </TabsList>

        {applications.length > 4 && (
          <div className="mt-2 p-2 bg-gray-50 rounded-lg">
            <p className="text-xs text-gray-600 mb-2">Additional applications:</p>
            <div className="flex flex-wrap gap-1">
              {applications.slice(4).map((appId) => (
                <button
                  key={appId}
                  onClick={() => onAppSelect(appId)}
                  className={cn(
                    "px-2 py-1 text-xs rounded-md border transition-colors",
                    selectedApp === appId
                      ? "bg-blue-100 text-blue-700 border-blue-200"
                      : "bg-white text-gray-600 border-gray-200 hover:bg-gray-50"
                  )}
                >
                  {getApplicationName(appId)}
                </button>
              ))}
            </div>
          </div>
        )}
      </Tabs>
    </div>
  );
};
