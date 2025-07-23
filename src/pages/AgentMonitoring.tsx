import type React from 'react';
import Sidebar from '../components/Sidebar';
import FlowCrewAgentMonitor from '../components/FlowCrewAgentMonitor';
import { Network } from 'lucide-react';

const AgentMonitoring = () => {
  return (
    <div className="min-h-screen bg-gray-50 flex">
      <Sidebar />
      <div className="flex-1 ml-64">
        <main className="p-8">
          <div className="max-w-7xl mx-auto">
            <div className="mb-8">
              <h1 className="text-3xl font-bold text-gray-900 mb-2 flex items-center">
                <Network className="h-8 w-8 mr-3 text-blue-600" />
                Flow & Agent Monitoring
              </h1>
              <p className="text-gray-600">
                Monitor and observe the performance of CrewAI Discovery Flows, Crews, and Agents in real-time. 
                Track flow progress, crew coordination, agent collaboration, and detailed execution analytics.
              </p>
            </div>

            <FlowCrewAgentMonitor />
          </div>
        </main>
      </div>
    </div>
  );
};

export default AgentMonitoring; 