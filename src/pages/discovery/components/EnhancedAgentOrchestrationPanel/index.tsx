import React from 'react'
import { useState } from 'react'
import { useEffect } from 'react'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';

// Components
import { OverallProgress } from './components/OverallProgress';
import { CrewCard } from './components/CrewCard';
import { CollaborationTab } from './components/tabs/CollaborationTab';
import { PlanningTab } from './components/tabs/PlanningTab';
import { MemoryTab } from './components/tabs/MemoryTab';

// Hooks
import { useEnhancedMonitoring } from './hooks/useEnhancedMonitoring';

// Types and Constants
import type { EnhancedAgentOrchestrationPanelProps } from './types';
import { TAB_ITEMS } from './constants';

const EnhancedAgentOrchestrationPanel: React.FC<EnhancedAgentOrchestrationPanelProps> = ({
  flowId,
  flowState,
  onStatusUpdate
}) => {
  const [activeTab, setActiveTab] = useState('overview');

  const {
    crews,
    collaborationData,
    planningData,
    memoryAnalytics,
    loading
  } = useEnhancedMonitoring(flowId, flowState);

  // Update parent component when status changes
  useEffect(() => {
    if (onStatusUpdate) {
      const overallProgress = Math.round(
        crews.reduce((sum, crew) => sum + crew.progress, 0) / crews.length
      );
      const activeCrews = crews.filter(c => c.status === 'running').length;
      const completedCrews = crews.filter(c => c.status === 'completed').length;

      onStatusUpdate({
        overallProgress,
        activeCrews,
        completedCrews,
        crews
      });
    }
  }, [crews, onStatusUpdate]);

  return (
    <div className="w-full space-y-4">
      <OverallProgress crews={crews} />

      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="grid grid-cols-5 w-full">
          {TAB_ITEMS.map(tab => (
            <TabsTrigger key={tab.value} value={tab.value}>
              {tab.label}
            </TabsTrigger>
          ))}
        </TabsList>

        <TabsContent value="overview" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {crews.slice(0, 4).map((crew, idx) => (
              <CrewCard
                key={idx}
                crew={crew}
                isActive={crew.status === 'running'}
              />
            ))}
          </div>
        </TabsContent>

        <TabsContent value="crews" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {crews.map((crew, idx) => (
              <CrewCard
                key={idx}
                crew={crew}
                isActive={crew.status === 'running'}
              />
            ))}
          </div>
        </TabsContent>

        <TabsContent value="collaboration">
          <CollaborationTab collaborationData={collaborationData} />
        </TabsContent>

        <TabsContent value="planning">
          <PlanningTab planningData={planningData} />
        </TabsContent>

        <TabsContent value="memory">
          <MemoryTab memoryAnalytics={memoryAnalytics} />
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default EnhancedAgentOrchestrationPanel;
