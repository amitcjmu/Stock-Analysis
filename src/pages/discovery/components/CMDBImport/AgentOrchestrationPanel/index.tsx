import React from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Target, Users, CheckCircle2 } from 'lucide-react';
import { AgentOrchestrationPanelProps } from './types';
import { useAgentOrchestrationState } from './hooks';
import { OverallProgressHeader } from './components/OverallProgressHeader';
import { OverviewTab } from './components/OverviewTab';
import { CrewsTab } from './components/CrewsTab';
import { ResultsTab } from './components/ResultsTab';

const AgentOrchestrationPanel: React.FC<AgentOrchestrationPanelProps> = ({
  flowId,
  flowState,
  onStatusUpdate
}) => {
  const {
    activeTab,
    setActiveTab,
    crews,
    overallProgress,
    currentPhase
  } = useAgentOrchestrationState();

  return (
    <div className="space-y-6">
      {/* Overall Progress Header */}
      <OverallProgressHeader
        overallProgress={overallProgress}
        currentPhase={currentPhase}
        flowId={flowId}
      />

      {/* Crew Orchestration Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="overview">
            <Target className="h-4 w-4 mr-2" />
            Overview
          </TabsTrigger>
          <TabsTrigger value="crews">
            <Users className="h-4 w-4 mr-2" />
            Crews
          </TabsTrigger>
          <TabsTrigger value="results">
            <CheckCircle2 className="h-4 w-4 mr-2" />
            Results
          </TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-4">
          <OverviewTab crews={crews} />
        </TabsContent>

        <TabsContent value="crews" className="space-y-4">
          <CrewsTab crews={crews} />
        </TabsContent>

        <TabsContent value="results" className="space-y-4">
          <ResultsTab flowState={flowState} />
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default AgentOrchestrationPanel;