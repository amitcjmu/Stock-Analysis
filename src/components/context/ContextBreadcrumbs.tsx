import React, { useState, useEffect } from 'react';
import { ChevronRight, Home, Building2, Calendar, Settings, ChevronDown } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { 
  Select, 
  SelectContent, 
  SelectItem, 
  SelectTrigger, 
  SelectValue 
} from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { 
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover';
import { useAuth } from '@/contexts/AuthContext';
import { useToast } from '@/hooks/use-toast';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { apiCall } from '@/config/api';

// Types
interface Client {
  id: string;
  name: string;
}

interface Engagement {
  id: string;
  name: string;
  client_id: string;
  status?: string;
}

interface ContextBreadcrumbsProps {
  className?: string;
  showContextSelector?: boolean;
}

export const ContextBreadcrumbs: React.FC<ContextBreadcrumbsProps> = ({ 
  className = '', 
  showContextSelector = true 
}) => {
  const { 
    client,
    engagement,
    switchClient,
    switchEngagement,
    getAuthHeaders,
    isAuthenticated,
    isLoading: authLoading
  } = useAuth();
  
  const { toast } = useToast();
  const queryClient = useQueryClient();
  
  // Local state for context switcher
  const [isContextSelectorOpen, setIsContextSelectorOpen] = useState(false);
  const [selectedClientId, setSelectedClientId] = useState<string>(client?.id || '');
  const [selectedEngagementId, setSelectedEngagementId] = useState<string>(engagement?.id || '');

  // Update local state when auth context changes
  useEffect(() => {
    setSelectedClientId(client?.id || '');
    setSelectedEngagementId(engagement?.id || '');
  }, [client?.id, engagement?.id]);

  // Fetch available clients using context establishment endpoint
  const { data: clients = [], isLoading: clientsLoading } = useQuery({
    queryKey: ['context-clients'],
    queryFn: async () => {
      try {
        const response = await apiCall('/api/v1/context/clients', {
          method: 'GET',
          headers: getAuthHeaders()
        });
        return response.clients || [];
      } catch (error) {
        console.error('Failed to fetch clients:', error);
        return [];
      }
    },
    enabled: isAuthenticated && !authLoading // Only run when user is authenticated and auth is not loading
  });

  // Fetch engagements for selected client using context establishment endpoint
  const { data: engagements = [], isLoading: engagementsLoading } = useQuery({
    queryKey: ['context-engagements', selectedClientId],
    queryFn: async () => {
      if (!selectedClientId) return [];
      try {
        const response = await apiCall(`/context/clients/${selectedClientId}/engagements`, {
          method: 'GET',
          headers: getAuthHeaders()
        });
        return response.engagements || [];
      } catch (error) {
        console.error('Failed to fetch engagements:', error);
        return [];
      }
    },
    enabled: isAuthenticated && !authLoading && !!selectedClientId // Only run when user is authenticated, auth is not loading, and client is selected
  });

  // Handle client selection
  const handleClientChange = async (clientId: string) => {
    setSelectedClientId(clientId);
    setSelectedEngagementId(''); // Reset engagement when client changes
    
    try {
      // Find the full client data
      const selectedClient = clients.find(c => c.id === clientId);
      if (selectedClient) {
        // Create client data object for AuthContext
        const clientData = {
          id: selectedClient.id,
          name: selectedClient.name,
          status: selectedClient.status || 'active'
        };
        
        // Update AuthContext with full client data
        await switchClient(clientId, clientData);
      } else {
        // Fallback if client not found in local data
        await switchClient(clientId);
      }
      
      // Invalidate queries to refresh data
      queryClient.invalidateQueries({ queryKey: ['engagements'] });
      
      toast({
        title: "Client switched",
        description: `Switched to ${selectedClient?.name || 'selected client'}`,
      });
    } catch (error) {
      console.error('Failed to switch client:', error);
      toast({
        title: "Error",
        description: "Failed to switch client",
        variant: "destructive"
      });
    }
  };

  // Handle engagement selection
  const handleEngagementChange = async (engagementId: string) => {
    setSelectedEngagementId(engagementId);
    
    try {
      // Find the full engagement data
      const selectedEngagement = engagements.find(e => e.id === engagementId);
      if (selectedEngagement) {
        // Create engagement data object for AuthContext
        const engagementData = {
          id: selectedEngagement.id,
          name: selectedEngagement.name,
          status: selectedEngagement.status || 'active'
        };
        
        // Update AuthContext with full engagement data
        await switchEngagement(engagementId, engagementData);
      } else {
        // Fallback if engagement not found in local data
        await switchEngagement(engagementId);
      }
      
      toast({
        title: "Engagement switched",
        description: `Switched to ${selectedEngagement?.name || 'selected engagement'}`,
      });
    } catch (error) {
      console.error('Failed to switch engagement:', error);
      toast({
        title: "Error",
        description: "Failed to switch engagement",
        variant: "destructive"
      });
    }
  };

  // Apply context changes and close popover
  const handleApplyContext = () => {
    setIsContextSelectorOpen(false);
    
    // Invalidate all queries to refresh data with new context
    queryClient.invalidateQueries();
    
    toast({
      title: "Context applied",
      description: "All data will refresh with the new context",
    });
  };

  // Build breadcrumb items
  const breadcrumbs = [];
  if (client) {
    breadcrumbs.push({ type: 'Client', label: client.name, id: client.id });
  }
  if (engagement) {
    breadcrumbs.push({ type: 'Engagement', label: engagement.name, id: engagement.id });
  }

  return (
    <div className={`flex items-center justify-between ${className}`}>
      {/* Breadcrumbs Navigation */}
      <div className="flex items-center text-sm text-gray-500">
        <Button
          variant="ghost"
          size="sm"
          className="h-8 px-2"
          onClick={() => window.location.href = '/'}
        >
          <Home className="h-4 w-4" />
        </Button>
        
        {breadcrumbs.map((crumb) => (
          <React.Fragment key={crumb.id}>
            <ChevronRight className="h-4 w-4 text-gray-400 mx-1" />
            <div className="flex items-center space-x-1">
              {crumb.type === 'Client' && <Building2 className="h-4 w-4" />}
              {crumb.type === 'Engagement' && <Calendar className="h-4 w-4" />}
              <span className="font-medium text-gray-700">{crumb.label}</span>
            </div>
          </React.Fragment>
        ))}
      </div>

      {/* Context Switcher */}
      {showContextSelector && (
        <div className="flex items-center space-x-2">
          {/* Current Context Display */}
          <div className="flex items-center space-x-2">
            {client && (
              <Badge variant="outline" className="bg-blue-50 text-blue-700">
                <Building2 className="h-3 w-3 mr-1" />
                {client.name}
              </Badge>
            )}
            {engagement && (
              <Badge variant="outline" className="bg-green-50 text-green-700">
                <Calendar className="h-3 w-3 mr-1" />
                {engagement.name}
              </Badge>
            )}
          </div>

          {/* Context Switcher Popover */}
          <Popover open={isContextSelectorOpen} onOpenChange={setIsContextSelectorOpen}>
            <PopoverTrigger asChild>
              <Button
                variant="outline"
                size="sm"
                className="h-8 px-3"
              >
                <Settings className="h-4 w-4 mr-1" />
                Switch Context
                <ChevronDown className="h-3 w-3 ml-1" />
              </Button>
            </PopoverTrigger>
            <PopoverContent className="w-96 p-4" align="end">
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <h4 className="font-medium">Switch Context</h4>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setIsContextSelectorOpen(false)}
                  >
                    ×
                  </Button>
                </div>

                {/* Client Selection */}
                <div className="space-y-2">
                  <label className="text-sm font-medium text-gray-700">
                    <Building2 className="h-4 w-4 inline mr-1" />
                    Client
                  </label>
                  <Select
                    value={selectedClientId}
                    onValueChange={handleClientChange}
                    disabled={clientsLoading}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select a client..." />
                    </SelectTrigger>
                    <SelectContent>
                      {clients.map((clientOption) => (
                        <SelectItem key={clientOption.id} value={clientOption.id}>
                          <div className="flex items-center">
                            <Building2 className="h-4 w-4 mr-2" />
                            {clientOption.name}
                          </div>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                {/* Engagement Selection */}
                <div className="space-y-2">
                  <label className="text-sm font-medium text-gray-700">
                    <Calendar className="h-4 w-4 inline mr-1" />
                    Engagement
                  </label>
                  <Select
                    value={selectedEngagementId}
                    onValueChange={handleEngagementChange}
                    disabled={!selectedClientId || engagementsLoading}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder={selectedClientId ? "Select an engagement..." : "Select a client first"} />
                    </SelectTrigger>
                    <SelectContent>
                      {engagements.map((engagementOption) => (
                        <SelectItem key={engagementOption.id} value={engagementOption.id}>
                          <div className="flex items-center justify-between w-full">
                            <div className="flex items-center">
                              <Calendar className="h-4 w-4 mr-2" />
                              {engagementOption.name}
                            </div>
                            {engagementOption.status && (
                              <Badge 
                                variant={engagementOption.status === 'active' ? 'default' : 'secondary'}
                                className="text-xs ml-2"
                              >
                                {engagementOption.status}
                              </Badge>
                            )}
                          </div>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                {/* Apply Button */}
                <div className="flex justify-end space-x-2 pt-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setIsContextSelectorOpen(false)}
                  >
                    Cancel
                  </Button>
                  <Button
                    size="sm"
                    onClick={handleApplyContext}
                    disabled={!selectedClientId || !selectedEngagementId}
                  >
                    Apply Context
                  </Button>
                </div>
              </div>
            </PopoverContent>
          </Popover>
        </div>
      )}
    </div>
  );
};

// Export as default for backward compatibility
export default ContextBreadcrumbs;