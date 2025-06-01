import React from 'react';
import Sidebar from '../components/Sidebar';
import AgentMonitor from '../components/AgentMonitor';
import { Bot } from 'lucide-react';

const AgentMonitoring = () => {
  return (
    <div className="min-h-screen bg-gray-50 flex">
      <Sidebar />
      <div className="flex-1 ml-64">
        <main className="p-8">
          <div className="max-w-7xl mx-auto">
            <div className="mb-8">
              <h1 className="text-3xl font-bold text-gray-900 mb-2 flex items-center">
                <Bot className="h-8 w-8 mr-3 text-purple-600" />
                Agent Monitoring
              </h1>
              <p className="text-gray-600">
                Monitor and observe the performance of AI agents across all migration phases. 
                Track agent status, task execution, and detailed activity history in real-time.
              </p>
            </div>

            <AgentMonitor />
          </div>
        </main>
      </div>
    </div>
  );
};

export default AgentMonitoring; 