import React from 'react'
import { useState } from 'react'
import { useEffect } from 'react'
import { AlertCircle } from 'lucide-react'
import { ChevronDown, Building2, Calendar, Database, Eye, Layers, RefreshCw, Check, X } from 'lucide-react'
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
import { useClient } from '@/contexts/ClientContext';
import { useEngagement } from '@/contexts/EngagementContext';
import { useSession } from '@/contexts/SessionContext';
import { useToast } from '@/hooks/use-toast';
import { useQuery } from '@tanstack/react-query'
import { useQueryClient } from '@tanstack/react-query'
import { apiCall } from '@/config/api';
import { useAuth } from '@/contexts/AuthContext';
import { getContextHeaders } from '@/utils/contextUtils';

interface Client {
  id: string;
  name: string;
}

interface Engagement {
  id: string;
  name: string;
  client_id: string;
}

interface Session {
  id: string;
  session_name: string;
  session_display_name?: string;
  engagement_id: string;
}

interface ContextSelectorProps {
  className?: string;
  compact?: boolean;
  onSelectionChange?: () => void;
}

const ContextSelector: React.FC<ContextSelectorProps> = ({ className = '', compact = false, onSelectionChange }) => {
  const auth = useAuth();
  const { currentClient, setCurrentClient } = useClient();
  const { currentEngagement, setCurrentEngagement } = useEngagement();
  const { currentSession, setCurrentSession, viewMode, setViewMode } = useSession();
  const { toast } = useToast();
  const queryClient = useQueryClient();

  const [isExpanded, setIsExpanded] = useState(!compact);

  // Staging selections (local state for preview)
  const [stagedClient, setStagedClient] = useState<Client | null>(currentClient);
  const [stagedEngagement, setStagedEngagement] = useState<Engagement | null>(currentEngagement);
  const [stagedSession, setStagedSession] = useState<Session | null>(currentSession);
  const [stagedViewMode, setStagedViewMode] = useState<'session_view' | 'engagement_view'>(viewMode);

  // Queries for data fetching
  const { data: clients = [] } = useQuery({
    queryKey: ['clients'],
    queryFn: async () => {
      console.log('🔍 ContextSelector - Fetching clients...');
      const response = await apiCall('/api/v1/context-establishment/clients', {
        method: 'GET',
        headers: auth.getAuthHeaders()
      }, false); // Don't include context - we're establishing it
      console.log('🔍 ContextSelector - Clients API response:', response);
      return response.clients || [];
    }
  });

  const { data: engagements = [] } = useQuery({
    queryKey: ['engagements', stagedClient?.id],
    queryFn: async () => {
      if (!stagedClient?.id) return [];
      console.log('🔍 ContextSelector - Fetching engagements for client:', stagedClient.id);
      const response = await apiCall(`/api/v1/context-establishment/engagements?client_id=${stagedClient.id}`, {
        method: 'GET',
        headers: auth.getAuthHeaders()
      }, false); // Don't include context - we're establishing it
      console.log('🔍 ContextSelector - Engagements API response:', response);
      return response.engagements || [];
    },
    enabled: !!stagedClient?.id
  });

  const { data: sessions = [] } = useQuery({
    queryKey: ['sessions', stagedEngagement?.id],
    queryFn: async () => {
      if (!stagedEngagement?.id) return [];
      const response = await apiCall(`/api/v1/context-establishment/engagements/${stagedEngagement.id}/sessions`, {
        method: 'GET',
        headers: auth.getAuthHeaders()
      }, false); // Don't include context - we're establishing it
      return response.sessions;
    },
    enabled: !!stagedEngagement?.id
  });

  // Update staged selections when current context changes
  useEffect(() => {
    setStagedClient(currentClient);
    setStagedEngagement(currentEngagement);
    setStagedSession(currentSession);
    setStagedViewMode(viewMode);
  }, [currentClient, currentEngagement, currentSession, viewMode]);

  // Staging handlers
  const handleStagedClientChange = (clientId: string) => {
    const selectedClient = clients.find(c => c.id === clientId);
    setStagedClient(selectedClient || null);
    setStagedEngagement(null);
    setStagedSession(null);
  };

  const handleStagedEngagementChange = (engagementId: string) => {
    const selectedEngagement = engagements.find(e => e.id === engagementId);
    setStagedEngagement(selectedEngagement || null);
    setStagedSession(null);
  };

  const handleStagedSessionChange = (sessionId: string) => {
    if (sessionId === 'no-session') {
      setStagedSession(null);
      setStagedViewMode('engagement_view');
    } else {
      const selectedSession = sessions.find(s => s.id === sessionId);
      setStagedSession(selectedSession || null);
      if (selectedSession) {
        setStagedViewMode('session_view');
      }
    }
  };

  const handleStagedViewModeChange = (mode: 'session_view' | 'engagement_view') => {
    setStagedViewMode(mode);
  };

  // Confirm the staged selections and apply to global context
  const handleConfirmSelection = async () => {
    try {
      // Switch client first and wait for completion
      if (stagedClient && stagedClient.id !== auth.client?.id) {
        console.log('🔄 Switching client first:', stagedClient.id);
        await auth.switchClient(stagedClient.id, stagedClient);
        console.log('✅ Client switch completed');

        // Small delay to ensure context state is updated
        await new Promise(resolve => setTimeout(resolve, 100));
      }

      // Then switch engagement with the updated client context
      if (stagedEngagement && stagedEngagement.id !== auth.engagement?.id) {
        console.log('🔄 Switching engagement:', stagedEngagement.id);
        await auth.switchEngagement(stagedEngagement.id, stagedEngagement);
        console.log('✅ Engagement switch completed');
      }

      // Also update local context providers for compatibility
      if (stagedClient) {
        setCurrentClient(stagedClient);
      }
      if (stagedEngagement) {
        setCurrentEngagement(stagedEngagement);
      }
      if (stagedSession) {
        setCurrentSession(stagedSession);
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

      onSelectionChange?.();
    } catch (error) {
      console.error('Failed to switch context:', error);
      toast({
        title: "Context Switch Failed",
        description: "Failed to switch context. Please try again.",
        variant: "destructive"
      });
    }
  };

  // Cancel staged selections and revert to current context
  const handleCancelSelection = () => {
    setStagedClient(currentClient);
    setStagedEngagement(currentEngagement);
    setStagedSession(currentSession);
    setStagedViewMode(viewMode);
    onSelectionChange?.();
  };

  // Check if there are changes to confirm
  const hasChanges = () => {
    return (
      stagedClient?.id !== currentClient?.id ||
      stagedEngagement?.id !== currentEngagement?.id ||
      stagedSession?.id !== currentSession?.id ||
      stagedViewMode !== viewMode
    );
  };

  const handleRefresh = () => {
    queryClient.invalidateQueries({ queryKey: ['clients'] });
    if (stagedClient?.id) {
      queryClient.invalidateQueries({ queryKey: ['engagements', stagedClient.id] });
    }
    if (stagedEngagement?.id) {
      queryClient.invalidateQueries({ queryKey: ['sessions', stagedEngagement.id] });
    }
    toast({
      title: "Context Refreshed",
      description: "Reloaded available contexts"
    });
  };

  const handleReset = () => {
    setCurrentClient(null);
    setCurrentEngagement(null);
    setCurrentSession(null);
    setViewMode('engagement_view');
    toast({
      title: "Context Reset",
      description: "Context cleared"
    });
    onSelectionChange?.();
  };

  if (compact && !isExpanded) {
    return (
      <div className={`flex items-center space-x-2 ${className}`}>
        <Badge variant="outline" className="bg-blue-50">
          {currentClient?.name || 'No Client'}
        </Badge>
        {currentEngagement && (
          <Badge variant="outline" className="bg-green-50">
            {currentEngagement.name}
          </Badge>
        )}
        {currentSession && viewMode === 'session_view' && (
          <Badge variant="outline" className="bg-purple-50">
            {currentSession.session_display_name || currentSession.session_name}
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
            <Button
              variant="ghost"
              size="sm"
              onClick={handleRefresh}
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
              disabled={!stagedClient}
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
              value={stagedSession?.id || 'no-session'}
              onValueChange={handleStagedSessionChange}
              disabled={!stagedEngagement}
            >
              <SelectTrigger>
                <SelectValue placeholder={stagedEngagement ? "Select a session (optional)..." : "Select an engagement first"} />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="no-session">
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
