import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { apiCall, API_CONFIG } from '../config/api';
import { useAuth } from './AuthContext';

// Types
interface TargetField {
  name: string;
  type: string;
  required: boolean;
  description: string;
  category: string;
  is_custom?: boolean;
}

interface FieldOptionsContextType {
  availableFields: TargetField[];
  isLoading: boolean;
  error: string | null;
  refetchFields: () => Promise<void>;
  lastUpdated: Date | null;
}

const FieldOptionsContext = createContext<FieldOptionsContextType | undefined>(undefined);

// Default fallback fields to ensure the app never breaks
const DEFAULT_FIELDS: TargetField[] = [
  { name: 'hostname', type: 'string', required: true, description: 'Server hostname', category: 'identity' },
  { name: 'ip_address', type: 'string', required: true, description: 'IP address', category: 'network' },
  { name: 'operating_system', type: 'string', required: false, description: 'Operating system', category: 'system' },
  { name: 'application_name', type: 'string', required: false, description: 'Application name', category: 'application' },
  { name: 'environment', type: 'string', required: false, description: 'Environment (prod, dev, test)', category: 'business' },
  { name: 'owner', type: 'string', required: false, description: 'Asset owner', category: 'business' },
  { name: 'cost_center', type: 'string', required: false, description: 'Cost center', category: 'business' },
  { name: 'criticality', type: 'string', required: false, description: 'Business criticality', category: 'business' },
  { name: 'cpu_cores', type: 'number', required: false, description: 'CPU cores', category: 'system' },
  { name: 'memory_gb', type: 'number', required: false, description: 'Memory in GB', category: 'system' },
  { name: 'storage_gb', type: 'number', required: false, description: 'Storage in GB', category: 'system' },
  { name: 'location', type: 'string', required: false, description: 'Physical location', category: 'system' },
  { name: 'version', type: 'string', required: false, description: 'Software version', category: 'application' },
  { name: 'dependencies', type: 'string', required: false, description: 'Dependencies', category: 'application' },
  { name: 'port', type: 'number', required: false, description: 'Service port', category: 'network' },
  { name: 'protocol', type: 'string', required: false, description: 'Network protocol', category: 'network' },
  { name: 'database', type: 'string', required: false, description: 'Database name', category: 'application' },
  { name: 'tech_stack', type: 'string', required: false, description: 'Technology stack', category: 'application' }
];

interface FieldOptionsProviderProps {
  children: ReactNode;
}

export const FieldOptionsProvider: React.FC<FieldOptionsProviderProps> = ({ children }) => {
  const { client, engagement, isAuthenticated } = useAuth();
  const [availableFields, setAvailableFields] = useState<TargetField[]>(DEFAULT_FIELDS);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const [hasInitialized, setHasInitialized] = useState(false);
  const [contextCheckRetries, setContextCheckRetries] = useState(0);

  const fetchAvailableFields = async () => {
    // Only fetch if user is authenticated and we have proper context
    if (!isAuthenticated || !client?.id || !engagement?.id) {
      console.log('🔍 FieldOptionsProvider - Not authenticated or no context, using default fields', {
        isAuthenticated,
        clientId: client?.id,
        engagementId: engagement?.id
      });
      if (!hasInitialized) {
        setAvailableFields(DEFAULT_FIELDS);
        setLastUpdated(new Date());
        setHasInitialized(true);
      }
      return;
    }

    // Prevent multiple fetches - only fetch once per application session
    if (hasInitialized && lastUpdated) {
      console.log('🔍 FieldOptionsProvider - Already initialized, skipping fetch');
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      console.log('🔍 FieldOptionsProvider - Fetching available fields (one-time per session)', {
        clientId: client.id,
        engagementId: engagement.id
      });
      const response = await apiCall(API_CONFIG.ENDPOINTS.DISCOVERY.AVAILABLE_TARGET_FIELDS, {
        method: 'GET',
        includeContext: true // Use the centralized context handling
      });

      if (response?.fields) {
        setAvailableFields(response.fields);
        setLastUpdated(new Date());
        setHasInitialized(true);
        console.log('✅ FieldOptionsProvider - Loaded', response.fields.length, 'fields from API');
      } else if (response?.data?.available_fields) {
        setAvailableFields(response.data.available_fields);
        setLastUpdated(new Date());
        setHasInitialized(true);
        console.log('✅ FieldOptionsProvider - Loaded', response.data.available_fields.length, 'fields from API');
      } else {
        console.log('⚠️ FieldOptionsProvider - No fields in response, using defaults');
        setAvailableFields(DEFAULT_FIELDS);
        setLastUpdated(new Date());
        setHasInitialized(true);
      }
    } catch (err) {
      console.error('❌ FieldOptionsProvider - Error fetching fields:', err);
      setError('Failed to load field options');
      setAvailableFields(DEFAULT_FIELDS); // Always provide fallback
      setHasInitialized(true); // Don't retry on error
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    // Only attempt to fetch when user becomes authenticated and we have full context
    if (isAuthenticated && client?.id && engagement?.id && !hasInitialized) {
      // Reset retry counter since we now have context
      setContextCheckRetries(0);
      // Add a small delay to ensure context is fully synchronized
      const timer = setTimeout(() => {
        fetchAvailableFields();
      }, 100);
      return () => clearTimeout(timer);
    }
    
    // Retry logic for when user is authenticated but context is not yet available
    if (isAuthenticated && (!client?.id || !engagement?.id) && !hasInitialized && contextCheckRetries < 3) {
      const timer = setTimeout(() => {
        console.log(`🔄 FieldOptionsProvider - Retry ${contextCheckRetries + 1}/3 - waiting for context`, {
          isAuthenticated,
          clientId: client?.id,
          engagementId: engagement?.id
        });
        setContextCheckRetries(prev => prev + 1);
      }, 200 * (contextCheckRetries + 1)); // Exponential backoff: 200ms, 400ms, 600ms
      return () => clearTimeout(timer);
    }
  }, [isAuthenticated, client?.id, engagement?.id, hasInitialized, contextCheckRetries]);

  const refetchFields = async () => {
    console.log('🔄 FieldOptionsProvider - Manual refetch requested');
    // Reset initialization state to allow refetch
    setHasInitialized(false);
    setContextCheckRetries(0);
    await fetchAvailableFields();
  };

  return (
    <FieldOptionsContext.Provider
      value={{
        availableFields,
        isLoading,
        error,
        refetchFields,
        lastUpdated
      }}
    >
      {children}
    </FieldOptionsContext.Provider>
  );
};

export const useFieldOptions = (): FieldOptionsContextType => {
  const context = useContext(FieldOptionsContext);
  if (context === undefined) {
    throw new Error('useFieldOptions must be used within a FieldOptionsProvider');
  }
  return context;
};

// Export types for use in other components
export type { TargetField };