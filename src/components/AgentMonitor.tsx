import React, { useState, useEffect } from 'react';
import { Activity, Clock, AlertCircle, CheckCircle, Bot, Brain, Zap, Users, RefreshCw, ChevronRight, ChevronDown } from 'lucide-react';
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
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [testingTask, setTestingTask] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
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
    } catch (err) {
      console.error('Failed to fetch agents by phase:', err);
    }
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    try {
      await Promise.all([fetchMonitoringData(), fetchAgentsByPhase()]);
    } finally {
      setRefreshing(false);
    }
  };

  const triggerTestTask = async () => {
    setTestingTask(true);
    try {
      const testData = {
        filename: 'test_monitoring.csv',
        structure: {
          columns: ['Name', 'CI_Type', 'Environment', 'CPU_Cores'],
          total_rows: 2,
          total_columns: 4
        },
        sample_data: [
          { Name: 'TestServer01', CI_Type: 'Server', Environment: 'Production', CPU_Cores: '4' },
          { Name: 'TestApp01', CI_Type: 'Application', Environment: 'Production', CPU_Cores: 'N/A' }
        ]
      };

      const response = await fetch(`${API_CONFIG.BASE_URL}/api/v1/discovery/analyze-cmdb`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(testData),
      });

      if (response.ok) {
        const result = await response.json();
        console.log('Test task completed:', result);
        await handleRefresh();
      }
    } catch (err) {
      console.error('Test task failed:', err);
    } finally {
      setTestingTask(false);
    }
  };

  const handleAgentClick = (agentId: string) => {
    setSelectedAgent(selectedAgent === agentId ? null : agentId);
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
    switch (status) {
      case 'active':
      case 'healthy':
      case 'available':
        return 'bg-green-100 text-green-800';
      case 'planned':
      case 'warning':
      case 'busy':
        return 'bg-yellow-100 text-yellow-800';
      case 'error':
      case 'down':
        return 'bg-red-100 text-red-800';
      case 'in_development':
        return 'bg-blue-100 text-blue-800';
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

  const getPhaseIcon = (phase: string) => {
    const icons: Record<string, JSX.Element> = {
      discovery: <Bot className="h-5 w-5 text-purple-600" />,
      assessment: <Brain className="h-5 w-5 text-blue-600" />,
      planning: <Activity className="h-5 w-5 text-green-600" />,
      migration: <Zap className="h-5 w-5 text-yellow-600" />,
      modernization: <RefreshCw className="h-5 w-5 text-indigo-600" />,
      decommission: <CheckCircle className="h-5 w-5 text-gray-600" />,
      finops: <AlertCircle className="h-5 w-5 text-orange-600" />,
      learning_context: <Users className="h-5 w-5 text-pink-600" />,
      observability: <Activity className="h-5 w-5 text-red-600" />
    };
    return icons[phase] || <Bot className="h-5 w-5 text-gray-600" />;
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
            fetchAgentsByPhase();
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
            <div className="flex items-center space-x-4">
              <button
                onClick={handleRefresh}
                disabled={refreshing}
                className="flex items-center space-x-2 px-3 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                title="Refresh monitoring data"
              >
                <RefreshCw className={`h-4 w-4 ${refreshing ? 'animate-spin' : ''}`} />
                <span>{refreshing ? 'Refreshing...' : 'Refresh'}</span>
              </button>
              <div className="flex items-center space-x-2">
                <div className={`w-3 h-3 rounded-full ${monitoringData?.monitoring.active ? 'bg-green-500' : 'bg-red-500'}`}></div>
                <span className="text-sm text-gray-600">
                  {monitoringData?.monitoring.active ? 'Active' : 'Inactive'}
                </span>
              </div>
            </div>
          </div>
        </div>
        
        <div className="p-6">
          <div className="grid grid-cols-1 md:grid-cols-5 gap-4 mb-6">
            <div className="text-center">
              <div className="text-2xl font-bold text-purple-600">{monitoringData?.agents.total_registered || 0}</div>
              <div className="text-sm text-gray-600">Total Agents</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">{monitoringData?.agents.active_agents || 0}</div>
              <div className="text-sm text-gray-600">Active Agents</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600">{monitoringData?.monitoring.active_tasks || 0}</div>
              <div className="text-sm text-gray-600">Active Tasks</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-orange-600">{monitoringData?.agents.learning_enabled || 0}</div>
              <div className="text-sm text-gray-600">Learning Enabled</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-pink-600">{monitoringData?.agents.cross_page_communication || 0}</div>
              <div className="text-sm text-gray-600">Cross-Page</div>
            </div>
          </div>
          
          {/* Test Task Button */}
          <div className="text-center">
            <button
              onClick={triggerTestTask}
              disabled={testingTask}
              className="px-6 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {testingTask ? 'Running Test Task...' : 'Trigger Test Task'}
            </button>
            <p className="text-sm text-gray-600 mt-2">
              Click to trigger a test CMDB analysis and see agent monitoring in action
            </p>
          </div>
        </div>
      </div>

      {/* Agents by Phase */}
      <div className="bg-white rounded-lg shadow">
        <div className="p-6 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900 flex items-center">
            <Users className="h-5 w-5 mr-2 text-blue-600" />
            Agents by Phase ({Object.keys(agentsByPhase).length} phases)
          </h3>
        </div>
        <div className="p-6">
          {Object.keys(agentsByPhase).length > 0 ? (
            <div className="space-y-4">
              {Object.entries(agentsByPhase).map(([phase, phaseData]) => (
                <div key={phase} className="border rounded-lg">
                  <div 
                    className="flex items-center justify-between p-4 cursor-pointer hover:bg-gray-50"
                    onClick={() => togglePhaseExpansion(phase)}
                  >
                    <div className="flex items-center space-x-3">
                      {getPhaseIcon(phase)}
                      <div>
                        <h4 className="font-medium text-gray-900">{phaseData.phase_name}</h4>
                        <p className="text-sm text-gray-600">
                          {phaseData.total_agents} agents ({phaseData.active_agents} active)
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center space-x-2">
                      <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                        phaseData.active_agents > 0 ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                      }`}>
                        {phaseData.active_agents > 0 ? 'Active' : 'Inactive'}
                      </span>
                      {expandedPhases[phase] ? 
                        <ChevronDown className="h-5 w-5 text-gray-400" /> : 
                        <ChevronRight className="h-5 w-5 text-gray-400" />
                      }
                    </div>
                  </div>
                  
                  {expandedPhases[phase] && (
                    <div className="px-4 pb-4">
                      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                        {phaseData.agents.map((agent) => (
                          <div 
                            key={agent.agent_id} 
                            className="border rounded-lg p-4 hover:shadow-md transition-shadow cursor-pointer"
                            onClick={() => handleAgentClick(agent.agent_id)}
                          >
                            <div className="flex items-center justify-between mb-2">
                              <h5 className="font-medium text-gray-900 text-sm">{agent.name}</h5>
                              <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getStatusColor(agent.status.current_status)}`}>
                                {agent.status.current_status}
                              </span>
                            </div>
                            <p className="text-xs text-gray-600 mb-2">{agent.role}</p>
                            <div className="text-xs text-gray-500 mb-2">
                              <div>Expertise: {agent.expertise.length > 50 ? agent.expertise.substring(0, 50) + '...' : agent.expertise}</div>
                            </div>
                            
                            {/* Features badges */}
                            <div className="flex flex-wrap gap-1 mb-2">
                              {agent.features.learning_enabled && (
                                <span className="inline-flex px-1 py-0.5 text-xs bg-blue-100 text-blue-800 rounded">Learning</span>
                              )}
                              {agent.features.cross_page_communication && (
                                <span className="inline-flex px-1 py-0.5 text-xs bg-pink-100 text-pink-800 rounded">Cross-Page</span>
                              )}
                              {agent.features.modular_handlers && (
                                <span className="inline-flex px-1 py-0.5 text-xs bg-green-100 text-green-800 rounded">Modular</span>
                              )}
                            </div>
                            
                            <div className="text-xs text-gray-500">
                              <div>Health: {agent.status.health}</div>
                              <div>Tasks: {agent.performance.tasks_completed}</div>
                            </div>
                            <div className="mt-2 text-xs text-blue-600">
                              Click for details →
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
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

      {/* Selected Agent Details */}
      {selectedAgent && (
        <div className="bg-white rounded-lg shadow">
          <div className="p-6 border-b border-gray-200">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold text-gray-900 flex items-center">
                <Bot className="h-5 w-5 mr-2 text-purple-600" />
                Agent Details
              </h3>
              <button
                onClick={() => setSelectedAgent(null)}
                className="text-gray-400 hover:text-gray-600"
              >
                ✕
              </button>
            </div>
          </div>
          <div className="p-6">
            {/* Find and display selected agent details */}
            {(() => {
              const agent = Object.values(agentsByPhase)
                .flatMap(phase => phase.agents)
                .find(a => a.agent_id === selectedAgent);
              
              if (!agent) return <p>Agent not found</p>;
              
              return (
                <div className="space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                      <h4 className="font-medium text-gray-900 mb-2">Basic Information</h4>
                      <div className="space-y-2 text-sm">
                        <div><span className="font-medium">Name:</span> {agent.name}</div>
                        <div><span className="font-medium">Role:</span> {agent.role}</div>
                        <div><span className="font-medium">Version:</span> {agent.version}</div>
                        <div><span className="font-medium">Status:</span> 
                          <span className={`ml-2 inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getStatusColor(agent.status.current_status)}`}>
                            {agent.status.current_status}
                          </span>
                        </div>
                      </div>
                    </div>
                    
                    <div>
                      <h4 className="font-medium text-gray-900 mb-2">Performance</h4>
                      <div className="space-y-2 text-sm">
                        <div><span className="font-medium">Tasks Completed:</span> {agent.performance.tasks_completed}</div>
                        <div><span className="font-medium">Success Rate:</span> {agent.performance.success_rate}</div>
                        <div><span className="font-medium">Avg Execution Time:</span> {agent.performance.avg_execution_time}</div>
                        <div><span className="font-medium">Health:</span> {agent.status.health}</div>
                      </div>
                    </div>
                  </div>
                  
                  <div>
                    <h4 className="font-medium text-gray-900 mb-2">Description</h4>
                    <p className="text-sm text-gray-600">{agent.description}</p>
                  </div>
                  
                  <div>
                    <h4 className="font-medium text-gray-900 mb-2">Expertise</h4>
                    <p className="text-sm text-gray-600">{agent.expertise}</p>
                  </div>
                  
                  <div>
                    <h4 className="font-medium text-gray-900 mb-2">Specialization</h4>
                    <p className="text-sm text-gray-600">{agent.specialization}</p>
                  </div>
                  
                  <div>
                    <h4 className="font-medium text-gray-900 mb-2">Key Skills</h4>
                    <div className="flex flex-wrap gap-2">
                      {agent.key_skills.map((skill, index) => (
                        <span key={index} className="inline-flex px-2 py-1 text-xs bg-blue-100 text-blue-800 rounded">
                          {skill}
                        </span>
                      ))}
                    </div>
                  </div>
                  
                  <div>
                    <h4 className="font-medium text-gray-900 mb-2">Capabilities</h4>
                    <div className="flex flex-wrap gap-2">
                      {agent.capabilities.map((capability, index) => (
                        <span key={index} className="inline-flex px-2 py-1 text-xs bg-green-100 text-green-800 rounded">
                          {capability}
                        </span>
                      ))}
                    </div>
                  </div>
                  
                  <div>
                    <h4 className="font-medium text-gray-900 mb-2">API Endpoints</h4>
                    <div className="space-y-1">
                      {agent.api_endpoints.map((endpoint, index) => (
                        <code key={index} className="block text-xs bg-gray-100 p-2 rounded">
                          {endpoint}
                        </code>
                      ))}
                    </div>
                  </div>
                </div>
              );
            })()}
          </div>
        </div>
      )}

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

      {/* No Active Tasks Message */}
      {(!monitoringData?.tasks.active || monitoringData.tasks.active.length === 0) && !selectedAgent && (
        <div className="bg-white rounded-lg shadow">
          <div className="p-6 border-b border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900 flex items-center">
              <Activity className="h-5 w-5 mr-2 text-gray-400" />
              Active Tasks
            </h3>
          </div>
          <div className="p-6">
            <div className="text-center py-8 text-gray-500">
              <Activity className="h-12 w-12 mx-auto mb-4 text-gray-300" />
              <p className="text-lg font-medium mb-2">No Active Tasks</p>
              <p>Tasks will appear here when agents are processing requests</p>
              <p className="text-sm mt-2">Use the "Trigger Test Task" button above to see agent monitoring in action</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AgentMonitor; 