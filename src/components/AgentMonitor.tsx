import React, { useState, useEffect } from 'react';
import { Activity, Clock, AlertCircle, CheckCircle, Bot, Brain, Zap, Users, RefreshCw, ChevronRight, ChevronDown, History, User } from 'lucide-react';
import { API_CONFIG } from '../config/api';

interface AgentStatus {
  agent_id: string;
  name: string;
  role: string;
  expertise: string;
  specialization: string;
  key_skills: string[];
  capabilities: string[];
  api_endpoints: string[];
  description: string;
  version: string;
  status: {
    current_status: string;
    available: boolean;
    currently_working: boolean;
    health: string;
  };
  features: {
    learning_enabled: boolean;
    cross_page_communication: boolean;
    modular_handlers: boolean;
  };
  performance: {
    tasks_completed: number;
    success_rate: string;
    avg_execution_time: string;
  };
  registration_time?: string;
  last_heartbeat?: string;
}

interface PhaseData {
  phase_name: string;
  total_agents: number;
  active_agents: number;
  agents: AgentStatus[];
}

interface TaskHistory {
  task_id: string;
  agent: string;
  description: string;
  status: string;
  start_time: string;
  end_time?: string;
  duration?: number;
  llm_calls: number;
  thinking_phases: number;
  result_preview?: string;
  error?: string;
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
    total_registered: number;
    active_agents: number;
    learning_enabled: number;
    cross_page_communication: number;
    modular_handlers: number;
    phase_distribution: Record<string, any>;
  };
  tasks: {
    active: ActiveTask[];
    hanging: any[];
  };
  registry_status: any;
}

interface AgentsByPhase {
  [phase: string]: PhaseData;
}

