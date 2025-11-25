import { useQuery } from '@tanstack/react-query';
import { apiCall } from '@/config/api';
import type { TargetField } from '@/contexts/FieldOptionsContext';

interface UseTargetFieldsOptions {
  flowId?: string | null;
  importCategory?: string;
}

interface UseTargetFieldsResult {
  fields: TargetField[];
  isLoading: boolean;
  error: Error | null;
  refetch: () => Promise<TargetField[]>;
}

// Derived/Computed fields that should not appear in field mapping dropdowns
// These are calculated fields, not actual CMDB data fields
const DERIVED_FIELDS_EXCLUDED = new Set([
  'ai_gap_analysis_status',
  'ai_gap_analysis_timestamp',
  'assessment_readiness',
  'assessment_readiness_score',
  'assessment_blockers',
  'assessment_recommendations',
  'quality_score',
  'completeness_score',
  'confidence_score',
  'complexity_score',
]);

const buildEndpoint = (flowId?: string | null, importCategory?: string): string => {
  const params = new URLSearchParams();
  // Only pass flow_id - backend derives import_category from flow_id
  // Backend is single source of truth for import type resolution
  if (flowId) {
    params.append('flow_id', flowId);
  }

  return params.toString()
    ? `/data-import/available-target-fields?${params.toString()}`
    : '/data-import/available-target-fields';
};

export const useTargetFields = ({
  flowId,
  importCategory,
}: UseTargetFieldsOptions): UseTargetFieldsResult => {
  const queryKey = ['target-fields', flowId || 'default', importCategory || 'default'];

  const query = useQuery<TargetField[], Error>({
    queryKey,
    queryFn: async () => {
      const endpoint = buildEndpoint(flowId, importCategory);
      console.log('🔍 [useTargetFields] Fetching fields:', { flowId, importCategory, endpoint });
      const data = await apiCall(endpoint, { method: 'GET' });
      let fields = Array.isArray(data?.fields) ? data.fields : [];

      // Use importCategory prop if provided (explicit user selection), otherwise use backend response
      // Backend returns import_category in response based on flow_id or import_category query param
      const resolvedCategory = importCategory || data?.import_category;
      console.log('📥 [useTargetFields] Received fields from backend:', fields.length, 'resolved_category:', resolvedCategory);

      // First, exclude derived/computed fields (not actual CMDB data fields)
      const beforeDerivedFilter = fields.length;
      fields = fields.filter((field) =>
        !DERIVED_FIELDS_EXCLUDED.has(field.name)
      );
      console.log(`🔧 [useTargetFields] After derived filter: ${beforeDerivedFilter} → ${fields.length}`);

      // CRITICAL: ALWAYS filter by category if available
      // Backend sends all fields with import_types metadata - frontend MUST filter based on category
      if (resolvedCategory && resolvedCategory.trim() !== '' && fields.length > 0) {
        // Normalize category: "app-discovery" -> "app_discovery", "cmdb_export" -> "cmdb"
        const normalizedCategory = resolvedCategory.toLowerCase().replace(/-/g, '_').replace('cmdb_export', 'cmdb');
        console.log(`🎯 [useTargetFields] FILTERING for category: "${normalizedCategory}" (from "${resolvedCategory}")`);

        const beforeFilter = fields.length;
        fields = fields.filter((field) => {
          // Field must have import_types and it must include the normalized category
          if (field.import_types && field.import_types.length > 0) {
            return field.import_types.includes(normalizedCategory);
          }
          // Fields without import_types are excluded (strict filtering)
          return false;
        });
        console.log(`✅ [useTargetFields] FILTERED: ${beforeFilter} → ${fields.length} fields for "${normalizedCategory}"`);
      } else {
        // If no category available, return empty array rather than all fields
        // This prevents accidentally showing wrong fields when category is missing
        console.error('❌ [useTargetFields] No category to filter by! Cannot safely return fields.', {
          importCategory,
          resolvedCategory,
          backendImportCategory: data?.import_category,
          flowId
        });
        fields = [];
      }

      return fields;
    },
    staleTime: 60 * 1000,
    keepPreviousData: true,
  });

  return {
    fields: query.data ?? [],
    isLoading: query.isLoading,
    error: query.error ?? null,
    refetch: async () => (await query.refetch()).data ?? [],
  };
};
