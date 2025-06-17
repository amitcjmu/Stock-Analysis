import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { 
  MessageSquare,
  Users,
  Network,
  Activity,
  Clock,
  Crown,
  ArrowRight,
  Zap,
  Brain,
  CheckCircle2,
  AlertCircle,
  Play,
  Pause,
  Filter
} from 'lucide-react';

interface AgentMessage {
  id: string;
  timestamp: string;
  agent_name: string;
  agent_role: string;
  is_manager: boolean;
  message_type: 'task_assignment' | 'result_sharing' | 'collaboration_request' | 'status_update' | 'knowledge_sharing';
  content: string;
  target_agent?: string;
  crew: string;
  metadata: {
    confidence?: number;
    task_id?: string;
    result_type?: string;
    collaboration_type?: string;
  };
}

interface CollaborationEvent {
  id: string;
  timestamp: string;
  event_type: 'crew_collaboration' | 'cross_crew_insight' | 'knowledge_transfer' | 'task_delegation';
  source_agent: string;
  source_crew: string;
  target_agent?: string;
  target_crew?: string;
  description: string;
  success: boolean;
  impact_score: number;
}

interface CommunicationStats {
  total_messages: number;
  active_collaborations: number;
  cross_crew_communications: number;
  success_rate: number;
  avg_response_time_seconds: number;
  top_communicators: Array<{
    agent: string;
    messages: number;
    collaborations: number;
  }>;
}

interface AgentCommunicationPanelProps {
  flowId: string;
  refreshInterval?: number;
  maxMessages?: number;
}

