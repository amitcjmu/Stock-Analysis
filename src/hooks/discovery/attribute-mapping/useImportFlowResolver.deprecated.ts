/**
 * @deprecated Use useSmartFlowResolver instead - it handles both import ID resolution and recent flow detection
 * This file is kept for backward compatibility but should not be used in new code
 */

import { useEffect, useState } from 'react';
import { apiCall } from '@/config/api';
import { useAuth } from '@/contexts/AuthContext';

interface ImportData {
  id: string;
  master_flow_id: string;
  status: string;
  [key: string]: unknown;
}

interface UseImportFlowResolverResult {
  resolvedFlowId: string | null;
  isResolving: boolean;
  error: Error | null;
  importData: ImportData | null;
}

/**
 * @deprecated Use useSmartFlowResolver instead
 * Hook to resolve a data import ID to its master flow ID
 * This is needed when navigating to attribute mapping with an import ID in the URL
 */
export function useImportFlowResolver(importId: string | undefined): UseImportFlowResolverResult {
  const [resolvedFlowId, setResolvedFlowId] = useState<string | null>(null);
  const [isResolving, setIsResolving] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const [importData, setImportData] = useState<ImportData | null>(null);
  const { user, client, engagement } = useAuth();

  useEffect(() => {
    if (!importId) {
      setResolvedFlowId(null);
      setImportData(null);
      return;
    }

    // Check if this is already a valid flow ID (UUID v4 format)
    // If it's a flow ID, just pass it through without resolution
    const isValidFlowId = /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(importId);

    if (isValidFlowId) {
      // This is already a flow ID, no need to resolve
      console.log(`✅ ${importId} is already a valid flow ID, no resolution needed`);
      setResolvedFlowId(importId);
      setIsResolving(false);
      return;
    }

    // Otherwise, try to resolve it as an import ID
    const resolveImportToFlow = async () => {
      setIsResolving(true);
      setError(null);

      try {
        // Try to fetch the import data
        const headers: Record<string, string> = {};
        if (client?.account_id) {
          headers['X-Client-Account-ID'] = client.account_id;
        }
        if (engagement?.id) {
          headers['X-Engagement-ID'] = engagement.id;
        }

        console.log(`🔍 Attempting to resolve import ID ${importId} to flow ID`);

        // Try to get the import details using the data-import API endpoint
        // Note: The API is still /data-import even though the frontend page is /cmdb-import
        const response = await apiCall(`/api/v1/data-import/imports/${importId}`, {
          method: 'GET',
          headers
        });

        if (response && response.master_flow_id) {
          console.log(`✅ Resolved import ID ${importId} to flow ID ${response.master_flow_id}`);
          setResolvedFlowId(response.master_flow_id);
          setImportData(response);
        } else {
          // If no master_flow_id, this might actually be a flow ID
          // Let the normal flow detection handle it
          console.log(`⚠️ No master_flow_id found for ${importId}, treating as potential flow ID`);
          setResolvedFlowId(importId);
        }
      } catch (err) {
        // If we get a 404, this might be a flow ID not an import ID
        if (err && typeof err === 'object' && 'status' in err && err.status === 404) {
          console.log(`📌 ${importId} not found as import, treating as flow ID`);
          setResolvedFlowId(importId);
        } else {
          console.error(`❌ Error resolving import ID ${importId}:`, err);
          setError(err as Error);
          // Still pass through the ID in case it's a flow ID
          setResolvedFlowId(importId);
        }
      } finally {
        setIsResolving(false);
      }
    };

    resolveImportToFlow();
  }, [importId, client, engagement]);

  return {
    resolvedFlowId,
    isResolving,
    error,
    importData
  };
}
