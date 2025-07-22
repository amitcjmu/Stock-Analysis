import { QualityIssue } from '../components/discovery/data-cleansing/QualityIssuesSummary';
import { AgentRecommendation } from '../components/discovery/data-cleansing/RecommendationsSummary';

/**
 * Fixed field highlighting function that properly matches assets and fields
 */
export const getFieldHighlight = (
  fieldName: string, 
  assetId: string, 
  rawData: unknown[], 
  qualityIssues: QualityIssue[], 
  agentRecommendations: AgentRecommendation[],
  selectedIssue: string | null,
  selectedRecommendation: string | null
): string => {
  let highlightClass = '';
  
  // Debug logging for troubleshooting
  const isDebugMode = typeof import.meta !== 'undefined' && import.meta.env?.DEV;
  
  // Highlight based on selected issue
  if (selectedIssue) {
    const issue = qualityIssues.find(i => i.id === selectedIssue);
    if (issue && issue.field_name) {
      if (isDebugMode) {
        console.log('🔍 Highlighting check:', {
          selectedIssue,
          issueFieldName: issue.field_name,
          tableFieldName: fieldName,
          tableAssetId: assetId,
          issueAssetId: issue.asset_id,
          issueAssetName: issue.asset_name
        });
      }
      
      // Convert field names for comparison - handle both uppercase and lowercase variations
      const normalizedIssueField = normalizeFieldName(issue.field_name);
      const normalizedTableField = normalizeFieldName(fieldName);
      
      if (isDebugMode) {
        console.log('🔍 Field name comparison:', {
          issueFieldName: issue.field_name,
          tableFieldName: fieldName,
          normalizedIssueField,
          normalizedTableField,
          exactMatch: issue.field_name === fieldName,
          normalizedMatch: normalizedIssueField === normalizedTableField
        });
      }
      
      // Try exact match first, then normalized match
      const fieldsMatch = issue.field_name === fieldName || normalizedIssueField === normalizedTableField;
      
      if (fieldsMatch) {
        // Find the asset in rawData by matching various identifier formats
        const currentAsset = findAssetByIdentifier(rawData, issue.asset_name || issue.asset_id);
        
        if (currentAsset) {
          // Get the asset identifier that matches what the table is using
          const tableAssetId = getAssetTableIdentifier(currentAsset);
          
          if (isDebugMode) {
            console.log('🎯 Asset matching:', {
              foundAsset: !!currentAsset,
              tableAssetId,
              tableRowAssetId: assetId,
              matches: tableAssetId === assetId
            });
          }
          
          // Check if this row matches the issue's asset
          if (tableAssetId === assetId) {
            highlightClass = 'bg-red-100 border border-red-300 ring-2 ring-red-200';
            if (isDebugMode) {
              console.log('✅ Applied red highlight for field:', fieldName, 'asset:', assetId);
            }
          }
        } else if (isDebugMode) {
          console.log('❌ Could not find asset in rawData for issue:', {
            searchTerm: issue.asset_name || issue.asset_id,
            availableAssets: rawData.slice(0, 3).map(a => ({
              id: a.id,
              asset_name: a.asset_name,
              hostname: a.hostname,
              name: a.name
            }))
          });
        }
      } else if (isDebugMode) {
        console.log('❌ Field names do not match:', {
          issueFieldName: issue.field_name,
          tableFieldName: fieldName,
          normalizedIssueField,
          normalizedTableField
        });
      }
    }
  }
  
  // Highlight based on selected recommendation (override issue highlighting)
  if (selectedRecommendation && !highlightClass) {
    const recommendation = agentRecommendations.find(r => r.id === selectedRecommendation);
    if (recommendation && recommendation.change_details?.fields_affected) {
      const normalizedTableField = normalizeFieldName(fieldName);
      const hasMatchingField = recommendation.change_details.fields_affected.some(field => 
        normalizeFieldName(field) === normalizedTableField
      );
      
      if (hasMatchingField) {
        highlightClass = 'bg-blue-100 border border-blue-300 ring-2 ring-blue-200';
        if (isDebugMode) {
          console.log('✅ Applied blue highlight for recommendation field:', fieldName);
        }
      }
    }
  }
  
  return highlightClass;
};

/**
 * Normalize field names for comparison (handle case insensitive and common variations)
 */
const normalizeFieldName = (fieldName: string): string => {
  if (!fieldName) return '';
  
  // Convert to lowercase and remove spaces, underscores, parentheses, and other special chars for comparison
  const normalized = fieldName.toLowerCase()
    .replace(/[\s_\-\(\)]/g, '')  // Remove spaces, underscores, dashes, parentheses
    .replace(/[^a-z0-9]/g, '');   // Remove any remaining special characters
  
  // Handle common field name variations - return a standardized version
  const fieldMappings: { [key: string]: string } = {
    'hostname': 'hostname',
    'assetname': 'hostname',
    'name': 'hostname',
    'assettype': 'type',
    'type': 'type',
    'ipaddress': 'ipaddress',
    'ip': 'ipaddress',
    'os': 'os',
    'operatingsystem': 'os',
    'environment': 'environment',
    'env': 'environment',
    'location': 'location',
    'datacenter': 'location',
    'owner': 'owner',
    'cpucores': 'cpucores',
    'cpu': 'cpucores',
    'ramgb': 'ramgb',
    'ram': 'ramgb',
    'memory': 'ramgb',
    'relatedcmdbrecords': 'relatedcmdbrecords',
    'related': 'relatedcmdbrecords'
  };
  
  return fieldMappings[normalized] || normalized;
};

/**
 * Find asset by various identifier formats - MUST match table's getAssetIdentifier logic exactly
 */
const findAssetByIdentifier = (rawData: unknown[], identifier: string): any | null => {
  if (!identifier || !rawData || rawData.length === 0) return null;
  
  return rawData.find(asset => {
    // Use the EXACT same logic as table's getAssetIdentifier: row.id || row.ID || row.asset_name || row.hostname || row.name || row.NAME || 'unknown'
    const tableAssetId = asset.id || asset.ID || asset.asset_name || asset.hostname || asset.name || asset.NAME || 'unknown';
    return tableAssetId === identifier;
  }) || null;
};

/**
 * Get the asset identifier that the table is using for row identification - MUST match RawDataTable exactly
 */
const getAssetTableIdentifier = (asset: unknown): string => {
  // EXACT same logic as RawDataTable's getAssetIdentifier: row.id || row.ID || row.asset_name || row.hostname || row.name || row.NAME || 'unknown'
  return asset.id || asset.ID || asset.asset_name || asset.hostname || asset.name || asset.NAME || 'unknown';
};

/**
 * Enhanced asset matching for table highlighting
 */
export const doesAssetMatch = (asset: any, targetIdentifier: string): boolean => {
  if (!asset || !targetIdentifier) return false;
  
  const identifiers = [
    asset.id,
    asset.ID, 
    asset.asset_name,
    asset.hostname,
    asset.name,
    asset.NAME,
    asset.HOSTNAME
  ].filter(Boolean);
  
  return identifiers.some(id => String(id) === String(targetIdentifier));
}; 