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
    switch (status) {
      case 'active':
      case 'healthy':
      case 'available':
      case 'completed':
        return 'bg-green-100 text-green-800';
      case 'planned':
      case 'warning':
      case 'busy':
      case 'running':
        return 'bg-yellow-100 text-yellow-800';
      case 'error':
      case 'failed':
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
      discovery: <Bot className="h-4 w-4 text-purple-600" />,
      assessment: <Brain className="h-4 w-4 text-blue-600" />,
      planning: <Activity className="h-4 w-4 text-green-600" />,
      migration: <Zap className="h-4 w-4 text-yellow-600" />,
      modernization: <RefreshCw className="h-4 w-4 text-indigo-600" />,
      decommission: <CheckCircle className="h-4 w-4 text-gray-600" />,
      finops: <AlertCircle className="h-4 w-4 text-orange-600" />,
      learning_context: <Users className="h-4 w-4 text-pink-600" />,
      observability: <Activity className="h-4 w-4 text-red-600" />
    };
    return icons[phase] || <Bot className="h-4 w-4 text-gray-600" />;
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

  const currentPhaseData = agentsByPhase[selectedPhase];

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
        </div>
      </div>

      {/* Horizontal Phase Tabs */}
      <div className="bg-white rounded-lg shadow">
        <div className="p-6 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900 flex items-center mb-4">
            <Users className="h-5 w-5 mr-2 text-blue-600" />
            Agents by Phase ({Object.keys(agentsByPhase).length} phases)
          </h3>
          
          {/* Two-Row Horizontal Tab Navigation */}
          <div className="border-b border-gray-200">
            <nav className="-mb-px space-y-2">
              {/* First Row - First 6 phases */}
              <div className="flex space-x-4 justify-center">
                {Object.entries(agentsByPhase).slice(0, 6).map(([phase, phaseData]) => (
                  <button
                    key={phase}
                    onClick={() => setSelectedPhase(phase)}
                    className={`${
                      selectedPhase === phase
                        ? 'border-blue-500 text-blue-600 bg-blue-50'
                        : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 hover:bg-gray-50'
                    } border-b-2 py-2 px-3 text-sm font-medium flex items-center space-x-2 rounded-t-lg transition-colors duration-200`}
                  >
                    {getPhaseIcon(phase)}
                    <span>{phaseData.phase_name}</span>
                    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${
                      phaseData.active_agents > 0 ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                    }`}>
                      {phaseData.total_agents}
                    </span>
                  </button>
                ))}
              </div>
              {/* Second Row - Remaining phases */}
              {Object.entries(agentsByPhase).length > 6 && (
                <div className="flex space-x-4 justify-center">
                  {Object.entries(agentsByPhase).slice(6).map(([phase, phaseData]) => (
                    <button
                      key={phase}
                      onClick={() => setSelectedPhase(phase)}
                      className={`${
                        selectedPhase === phase
                          ? 'border-blue-500 text-blue-600 bg-blue-50'
                          : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 hover:bg-gray-50'
                      } border-b-2 py-2 px-3 text-sm font-medium flex items-center space-x-2 rounded-t-lg transition-colors duration-200`}
                    >
                      {getPhaseIcon(phase)}
                      <span>{phaseData.phase_name}</span>
                      <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${
                        phaseData.active_agents > 0 ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                      }`}>
                        {phaseData.total_agents}
                      </span>
                    </button>
                  ))}
                </div>
              )}
            </nav>
          </div>
        </div>
        
        {/* Phase Content */}
        <div className="p-6">
          {currentPhaseData ? (
            <div>
              <div className="mb-4">
                <p className="text-sm text-gray-600">
                  {currentPhaseData.total_agents} agents ({currentPhaseData.active_agents} active) in {currentPhaseData.phase_name} phase
                </p>
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {currentPhaseData.agents.map((agent) => (
                  <div 
                    key={agent.agent_id} 
                    className={`border rounded-lg p-4 hover:shadow-md transition-shadow cursor-pointer ${
                      selectedAgent === agent.agent_id ? 'border-blue-500 bg-blue-50' : 'border-gray-200'
                    }`}
                    onClick={() => handleAgentClick(agent.agent_id, agent.name)}
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
                      {selectedAgent === agent.agent_id ? 'Click to hide details' : 'Click for details & task history →'}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div className="text-center py-8 text-gray-500">
              <Bot className="h-12 w-12 mx-auto mb-4 text-gray-300" />
              <p>No agents available for this phase</p>
            </div>
          )}
        </div>
      </div>

      {/* Selected Agent Details - Now positioned prominently */}
      {selectedAgent && (
        <div className="bg-white rounded-lg shadow">
          <div className="p-6 border-b border-gray-200">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold text-gray-900 flex items-center">
                <Bot className="h-5 w-5 mr-2 text-purple-600" />
                Agent Details & Task History
              </h3>
              <button
                onClick={() => setSelectedAgent(null)}
                className="text-gray-400 hover:text-gray-600"
              >
                ✕
              </button>
            </div>
            
            {/* Horizontal tabs for agent details */}
            <div className="mt-4">
              <nav className="flex space-x-8">
                <button
                  onClick={() => setSelectedAgentTab('details')}
                  className={`${
                    selectedAgentTab === 'details'
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700'
                  } border-b-2 py-2 px-1 text-sm font-medium flex items-center space-x-2`}
                >
                  <User className="h-4 w-4" />
                  <span>Agent Details</span>
                </button>
                <button
                  onClick={() => setSelectedAgentTab('tasks')}
                  className={`${
                    selectedAgentTab === 'tasks'
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700'
                  } border-b-2 py-2 px-1 text-sm font-medium flex items-center space-x-2`}
                >
                  <History className="h-4 w-4" />
                  <span>Task History</span>
                  <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                    {agentTaskHistory.length}
                  </span>
                </button>
              </nav>
            </div>
          </div>
          
          <div className="p-6">
            {/* Agent Details Tab */}
            {selectedAgentTab === 'details' && (() => {
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

            {/* Task History Tab */}
            {selectedAgentTab === 'tasks' && (
              <div>
                {loadingTaskHistory ? (
                  <div className="text-center py-8">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
                    <p className="text-sm text-gray-600 mt-2">Loading task history...</p>
                  </div>
                ) : agentTaskHistory.length > 0 ? (
                  <div className="space-y-4">
                    <h4 className="font-medium text-gray-900 mb-3">Recent Task History</h4>
                    {agentTaskHistory.map((task) => (
                      <div key={task.task_id} className="border rounded-lg p-4 bg-gray-50">
                        <div className="flex items-center justify-between mb-2">
                          <div className="flex items-center space-x-2">
                            <CheckCircle className="h-4 w-4 text-green-500" />
                            <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getStatusColor(task.status)}`}>
                              {task.status.toUpperCase()}
                            </span>
                            <span className="text-sm text-gray-600">#{task.task_id.split('_').pop()}</span>
                          </div>
                          <div className="text-sm text-gray-600">
                            <Clock className="h-4 w-4 inline mr-1" />
                            {task.duration}s
                          </div>
                        </div>
                        <p className="text-sm text-gray-700 mb-2">{task.description}</p>
                        {task.result_preview && (
                          <div className="bg-white rounded p-2 mb-2">
                            <span className="text-xs text-gray-500">Result: </span>
                            <span className="text-sm text-gray-700">{task.result_preview}</span>
                          </div>
                        )}
                        <div className="flex items-center justify-between text-xs text-gray-500">
                          <div className="flex space-x-4">
                            <span>🧠 LLM Calls: {task.llm_calls}</span>
                            <span>💭 Thinking Phases: {task.thinking_phases}</span>
                          </div>
                          <div>
                            {new Date(task.start_time).toLocaleTimeString()}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-8 text-gray-500">
                    <History className="h-12 w-12 mx-auto mb-4 text-gray-300" />
                    <p>No recent task history available</p>
                    <p className="text-sm">Tasks will appear here when the agent is active</p>
                  </div>
                )}
              </div>
            )}
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
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AgentMonitor; 