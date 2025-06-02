import React, { useState, useEffect } from 'react';
import { ChevronDown, Building2, Calendar, Database, Eye, Layers, RefreshCw, AlertCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { 
  Select, 
  SelectContent, 
  SelectItem, 
  SelectTrigger, 
  SelectValue 
} from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent } from '@/components/ui/card';
import { useAppContext, ClientContext, EngagementContext, SessionContext } from '@/hooks/useContext';
import { useToast } from '@/hooks/use-toast';

interface ContextSelectorProps {
  className?: string;
  compact?: boolean;
}

const ContextSelector: React.FC<ContextSelectorProps> = ({ className = '', compact = false }) => {
  const { 
    context, 
    isLoading, 
    error,
    fetchClients,
    fetchEngagements,
    fetchSessions,
    setClient,
    setEngagement,
    setSession,
    setViewMode,
    resetToDemo,
    clearError
  } = useAppContext();

  const { toast } = useToast();
  
  const [clients, setClients] = useState<ClientContext[]>([]);
  const [engagements, setEngagements] = useState<EngagementContext[]>([]);
  const [sessions, setSessions] = useState<SessionContext[]>([]);
  const [isExpanded, setIsExpanded] = useState(!compact);

  // Load initial data
  useEffect(() => {
    loadClients();
  }, []);

  // Load engagements when client changes
  useEffect(() => {
    if (context.client) {
      loadEngagements(context.client.id);
    } else {
      setEngagements([]);
    }
  }, [context.client]);

  // Load sessions when engagement changes
  useEffect(() => {
    if (context.engagement) {
      loadSessions(context.engagement.id);
    } else {
      setSessions([]);
    }
  }, [context.engagement]);

  // Show error toasts
  useEffect(() => {
    if (error) {
      toast({
        title: "Context Error",
        description: error,
        variant: "destructive"
      });
      clearError();
    }
  }, [error, toast, clearError]);

  const loadClients = async () => {
    try {
      const clientList = await fetchClients();
      setClients(clientList);
    } catch (err) {
      console.error('Failed to load clients:', err);
    }
  };

  const loadEngagements = async (clientId: string) => {
    try {
      const engagementList = await fetchEngagements(clientId);
      setEngagements(engagementList);
    } catch (err) {
      console.error('Failed to load engagements:', err);
    }
  };

  const loadSessions = async (engagementId: string) => {
    try {
      const sessionList = await fetchSessions(engagementId);
      setSessions(sessionList);
    } catch (err) {
      console.error('Failed to load sessions:', err);
    }
  };

  const handleClientChange = (clientId: string) => {
    const selectedClient = clients.find(c => c.id === clientId);
    if (selectedClient) {
      setClient(selectedClient);
      toast({
        title: "Client Selected",
        description: `Switched to ${selectedClient.name}`
      });
    }
  };

  const handleEngagementChange = (engagementId: string) => {
    const selectedEngagement = engagements.find(e => e.id === engagementId);
    if (selectedEngagement) {
      setEngagement(selectedEngagement);
      toast({
        title: "Engagement Selected",
        description: `Switched to ${selectedEngagement.name}`
      });
    }
  };

  const handleSessionChange = (sessionId: string) => {
    const selectedSession = sessions.find(s => s.id === sessionId);
    setSession(selectedSession || null);
    if (selectedSession) {
      setViewMode('session_view');
      toast({
        title: "Session Selected",
        description: `Switched to ${selectedSession.session_display_name || selectedSession.session_name}`
      });
    }
  };

  const handleViewModeChange = (mode: 'session_view' | 'engagement_view') => {
    setViewMode(mode);
    toast({
      title: "View Mode Changed",
      description: mode === 'session_view' ? 'Viewing session-specific data' : 'Viewing engagement-level data'
    });
  };

  const handleRefresh = () => {
    loadClients();
    if (context.client) {
      loadEngagements(context.client.id);
    }
    if (context.engagement) {
      loadSessions(context.engagement.id);
    }
    toast({
      title: "Context Refreshed",
      description: "Reloaded available contexts"
    });
  };

  const handleReset = () => {
    resetToDemo();
    loadClients();
    toast({
      title: "Context Reset",
      description: "Switched back to demo context"
    });
  };

  if (compact && !isExpanded) {
    return (
      <div className={`flex items-center space-x-2 ${className}`}>
        <Badge variant="outline" className="bg-blue-50">
          {context.client?.name || 'No Client'}
        </Badge>
        {context.engagement && (
          <Badge variant="outline" className="bg-green-50">
            {context.engagement.name}
          </Badge>
        )}
        {context.session && context.viewMode === 'session_view' && (
          <Badge variant="outline" className="bg-purple-50">
            {context.session.session_display_name || context.session.session_name}
          </Badge>
        )}
        <Button
          variant="ghost"
          size="sm"
          onClick={() => setIsExpanded(true)}
          className="h-6 px-2"
        >
          <ChevronDown className="h-3 w-3" />
        </Button>
      </div>
    );
  }

  return (
    <Card className={`${className}`}>
      <CardContent className="p-4">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-2">
            <Layers className="h-5 w-5 text-blue-600" />
            <h3 className="text-lg font-semibold">Context Selection</h3>
          </div>
          <div className="flex items-center space-x-2">
            {isLoading && <RefreshCw className="h-4 w-4 animate-spin text-gray-400" />}
            <Button
              variant="ghost"
              size="sm"
              onClick={handleRefresh}
              disabled={isLoading}
              title="Refresh contexts"
            >
              <RefreshCw className="h-4 w-4" />
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={handleReset}
              title="Reset to demo"
            >
              Reset
            </Button>
            {compact && (
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setIsExpanded(false)}
                title="Collapse"
              >
                <ChevronDown className="h-4 w-4 rotate-180" />
              </Button>
            )}
          </div>
        </div>

        <div className="space-y-4">
          {/* Client Selection */}
          <div className="space-y-2">
            <label className="flex items-center text-sm font-medium text-gray-700">
              <Building2 className="h-4 w-4 mr-2" />
              Client
            </label>
            <Select
              value={context.client?.id || ''}
              onValueChange={handleClientChange}
              disabled={isLoading}
            >
              <SelectTrigger>
                <SelectValue placeholder="Select a client..." />
              </SelectTrigger>
              <SelectContent>
                {clients.map((client) => (
                  <SelectItem key={client.id} value={client.id}>
                    <div className="flex items-center">
                      <Building2 className="h-4 w-4 mr-2" />
                      {client.name}
                      {client.id === 'cc92315a-4bae-469d-9550-46d1c6e5ab68' && (
                        <Badge variant="secondary" className="ml-2 text-xs">Demo</Badge>
                      )}
                    </div>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Engagement Selection */}
          <div className="space-y-2">
            <label className="flex items-center text-sm font-medium text-gray-700">
              <Calendar className="h-4 w-4 mr-2" />
              Engagement
            </label>
            <Select
              value={context.engagement?.id || ''}
              onValueChange={handleEngagementChange}
              disabled={isLoading || !context.client}
            >
              <SelectTrigger>
                <SelectValue placeholder={context.client ? "Select an engagement..." : "Select a client first"} />
              </SelectTrigger>
              <SelectContent>
                {engagements.map((engagement) => (
                  <SelectItem key={engagement.id} value={engagement.id}>
                    <div className="flex items-center">
                      <Calendar className="h-4 w-4 mr-2" />
                      {engagement.name}
                    </div>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Session Selection */}
          <div className="space-y-2">
            <label className="flex items-center text-sm font-medium text-gray-700">
              <Database className="h-4 w-4 mr-2" />
              Session (Optional)
            </label>
            <Select
              value={context.session?.id || ''}
              onValueChange={handleSessionChange}
              disabled={isLoading || !context.engagement}
            >
              <SelectTrigger>
                <SelectValue placeholder={context.engagement ? "Select a session or use engagement view..." : "Select an engagement first"} />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="">
                  <div className="flex items-center">
                    <Eye className="h-4 w-4 mr-2" />
                    Engagement View (All Sessions)
                  </div>
                </SelectItem>
                {sessions.map((session) => (
                  <SelectItem key={session.id} value={session.id}>
                    <div className="flex items-center">
                      <Database className="h-4 w-4 mr-2" />
                      {session.session_display_name || session.session_name}
                      <Badge 
                        variant={session.status === 'active' ? 'default' : 'secondary'} 
                        className="ml-2 text-xs"
                      >
                        {session.status}
                      </Badge>
                    </div>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* View Mode Toggle */}
          {context.engagement && (
            <div className="space-y-2">
              <label className="flex items-center text-sm font-medium text-gray-700">
                <Eye className="h-4 w-4 mr-2" />
                Data View Mode
              </label>
              <div className="flex space-x-2">
                <Button
                  variant={context.viewMode === 'engagement_view' ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => handleViewModeChange('engagement_view')}
                  className="flex-1"
                >
                  <Layers className="h-4 w-4 mr-2" />
                  Engagement View
                </Button>
                <Button
                  variant={context.viewMode === 'session_view' ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => handleViewModeChange('session_view')}
                  disabled={!context.session}
                  className="flex-1"
                >
                  <Database className="h-4 w-4 mr-2" />
                  Session View
                </Button>
              </div>
              <p className="text-xs text-gray-500">
                {context.viewMode === 'engagement_view' 
                  ? 'Showing deduplicated data across all sessions in engagement'
                  : 'Showing data from selected session only'
                }
              </p>
            </div>
          )}

          {/* Context Status */}
          <div className="pt-2 border-t">
            <div className="text-xs text-gray-500 space-y-1">
              <div>Current Context:</div>
              <div className="flex flex-wrap gap-1">
                {context.client && (
                  <Badge variant="outline" className="text-xs">
                    Client: {context.client.name}
                  </Badge>
                )}
                {context.engagement && (
                  <Badge variant="outline" className="text-xs">
                    Engagement: {context.engagement.name}
                  </Badge>
                )}
                {context.session && context.viewMode === 'session_view' && (
                  <Badge variant="outline" className="text-xs">
                    Session: {context.session.session_display_name || context.session.session_name}
                  </Badge>
                )}
                <Badge variant="outline" className="text-xs">
                  Mode: {context.viewMode === 'session_view' ? 'Session' : 'Engagement'}
                </Badge>
              </div>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default ContextSelector; 