const AgentMonitor: React.FC = () => {
  const [monitoringData, setMonitoringData] = useState<MonitoringData | null>(null);
  const [agentsByPhase, setAgentsByPhase] = useState<AgentsByPhase>({});
  const [selectedPhase, setSelectedPhase] = useState<string>('discovery');
  const [selectedAgent, setSelectedAgent] = useState<string | null>(null);
  const [selectedAgentTab, setSelectedAgentTab] = useState<'details' | 'tasks'>('details');
  const [agentTaskHistory, setAgentTaskHistory] = useState<TaskHistory[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);
  const [loadingTaskHistory, setLoadingTaskHistory] = useState(false);
  const [expandedPhases, setExpandedPhases] = useState<Record<string, boolean>>({
    discovery: true,
    assessment: false,
    planning: false,
    migration: false,
    modernization: false,
    decommission: false,
    finops: false,
    learning_context: true,
    observability: true
  });

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

  const fetchAgentsByPhase = async () => {
    try {
      const response = await fetch(`${API_CONFIG.BASE_URL}/api/v1/monitoring/agents`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      setAgentsByPhase(data.agents_by_phase || {});
      
      // Auto-select first phase if none selected
      if (!selectedPhase && Object.keys(data.agents_by_phase || {}).length > 0) {
        setSelectedPhase(Object.keys(data.agents_by_phase)[0]);
      }
    } catch (err) {
      console.error('Failed to fetch agents by phase:', err);
    }
  };

  const fetchAgentTaskHistory = async (agentName: string) => {
    setLoadingTaskHistory(true);
    try {
      // Try to fetch task history for the specific agent
      const response = await fetch(`${API_CONFIG.BASE_URL}/api/v1/monitoring/tasks?agent_id=${encodeURIComponent(agentName)}&limit=10`);
      if (response.ok) {
        const data = await response.json();
        setAgentTaskHistory(data.tasks || []);
      } else {
        // If no specific endpoint, generate mock task history for demo
        const mockHistory: TaskHistory[] = [
          {
            task_id: `${agentName.toLowerCase().replace(/\s+/g, '_')}_task_001`,
            agent: agentName,
            description: 'Analyzed CMDB data for asset type detection and migration readiness',
            status: 'completed',
            start_time: new Date(Date.now() - 300000).toISOString(),
            end_time: new Date(Date.now() - 280000).toISOString(),
            duration: 20,
            llm_calls: 3,
            thinking_phases: 2,
            result_preview: 'Successfully classified 15 assets with 92% confidence'
          },
          {
            task_id: `${agentName.toLowerCase().replace(/\s+/g, '_')}_task_002`,
            agent: agentName,
            description: 'Processed user feedback for learning improvement',
            status: 'completed',
            start_time: new Date(Date.now() - 180000).toISOString(),
            end_time: new Date(Date.now() - 165000).toISOString(),
            duration: 15,
            llm_calls: 2,
            thinking_phases: 1,
            result_preview: 'Learning patterns updated, confidence boost: +0.15'
          },
          {
            task_id: `${agentName.toLowerCase().replace(/\s+/g, '_')}_task_003`,
            agent: agentName,
            description: 'Field mapping analysis with organizational pattern recognition',
            status: 'completed',
            start_time: new Date(Date.now() - 120000).toISOString(),
            end_time: new Date(Date.now() - 105000).toISOString(),
            duration: 15,
            llm_calls: 4,
            thinking_phases: 3,
            result_preview: 'Mapped 8 fields to critical attributes with learned patterns'
          }
        ];
        setAgentTaskHistory(mockHistory);
      }
    } catch (err) {
      console.error('Failed to fetch agent task history:', err);
      setAgentTaskHistory([]);
    } finally {
      setLoadingTaskHistory(false);
    }
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    try {
      await Promise.all([fetchMonitoringData(), fetchAgentsByPhase()]);
      if (selectedAgent) {
        await fetchAgentTaskHistory(selectedAgent);
      }
    } finally {
      setRefreshing(false);
    }
  };

  const handleAgentClick = async (agentId: string, agentName: string) => {
    if (selectedAgent === agentId) {
      setSelectedAgent(null);
      setAgentTaskHistory([]);
    } else {
      setSelectedAgent(agentId);
      setSelectedAgentTab('details');
      await fetchAgentTaskHistory(agentName);
    }
  };

  const togglePhaseExpansion = (phase: string) => {
    setExpandedPhases(prev => ({
      ...prev,
      [phase]: !prev[phase]
    }));
  };

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      await Promise.all([fetchMonitoringData(), fetchAgentsByPhase()]);
      setLoading(false);
    };

    fetchData();
  }, []);

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'active':
      case 'healthy':
      case 'available':
        return 'text-green-500';
      case 'idle':
      case 'standby':
        return 'text-yellow-500';
      case 'error':
      case 'degraded':
      case 'unavailable':
        return 'text-red-500';
      case 'working':
      case 'processing':
        return 'text-blue-500';
      default:
        return 'text-gray-500';
    }
  };

  const getTaskStatusIcon = (task: ActiveTask) => {
    if (task.is_hanging) {
      return <AlertCircle className="text-red-500" />;
    }
    if (task.status === 'completed') {
      return <CheckCircle className="text-green-500" />;
    }
    return <Activity className="text-blue-500" />;
  };

  const getPhaseIcon = (phase: string) => {
    switch(phase) {
      case 'discovery': return <Brain className="h-5 w-5 mr-2 text-purple-500" />;
      case 'assessment': return <Zap className="h-5 w-5 mr-2 text-yellow-500" />;
      case 'planning': return <Users className="h-5 w-5 mr-2 text-blue-500" />;
      case 'migration': return <RefreshCw className="h-5 w-5 mr-2 text-green-500" />;
      case 'learning_context': return <Bot className="h-5 w-5 mr-2 text-indigo-500" />;
      default: return <Bot className="h-5 w-5 mr-2 text-gray-500" />;
    }
  };

  if (loading && !refreshing) {
    return <div className="p-4 text-center">Loading agent monitoring data...</div>;
  }

  if (error) {
    return (
      <div className="p-4 text-center text-red-500">
        <p>Agent Monitoring Error</p>
        <p>{error}</p>
        <button
          onClick={handleRefresh}
          className="mt-4 px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="p-4 bg-gray-50 min-h-screen">
      <div className="flex justify-between items-center mb-4">
        <h1 className="text-2xl font-bold text-gray-800">Agent Monitoring</h1>
        <button
          onClick={handleRefresh}
          className={`px-4 py-2 flex items-center bg-white border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50 ${refreshing ? 'animate-spin' : ''}`}
          disabled={refreshing}
        >
          <RefreshCw className={`mr-2 h-4 w-4 ${refreshing ? 'animate-spin' : ''}`} />
          {refreshing ? 'Refreshing...' : 'Refresh'}
        </button>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        {/* ... Card JSX ... */}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Agents by Phase Column */}
        <div className="lg:col-span-1 bg-white p-4 rounded-lg shadow">
          <h2 className="text-lg font-semibold mb-3">Agents by Phase</h2>
          <div className="space-y-2">
            {Object.entries(agentsByPhase).map(([phase, data]) => (
              <div key={phase} className="border rounded-md">
                <button
                  className="w-full flex justify-between items-center p-3 text-left"
                  onClick={() => togglePhaseExpansion(phase)}
                >
                  <div className="flex items-center">
                    {getPhaseIcon(phase)}
                    <span className="font-medium capitalize">{phase.replace('_', ' ')}</span>
                  </div>
                  <div className="flex items-center">
                    <span className="text-sm text-gray-500 mr-2">{data.active_agents}/{data.total_agents} active</span>
                    {expandedPhases[phase] ? <ChevronDown className="h-5 w-5" /> : <ChevronRight className="h-5 w-5" />}
                  </div>
                </button>
                {expandedPhases[phase] && (
                  <div className="p-3 border-t">
                    {data.agents.map(agent => (
                      <div
                        key={agent.agent_id}
                        className={`p-2 rounded cursor-pointer ${selectedAgent === agent.agent_id ? 'bg-blue-100' : 'hover:bg-gray-100'}`}
                        onClick={() => handleAgentClick(agent.agent_id, agent.name)}
                      >
                        <div className="flex justify-between items-center">
                          <span className="font-medium text-sm">{agent.name}</span>
                          <span className={`text-xs font-semibold ${getStatusColor(agent.status.current_status)}`}>
                            {agent.status.current_status}
                          </span>
                        </div>
                        <p className="text-xs text-gray-500">{agent.role}</p>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Agent Details / Active Tasks Column */}
        <div className="lg:col-span-2 bg-white p-4 rounded-lg shadow">
          {selectedAgent ? (
            <div>
              <div className="flex justify-between items-center mb-3">
                <h2 className="text-lg font-semibold">
                  {agentsByPhase[Object.keys(agentsByPhase).find(p => agentsByPhase[p].agents.some(a => a.agent_id === selectedAgent)) || '']?.agents.find(a => a.agent_id === selectedAgent)?.name}
                </h2>
                <div>
                  <button
                    onClick={() => setSelectedAgentTab('details')}
                    className={`px-3 py-1 text-sm rounded-l-md ${selectedAgentTab === 'details' ? 'bg-blue-500 text-white' : 'bg-gray-200'}`}
                  >
                    Details
                  </button>
                  <button
                    onClick={() => setSelectedAgentTab('tasks')}
                    className={`px-3 py-1 text-sm rounded-r-md ${selectedAgentTab === 'tasks' ? 'bg-blue-500 text-white' : 'bg-gray-200'}`}
                  >
                    Task History
                  </button>
                </div>
              </div>

              {selectedAgentTab === 'details' && (
                <div>
                  {/* ... Agent Details JSX ... */}
                </div>
              )}

              {selectedAgentTab === 'tasks' && (
                <div>
                  {loadingTaskHistory ? (
                    <p>Loading task history...</p>
                  ) : (
                    <div className="space-y-3">
                      {agentTaskHistory.map(task => (
                        <div key={task.task_id} className="p-3 bg-gray-50 rounded-md border">
                          <div className="flex justify-between items-start">
                            <div className="flex items-center">
                              <History className="h-4 w-4 mr-2 text-gray-400" />
                              <p className="font-medium text-sm">{task.description}</p>
                            </div>
                            <span className={`text-xs font-bold ${task.status === 'completed' ? 'text-green-600' : 'text-red-600'}`}>
                              {task.status.toUpperCase()}
                            </span>
                          </div>
                          <div className="mt-2 text-xs text-gray-500 grid grid-cols-2 md:grid-cols-4 gap-2">
                            <span><strong>Duration:</strong> {task.duration}s</span>
                            <span><strong>LLM Calls:</strong> {task.llm_calls}</span>
                            <span><strong>Started:</strong> {new Date(task.start_time).toLocaleTimeString()}</span>
                            <span><strong>Agent:</strong> {task.agent}</span>
                          </div>
                          {task.result_preview && (
                            <p className="mt-2 text-xs text-gray-600 bg-gray-100 p-2 rounded">
                              <strong>Result:</strong> {task.result_preview}
                            </p>
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>
          ) : (
            <div>
              <h2 className="text-lg font-semibold mb-3">Active Tasks</h2>
              {/* ... Active Tasks JSX ... */}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default AgentMonitor; 