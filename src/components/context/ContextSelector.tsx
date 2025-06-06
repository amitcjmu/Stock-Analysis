import React, { useState, useEffect } from 'react';
import { ChevronDown, Building2, Calendar, Database, Eye, Layers, RefreshCw, AlertCircle, Check, X } from 'lucide-react';
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
  onSelectionChange?: () => void;
}

const ContextSelector: React.FC<ContextSelectorProps> = ({ className = '', compact = false, onSelectionChange }) => {
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

  // Staging selections (local state for preview)
  const [stagedClient, setStagedClient] = useState<ClientContext | null>(context.client);
  const [stagedEngagement, setStagedEngagement] = useState<EngagementContext | null>(context.engagement);
  const [stagedSession, setStagedSession] = useState<SessionContext | null>(context.session);
  const [stagedViewMode, setStagedViewMode] = useState<'session_view' | 'engagement_view'>(context.viewMode);

  // Load initial data
  useEffect(() => {
    loadClients();
  }, []);

  // Update staged selections when global context changes
  useEffect(() => {
    setStagedClient(context.client);
    setStagedEngagement(context.engagement);
    setStagedSession(context.session);
    setStagedViewMode(context.viewMode);
  }, [context]);

  // Load engagements when staged client changes
  useEffect(() => {
    if (stagedClient) {
      loadEngagements(stagedClient.id);
    } else {
      setEngagements([]);
    }
  }, [stagedClient]);

  // Load sessions when staged engagement changes
  useEffect(() => {
    if (stagedEngagement) {
      loadSessions(stagedEngagement.id);
    } else {
      setSessions([]);
    }
  }, [stagedEngagement]);

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

  // Staging handlers (don't affect global context immediately)
  const handleStagedClientChange = (clientId: string) => {
    const selectedClient = clients.find(c => c.id === clientId);
    setStagedClient(selectedClient || null);
    // Clear downstream selections when client changes
    setStagedEngagement(null);
    setStagedSession(null);
  };

  const handleStagedEngagementChange = (engagementId: string) => {
    const selectedEngagement = engagements.find(e => e.id === engagementId);
    setStagedEngagement(selectedEngagement || null);
    // Clear session when engagement changes
    setStagedSession(null);
  };

  const handleStagedSessionChange = (sessionId: string) => {
    const selectedSession = sessions.find(s => s.id === sessionId);
    setStagedSession(selectedSession || null);
    if (selectedSession) {
      setStagedViewMode('session_view');
    }
  };

  const handleStagedViewModeChange = (mode: 'session_view' | 'engagement_view') => {
    setStagedViewMode(mode);
  };

  // Confirm the staged selections and apply to global context
  const handleConfirmSelection = () => {
    if (stagedClient) {
      setClient(stagedClient);
    }
    if (stagedEngagement) {
      setEngagement(stagedEngagement);
    }
    if (stagedSession) {
      setSession(stagedSession);
    }
    setViewMode(stagedViewMode);

    const contextParts = [];
    if (stagedClient) contextParts.push(stagedClient.name);
    if (stagedEngagement) contextParts.push(stagedEngagement.name);
    if (stagedSession) contextParts.push(stagedSession.session_display_name || stagedSession.session_name);

    toast({
      title: "Context Switched",
      description: `Switched to: ${contextParts.join(' → ')}`
    });

    // Close the modal after confirming
    onSelectionChange?.();
  };

  // Cancel staged selections and revert to current context
  const handleCancelSelection = () => {
    setStagedClient(context.client);
    setStagedEngagement(context.engagement);
    setStagedSession(context.session);
    setStagedViewMode(context.viewMode);
    
    // Close the modal
    onSelectionChange?.();
  };

  // Check if there are changes to confirm
  const hasChanges = () => {
    return (
      stagedClient?.id !== context.client?.id ||
      stagedEngagement?.id !== context.engagement?.id ||
      stagedSession?.id !== context.session?.id ||
      stagedViewMode !== context.viewMode
    );
  };

  const handleRefresh = () => {
    loadClients();
    if (stagedClient) {
      loadEngagements(stagedClient.id);
    }
    if (stagedEngagement) {
      loadSessions(stagedEngagement.id);
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
    onSelectionChange?.();
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
            <Button
              variant="ghost"
              size="sm"
              onClick={handleCancelSelection}
              title="Cancel"
            >
              <X className="h-4 w-4" />
            </Button>
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
              value={stagedClient?.id || ''}
              onValueChange={handleStagedClientChange}
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
                      {client.id === 'd838573d-f461-44e4-81b5-5af510ef83b7' && (
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
              value={stagedEngagement?.id || ''}
              onValueChange={handleStagedEngagementChange}
              disabled={isLoading || !stagedClient}
            >
              <SelectTrigger>
                <SelectValue placeholder={stagedClient ? "Select an engagement..." : "Select a client first"} />
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
              value={stagedSession?.id || ''}
              onValueChange={handleStagedSessionChange}
              disabled={isLoading || !stagedEngagement}
            >
              <SelectTrigger>
                <SelectValue placeholder={stagedEngagement ? "Select a session (optional)..." : "Select an engagement first"} />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="">
                  <div className="flex items-center">
                    <Eye className="h-4 w-4 mr-2" />
                    Engagement View (No specific session)
                  </div>
                </SelectItem>
                {sessions.map((session) => (
                  <SelectItem key={session.id} value={session.id}>
                    <div className="flex items-center">
                      <Database className="h-4 w-4 mr-2" />
                      {session.session_display_name || session.session_name}
                      <Badge variant="outline" className="ml-2 text-xs">
                        {session.status}
                      </Badge>
                    </div>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* View Mode Selection (when session is selected) */}
          {stagedSession && (
            <div className="space-y-2">
              <label className="flex items-center text-sm font-medium text-gray-700">
                <Eye className="h-4 w-4 mr-2" />
                View Mode
              </label>
              <Select
                value={stagedViewMode}
                onValueChange={handleStagedViewModeChange}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="engagement_view">
                    <div className="flex items-center">
                      <Calendar className="h-4 w-4 mr-2" />
                      Engagement View
                    </div>
                  </SelectItem>
                  <SelectItem value="session_view">
                    <div className="flex items-center">
                      <Database className="h-4 w-4 mr-2" />
                      Session View
                    </div>
                  </SelectItem>
                </SelectContent>
              </Select>
            </div>
          )}
        </div>

        {/* Action Buttons */}
        <div className="flex items-center justify-between mt-6 pt-4 border-t border-gray-200">
          <div className="text-sm text-gray-500">
            {hasChanges() ? "You have unsaved changes" : "No changes"}
          </div>
          
          <div className="flex items-center space-x-2">
            <Button
              variant="outline"
              size="sm"
              onClick={handleCancelSelection}
            >
              <X className="h-4 w-4 mr-1" />
              Cancel
            </Button>
            <Button
              onClick={handleConfirmSelection}
              disabled={!stagedClient || !stagedEngagement}
              size="sm"
            >
              <Check className="h-4 w-4 mr-1" />
              Confirm Selection
            </Button>
          </div>
        </div>

        {/* Preview of staged context */}
        {(stagedClient || stagedEngagement || stagedSession) && (
          <div className="mt-4 p-3 bg-gray-50 rounded-lg">
            <div className="text-sm font-medium text-gray-700 mb-2">Preview:</div>
            <div className="flex flex-wrap gap-2">
              {stagedClient && (
                <Badge variant="outline" className="bg-blue-50">
                  <Building2 className="h-3 w-3 mr-1" />
                  {stagedClient.name}
                </Badge>
              )}
              {stagedEngagement && (
                <Badge variant="outline" className="bg-green-50">
                  <Calendar className="h-3 w-3 mr-1" />
                  {stagedEngagement.name}
                </Badge>
              )}
              {stagedSession && (
                <Badge variant="outline" className="bg-purple-50">
                  <Database className="h-3 w-3 mr-1" />
                  {stagedSession.session_display_name || stagedSession.session_name}
                </Badge>
              )}
              <Badge variant="outline" className="bg-yellow-50">
                <Eye className="h-3 w-3 mr-1" />
                {stagedViewMode === 'session_view' ? 'Session View' : 'Engagement View'}
              </Badge>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default ContextSelector; 