import React, { useState, useEffect } from 'react';
import { Activity, Clock, AlertCircle, CheckCircle, Bot, Brain, Zap, Users } from 'lucide-react';
import { API_CONFIG } from '../config/api';

interface AgentStatus {
  name: string;
  role: string;
  expertise: string;
  specialization: string;
  key_skills: string;
  status: {
    available: boolean;
    currently_working: boolean;
    health: string;
  };
  performance: {
    tasks_completed: number;
    success_rate: string;
    avg_execution_time: string;
  };
}

interface ActiveTask {
  task_id: string;
  agent: string;
  status: string;
  elapsed: string;
  since_activity: string;
  description: string;
  is_hanging: boolean;
  hanging_reason: string;
  llm_calls: number;
  thinking_phases: number;
  progress_indicators: {
    has_started: boolean;
    making_progress: boolean;
    llm_active: boolean;
    thinking_active: boolean;
  };
}

interface MonitoringData {
  success: boolean;
  timestamp: string;
  monitoring: {
    active: boolean;
    active_tasks: number;
    completed_tasks: number;
    hanging_tasks: number;
  };
  agents: {
    available: number;
    capabilities: Record<string, any>;
    system_status: any;
  };
  tasks: {
    active: ActiveTask[];
    hanging: any[];
  };
}

const AgentMonitor: React.FC = () => {
  const [monitoringData, setMonitoringData] = useState<MonitoringData | null>(null);
  const [agentDetails, setAgentDetails] = useState<AgentStatus[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchMonitoringData = async () => {
    try {
      const response = await fetch(`${API_CONFIG.BASE_URL}/api/v1/monitoring/status`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      setMonitoringData(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch monitoring data');
    }
  };

  const fetchAgentDetails = async () => {
    try {
      const response = await fetch(`${API_CONFIG.BASE_URL}/api/v1/monitoring/agents`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      setAgentDetails(data.agents || []);
    } catch (err) {
      console.error('Failed to fetch agent details:', err);
    }
  };

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      await Promise.all([fetchMonitoringData(), fetchAgentDetails()]);
      setLoading(false);
    };

    fetchData();

    // Set up polling for real-time updates
    const interval = setInterval(() => {
      fetchMonitoringData();
      fetchAgentDetails();
    }, 5000); // Update every 5 seconds

    return () => clearInterval(interval);
  }, []);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy':
      case 'available':
        return 'bg-green-100 text-green-800';
      case 'warning':
      case 'busy':
        return 'bg-yellow-100 text-yellow-800';
      case 'error':
      case 'down':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getTaskStatusIcon = (task: ActiveTask) => {
    if (task.is_hanging) {
      return <AlertCircle className="h-4 w-4 text-red-500" />;
    }
    if (task.progress_indicators.thinking_active) {
      return <Brain className="h-4 w-4 text-purple-500 animate-pulse" />;
    }
    if (task.progress_indicators.llm_active) {
      return <Zap className="h-4 w-4 text-blue-500 animate-pulse" />;
    }
    return <Activity className="h-4 w-4 text-green-500" />;
  };

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="animate-pulse">
          <div className="h-6 bg-gray-200 rounded w-1/4 mb-4"></div>
          <div className="space-y-3">
            <div className="h-4 bg-gray-200 rounded"></div>
            <div className="h-4 bg-gray-200 rounded w-5/6"></div>
            <div className="h-4 bg-gray-200 rounded w-4/6"></div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center space-x-2 text-red-600">
          <AlertCircle className="h-5 w-5" />
          <span className="font-medium">Agent Monitoring Error</span>
        </div>
        <p className="text-gray-600 mt-2">{error}</p>
        <button
          onClick={() => {
            setError(null);
            fetchMonitoringData();
            fetchAgentDetails();
          }}
          className="mt-4 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Monitoring Overview */}
      <div className="bg-white rounded-lg shadow">
        <div className="p-6 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold text-gray-900 flex items-center">
              <Bot className="h-6 w-6 mr-2 text-purple-600" />
              Agent Monitoring
            </h2>
            <div className="flex items-center space-x-2">
              <div className={`w-3 h-3 rounded-full ${monitoringData?.monitoring.active ? 'bg-green-500' : 'bg-red-500'}`}></div>
              <span className="text-sm text-gray-600">
                {monitoringData?.monitoring.active ? 'Active' : 'Inactive'}
              </span>
            </div>
          </div>
        </div>
        
        <div className="p-6">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-purple-600">{monitoringData?.agents.available || 0}</div>
              <div className="text-sm text-gray-600">Available Agents</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600">{monitoringData?.monitoring.active_tasks || 0}</div>
              <div className="text-sm text-gray-600">Active Tasks</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">{monitoringData?.monitoring.completed_tasks || 0}</div>
              <div className="text-sm text-gray-600">Completed Tasks</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-red-600">{monitoringData?.monitoring.hanging_tasks || 0}</div>
              <div className="text-sm text-gray-600">Hanging Tasks</div>
            </div>
          </div>
        </div>
      </div>

      {/* Agent Status */}
      <div className="bg-white rounded-lg shadow">
        <div className="p-6 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900 flex items-center">
            <Users className="h-5 w-5 mr-2 text-blue-600" />
            Agent Status
          </h3>
        </div>
        <div className="p-6">
          {agentDetails.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {agentDetails.map((agent) => (
                <div key={agent.name} className="border rounded-lg p-4 hover:shadow-md transition-shadow">
                  <div className="flex items-center justify-between mb-2">
                    <h4 className="font-medium text-gray-900">{agent.role}</h4>
                    <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                      agent.status.currently_working ? getStatusColor('busy') : getStatusColor('available')
                    }`}>
                      {agent.status.currently_working ? 'Busy' : 'Available'}
                    </span>
                  </div>
                  <p className="text-sm text-gray-600 mb-2">{agent.expertise}</p>
                  <div className="text-xs text-gray-500">
                    <div>Skills: {agent.key_skills}</div>
                    <div className="mt-1">Health: {agent.status.health}</div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8 text-gray-500">
              <Bot className="h-12 w-12 mx-auto mb-4 text-gray-300" />
              <p>No agents available</p>
            </div>
          )}
        </div>
      </div>

      {/* Active Tasks */}
      {monitoringData?.tasks.active && monitoringData.tasks.active.length > 0 && (
        <div className="bg-white rounded-lg shadow">
          <div className="p-6 border-b border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900 flex items-center">
              <Activity className="h-5 w-5 mr-2 text-green-600" />
              Active Tasks
            </h3>
          </div>
          <div className="p-6">
            <div className="space-y-4">
              {monitoringData.tasks.active.map((task) => (
                <div key={task.task_id} className={`border rounded-lg p-4 ${task.is_hanging ? 'border-red-200 bg-red-50' : 'border-gray-200'}`}>
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center space-x-2">
                      {getTaskStatusIcon(task)}
                      <span className="font-medium text-gray-900">{task.agent}</span>
                      <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getStatusColor(task.status)}`}>
                        {task.status}
                      </span>
                    </div>
                    <div className="text-sm text-gray-600">
                      <Clock className="h-4 w-4 inline mr-1" />
                      {task.elapsed}
                    </div>
                  </div>
                  <p className="text-sm text-gray-600 mb-2">{task.description}</p>
                  <div className="flex items-center justify-between text-xs text-gray-500">
                    <div>
                      LLM Calls: {task.llm_calls} | Thinking Phases: {task.thinking_phases}
                    </div>
                    {task.is_hanging && (
                      <div className="text-red-600 font-medium">
                        ⚠️ {task.hanging_reason}
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AgentMonitor; 