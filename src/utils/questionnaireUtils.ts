/**
 * Questionnaire Utility Functions
 * Handles multi-asset questionnaire processing and unique ID generation
 */

export interface QuestionWithAsset {
  field_id: string;
  question_text: string;
  field_type: string;
  required?: boolean;
  options?: any[];
  sub_questions?: QuestionWithAsset[];
  asset_id?: string;
  asset_specific?: boolean;
  metadata?: {
    asset_ids?: string[];
    [key: string]: any;
  };
}

export interface AssetQuestionGroup {
  asset_id: string;
  asset_name?: string;
  questions: QuestionWithAsset[];
  completion_percentage?: number;
}

/**
 * Extract asset ID from question metadata
 */
function getQuestionAssetId(question: QuestionWithAsset): string | null {
  // Direct asset_id field
  if (question.asset_id) {
    return question.asset_id;
  }

  // From metadata.asset_ids array (take first)
  if (question.metadata?.asset_ids && question.metadata.asset_ids.length > 0) {
    return question.metadata.asset_ids[0];
  }

  // Extract from field_id pattern like "app_technical_<asset_id>"
  const match = question.field_id.match(/[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}/);
  if (match) {
    return match[0];
  }

  return null;
}

/**
 * Generate unique field ID by combining parent and sub-question IDs
 */
export function generateUniqueFieldId(
  question: QuestionWithAsset,
  parentId?: string
): string {
  if (parentId) {
    return `${parentId}__${question.field_id}`;
  }
  return question.field_id;
}

/**
 * Flatten sub_questions with unique IDs
 */
export function flattenQuestionsWithUniqueIds(
  questions: QuestionWithAsset[]
): QuestionWithAsset[] {
  const flattened: QuestionWithAsset[] = [];

  for (const question of questions) {
    if (question.field_type === 'form_group' && question.sub_questions) {
      // Add parent question
      flattened.push(question);

      // Add sub-questions with unique IDs
      for (const subQ of question.sub_questions) {
        flattened.push({
          ...subQ,
          field_id: generateUniqueFieldId(subQ, question.field_id),
          metadata: {
            ...subQ.metadata,
            parent_field_id: question.field_id, // Track parent for form submission
          }
        });
      }
    } else {
      flattened.push(question);
    }
  }

  return flattened;
}

/**
 * Group questions by asset ID
 */
export function groupQuestionsByAsset(
  questions: QuestionWithAsset[],
  assets?: Array<{id: string; name?: string}>
): AssetQuestionGroup[] {
  const assetMap = new Map<string, QuestionWithAsset[]>();
  const globalQuestions: QuestionWithAsset[] = [];

  // First pass: flatten questions with unique IDs
  const flattenedQuestions = flattenQuestionsWithUniqueIds(questions);

  // Second pass: group by asset
  for (const question of flattenedQuestions) {
    const assetId = getQuestionAssetId(question);

    if (assetId) {
      if (!assetMap.has(assetId)) {
        assetMap.set(assetId, []);
      }
      assetMap.get(assetId)!.push(question);
    } else {
      // Questions without asset_id are global (apply to all assets)
      globalQuestions.push(question);
    }
  }

  // Build result array
  const groups: AssetQuestionGroup[] = [];

  for (const [assetId, assetQuestions] of assetMap.entries()) {
    const asset = assets?.find(a => a.id === assetId);
    groups.push({
      asset_id: assetId,
      asset_name: asset?.name || assetId.substring(0, 8),
      questions: [...globalQuestions, ...assetQuestions], // Include global + asset-specific
      completion_percentage: 0, // TODO: Calculate from saved responses
    });
  }

  // If no asset-specific questions, return single group with all global questions
  if (groups.length === 0 && globalQuestions.length > 0) {
    groups.push({
      asset_id: 'global',
      asset_name: 'General Information',
      questions: globalQuestions,
      completion_percentage: 0,
    });
  }

  return groups;
}

/**
 * Extract original field ID from unique composite ID
 * Used when submitting form to get the actual backend field_id
 */
export function extractOriginalFieldId(uniqueFieldId: string): {
  fieldId: string;
  parentId?: string;
} {
  const parts = uniqueFieldId.split('__');

  if (parts.length === 2) {
    return {
      fieldId: parts[1],
      parentId: parts[0],
    };
  }

  return { fieldId: uniqueFieldId };
}
