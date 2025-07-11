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
  const [availableFields, setAvailableFields] = useState<TargetField[]>(DEFAULT_FIELDS);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const [hasInitialized, setHasInitialized] = useState(false);

  // Demo client/engagement IDs for fetching field options at startup
  const DEMO_CLIENT_ID = '21990f3a-abb6-4862-be06-cb6f854e167b';
  const DEMO_ENGAGEMENT_ID = '58467010-6a72-44e8-ba37-cc0238724455';

  const fetchAvailableFields = async () => {
    // Prevent multiple fetches - only fetch once per application session
    if (hasInitialized && lastUpdated) {
      console.log('🔍 FieldOptionsProvider - Already initialized, skipping fetch');
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      console.log('🔍 FieldOptionsProvider - Fetching available fields at startup using demo context');
      
      // Use demo client/engagement context for field options fetch
      const response = await apiCall(API_CONFIG.ENDPOINTS.DISCOVERY.AVAILABLE_TARGET_FIELDS, {
        method: 'GET',
        headers: {
          'X-Client-Account-ID': DEMO_CLIENT_ID,
          'X-Engagement-ID': DEMO_ENGAGEMENT_ID
        }
      });

      if (response?.fields) {
        setAvailableFields(response.fields);
        setLastUpdated(new Date());
        setHasInitialized(true);
        console.log('✅ FieldOptionsProvider - Loaded', response.fields.length, 'fields from API using demo context');
      } else if (response?.data?.available_fields) {
        setAvailableFields(response.data.available_fields);
        setLastUpdated(new Date());
        setHasInitialized(true);
        console.log('✅ FieldOptionsProvider - Loaded', response.data.available_fields.length, 'fields from API using demo context');
      } else {
        console.log('⚠️ FieldOptionsProvider - No fields in response, using defaults');
        setAvailableFields(DEFAULT_FIELDS);
        setLastUpdated(new Date());
        setHasInitialized(true);
      }
    } catch (err) {
      console.error('❌ FieldOptionsProvider - Error fetching fields with demo context:', err);
      setError('Failed to load field options');
      setAvailableFields(DEFAULT_FIELDS); // Always provide fallback
      setHasInitialized(true); // Don't retry on error
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    // Fetch field options immediately at startup using demo context
    // This eliminates the need for authentication context and prevents multiple API calls
    if (!hasInitialized) {
      console.log('🚀 FieldOptionsProvider - Initializing field options at application startup');
      fetchAvailableFields();
    }
  }, [hasInitialized]);

  const refetchFields = async () => {
    console.log('🔄 FieldOptionsProvider - Manual refetch requested');
    // Reset initialization state to allow refetch
    setHasInitialized(false);
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