const AgentCommunicationPanel: React.FC<AgentCommunicationPanelProps> = ({
  flowId,
  refreshInterval = 3000,
  maxMessages = 50
}) => {
  const [messages, setMessages] = useState<AgentMessage[]>([]);
  const [collaborationEvents, setCollaborationEvents] = useState<CollaborationEvent[]>([]);
  const [communicationStats, setCommunicationStats] = useState<CommunicationStats | null>(null);
  const [activeTab, setActiveTab] = useState<'messages' | 'collaborations' | 'stats'>('messages');
  const [isLive, setIsLive] = useState(true);
  const [filteredCrew, setFilteredCrew] = useState<string | null>(null);
  const [filteredMessageType, setFilteredMessageType] = useState<string | null>(null);

  // Fetch communication data
  const fetchCommunicationData = async () => {
    if (!flowId || !isLive) return;

    try {
      // Fetch agent messages
      const messagesResponse = await fetch(`/api/v1/discovery/flow/communication/messages/${flowId}?limit=${maxMessages}`);
      if (messagesResponse.ok) {
        const messagesData = await messagesResponse.json();
        if (messagesData.messages) {
          setMessages(messagesData.messages);
        }
      }

      // Fetch collaboration events
      const eventsResponse = await fetch(`/api/v1/discovery/flow/communication/events/${flowId}?limit=20`);
      if (eventsResponse.ok) {
        const eventsData = await eventsResponse.json();
        if (eventsData.events) {
          setCollaborationEvents(eventsData.events);
        }
      }

      // Fetch communication stats
      const statsResponse = await fetch(`/api/v1/discovery/flow/communication/stats/${flowId}`);
      if (statsResponse.ok) {
        const statsData = await statsResponse.json();
        setCommunicationStats(statsData);
      }
    } catch (error) {
      console.error('Failed to fetch communication data:', error);
      // Mock data for development
      setMessages([
        {
          id: '1',
          timestamp: new Date().toISOString(),
          agent_name: 'Field Mapping Manager',
          agent_role: 'Coordinates field mapping analysis',
          is_manager: true,
          message_type: 'task_assignment',
          content: 'Initiating field mapping analysis for 150 data fields. Schema Analysis Expert, please begin semantic analysis.',
          target_agent: 'Schema Analysis Expert',
          crew: 'Field Mapping Crew',
          metadata: { task_id: 'field_map_001' }
        },
        {
          id: '2',
          timestamp: new Date(Date.now() - 30000).toISOString(),
          agent_name: 'Schema Analysis Expert',
          agent_role: 'Analyzes data structure semantics',
          is_manager: false,
          message_type: 'status_update',
          content: 'Completed semantic analysis of 150 fields. Identified 142 standard mappings with high confidence.',
          crew: 'Field Mapping Crew',
          metadata: { confidence: 0.89, result_type: 'field_analysis' }
        }
      ]);

      setCollaborationEvents([
        {
          id: '1',
          timestamp: new Date().toISOString(),
          event_type: 'cross_crew_insight',
          source_agent: 'Field Mapping Manager',
          source_crew: 'Field Mapping Crew',
          target_crew: 'Data Cleansing Crew',
          description: 'Shared field mapping insights for data validation',
          success: true,
          impact_score: 8.5
        }
      ]);

      setCommunicationStats({
        total_messages: 45,
        active_collaborations: 8,
        cross_crew_communications: 12,
        success_rate: 0.92,
        avg_response_time_seconds: 3.2,
        top_communicators: [
          { agent: 'Field Mapping Manager', messages: 12, collaborations: 8 },
          { agent: 'Data Quality Manager', messages: 9, collaborations: 6 }
        ]
      });
    }
  };

  useEffect(() => {
    fetchCommunicationData();
    
    if (isLive) {
      const interval = setInterval(fetchCommunicationData, refreshInterval);
      return () => clearInterval(interval);
    }
  }, [flowId, refreshInterval, isLive]);

  const getMessageTypeIcon = (type: string) => {
    switch (type) {
      case 'task_assignment':
        return <Users className="h-4 w-4 text-blue-500" />;
      case 'result_sharing':
        return <CheckCircle2 className="h-4 w-4 text-green-500" />;
      case 'collaboration_request':
        return <Network className="h-4 w-4 text-purple-500" />;
      case 'status_update':
        return <Activity className="h-4 w-4 text-orange-500" />;
      case 'knowledge_sharing':
        return <Brain className="h-4 w-4 text-indigo-500" />;
      default:
        return <MessageSquare className="h-4 w-4 text-gray-500" />;
    }
  };

  const getMessageTypeColor = (type: string) => {
    switch (type) {
      case 'task_assignment': return 'bg-blue-50 border-blue-200';
      case 'result_sharing': return 'bg-green-50 border-green-200';
      case 'collaboration_request': return 'bg-purple-50 border-purple-200';
      case 'status_update': return 'bg-orange-50 border-orange-200';
      case 'knowledge_sharing': return 'bg-indigo-50 border-indigo-200';
      default: return 'bg-gray-50 border-gray-200';
    }
  };

  const getEventTypeIcon = (type: string) => {
    switch (type) {
      case 'crew_collaboration':
        return <Users className="h-4 w-4 text-blue-500" />;
      case 'cross_crew_insight':
        return <Zap className="h-4 w-4 text-yellow-500" />;
      case 'knowledge_transfer':
        return <Brain className="h-4 w-4 text-purple-500" />;
      case 'task_delegation':
        return <ArrowRight className="h-4 w-4 text-green-500" />;
      default:
        return <Activity className="h-4 w-4 text-gray-500" />;
    }
  };

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffSecs = Math.floor(diffMs / 1000);
    const diffMins = Math.floor(diffSecs / 60);
    const diffHours = Math.floor(diffMins / 60);

    if (diffSecs < 60) return `${diffSecs}s ago`;
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    return date.toLocaleDateString();
  };

  const filteredMessages = messages.filter(msg => {
    if (filteredCrew && msg.crew !== filteredCrew) return false;
    if (filteredMessageType && msg.message_type !== filteredMessageType) return false;
    return true;
  });

  const uniqueCrews = [...new Set(messages.map(msg => msg.crew))];
  const uniqueMessageTypes = [...new Set(messages.map(msg => msg.message_type))];

  const MessagesView = () => (
    <div className="space-y-4">
      {/* Filters */}
      <div className="flex items-center gap-4 p-4 bg-gray-50 rounded-lg">
        <Filter className="h-4 w-4 text-gray-600" />
        <div className="flex items-center gap-2">
          <label className="text-sm font-medium">Crew:</label>
          <select 
            value={filteredCrew || ''} 
            onChange={(e) => setFilteredCrew(e.target.value || null)}
            className="text-sm border rounded px-2 py-1"
          >
            <option value="">All Crews</option>
            {uniqueCrews.map(crew => (
              <option key={crew} value={crew}>{crew}</option>
            ))}
          </select>
        </div>
        <div className="flex items-center gap-2">
          <label className="text-sm font-medium">Type:</label>
          <select 
            value={filteredMessageType || ''} 
            onChange={(e) => setFilteredMessageType(e.target.value || null)}
            className="text-sm border rounded px-2 py-1"
          >
            <option value="">All Types</option>
            {uniqueMessageTypes.map(type => (
              <option key={type} value={type}>{type.replace('_', ' ')}</option>
            ))}
          </select>
        </div>
        <Button variant="outline" size="sm" onClick={() => { setFilteredCrew(null); setFilteredMessageType(null); }}>
          Clear Filters
        </Button>
      </div>

      {/* Messages */}
      <ScrollArea className="h-[500px]">
        <div className="space-y-3">
          {filteredMessages.map((message) => (
            <div key={message.id} className={`p-4 rounded-lg border ${getMessageTypeColor(message.message_type)}`}>
              <div className="flex items-start justify-between mb-2">
                <div className="flex items-center gap-2">
                  {message.is_manager && <Crown className="h-4 w-4 text-yellow-600" />}
                  <span className="font-medium text-sm">{message.agent_name}</span>
                  <Badge variant="outline" className="text-xs">{message.crew}</Badge>
                  {message.target_agent && (
                    <>
                      <ArrowRight className="h-3 w-3 text-gray-400" />
                      <span className="text-sm text-gray-600">{message.target_agent}</span>
                    </>
                  )}
                </div>
                <div className="flex items-center gap-2">
                  {getMessageTypeIcon(message.message_type)}
                  <span className="text-xs text-gray-500">{formatTimestamp(message.timestamp)}</span>
                </div>
              </div>
              
              <p className="text-sm text-gray-700 mb-2">{message.content}</p>
              
              <div className="flex items-center justify-between text-xs">
                <Badge variant="secondary" className="text-xs">
                  {message.message_type.replace('_', ' ')}
                </Badge>
                {message.metadata.confidence && (
                  <span className="text-gray-500">
                    Confidence: {(message.metadata.confidence * 100).toFixed(1)}%
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>
      </ScrollArea>
    </div>
  );

  const CollaborationsView = () => (
    <ScrollArea className="h-[500px]">
      <div className="space-y-3">
        {collaborationEvents.map((event) => (
          <div key={event.id} className="p-4 rounded-lg border border-gray-200">
            <div className="flex items-start justify-between mb-2">
              <div className="flex items-center gap-2">
                {getEventTypeIcon(event.event_type)}
                <span className="font-medium text-sm">{event.source_agent}</span>
                <Badge variant="outline" className="text-xs">{event.source_crew}</Badge>
                {event.target_crew && (
                  <>
                    <ArrowRight className="h-3 w-3 text-gray-400" />
                    <Badge variant="outline" className="text-xs">{event.target_crew}</Badge>
                  </>
                )}
              </div>
              <div className="flex items-center gap-2">
                {event.success ? 
                  <CheckCircle2 className="h-4 w-4 text-green-500" /> :
                  <AlertCircle className="h-4 w-4 text-red-500" />
                }
                <span className="text-xs text-gray-500">{formatTimestamp(event.timestamp)}</span>
              </div>
            </div>
            
            <p className="text-sm text-gray-700 mb-2">{event.description}</p>
            
            <div className="flex items-center justify-between text-xs">
              <Badge variant="secondary" className="text-xs">
                {event.event_type.replace('_', ' ')}
              </Badge>
              <span className="text-gray-500">
                Impact: {event.impact_score.toFixed(1)}/10
              </span>
            </div>
          </div>
        ))}
      </div>
    </ScrollArea>
  );

  const StatsView = () => (
    <div className="space-y-6">
      {communicationStats && (
        <>
          {/* Overview Stats */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm">Total Messages</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{communicationStats.total_messages}</div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm">Active Collaborations</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{communicationStats.active_collaborations}</div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm">Cross-Crew Communications</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{communicationStats.cross_crew_communications}</div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm">Success Rate</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{(communicationStats.success_rate * 100).toFixed(1)}%</div>
              </CardContent>
            </Card>
          </div>

          {/* Top Communicators */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Top Communicators</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {communicationStats.top_communicators.map((comm, index) => (
                  <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                    <div className="flex items-center gap-2">
                      <Badge variant="outline" className="text-xs">#{index + 1}</Badge>
                      <span className="font-medium">{comm.agent}</span>
                    </div>
                    <div className="flex items-center gap-4 text-sm">
                      <span>{comm.messages} messages</span>
                      <span>{comm.collaborations} collaborations</span>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Response Time */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Average Response Time</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold">
                {communicationStats.avg_response_time_seconds.toFixed(1)}s
              </div>
              <p className="text-sm text-gray-600">Average time between agent communications</p>
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <MessageSquare className="h-5 w-5" />
                Agent Communication Center
              </CardTitle>
              <CardDescription>
                Real-time monitoring of agent conversations and collaboration events
              </CardDescription>
            </div>
            <div className="flex items-center gap-2">
              <Button
                variant={isLive ? "default" : "outline"}
                size="sm"
                onClick={() => setIsLive(!isLive)}
              >
                {isLive ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
                {isLive ? 'Pause' : 'Resume'} Live
              </Button>
              <div className={`w-2 h-2 rounded-full ${isLive ? 'bg-green-500 animate-pulse' : 'bg-gray-400'}`}></div>
            </div>
          </div>
        </CardHeader>
      </Card>

      {/* Tabs */}
      <div className="flex gap-2 border-b">
        <Button
          variant={activeTab === 'messages' ? 'default' : 'ghost'}
          onClick={() => setActiveTab('messages')}
          className="flex items-center gap-2"
        >
          <MessageSquare className="h-4 w-4" />
          Messages ({filteredMessages.length})
        </Button>
        <Button
          variant={activeTab === 'collaborations' ? 'default' : 'ghost'}
          onClick={() => setActiveTab('collaborations')}
          className="flex items-center gap-2"
        >
          <Network className="h-4 w-4" />
          Collaborations ({collaborationEvents.length})
        </Button>
        <Button
          variant={activeTab === 'stats' ? 'default' : 'ghost'}
          onClick={() => setActiveTab('stats')}
          className="flex items-center gap-2"
        >
          <Activity className="h-4 w-4" />
          Statistics
        </Button>
      </div>

      {/* Content */}
      <Card>
        <CardContent className="pt-6">
          {activeTab === 'messages' && <MessagesView />}
          {activeTab === 'collaborations' && <CollaborationsView />}
          {activeTab === 'stats' && <StatsView />}
        </CardContent>
      </Card>
    </div>
  );
};

export default AgentCommunicationPanel; 