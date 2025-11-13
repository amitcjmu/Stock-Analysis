/**
 * AnswerVariantReconciler Component
 *
 * Displays conflicting answers from multiple assets and provides
 * conflict resolution with a "Keep Majority" quick action.
 *
 * Features:
 * - Groups answers by value with asset counts
 * - "Keep Majority" button (auto-selects most common answer)
 * - Majority badge on winning answer
 * - Manual dropdown override option
 */

import React, { useState, useEffect, useMemo } from "react";
import type { ConflictDetail } from "@/services/api/collection-flow";

export interface AnswerVariantReconcilerProps {
  conflicts: ConflictDetail[];
  on_resolution_change: (resolutions: Record<string, string>) => void;
  question_texts?: Record<string, string>;
}

export const AnswerVariantReconciler: React.FC<AnswerVariantReconcilerProps> = ({
  conflicts,
  on_resolution_change,
  question_texts = {},
}) => {
  // Store user's resolution choices (question_id -> selected_answer)
  const [resolutions, set_resolutions] = useState<Record<string, string>>({});

  // Calculate majority answer for each conflict
  const majority_answers = useMemo(() => {
    const result: Record<string, string> = {};

    conflicts.forEach((conflict) => {
      // Find answer with most assets
      let max_count = 0;
      let majority_answer = "";

      Object.entries(conflict.existing_answers).forEach(
        ([answer, asset_ids]) => {
          if (asset_ids.length > max_count) {
            max_count = asset_ids.length;
            majority_answer = answer;
          }
        }
      );

      result[conflict.question_id] = majority_answer;
    });

    return result;
  }, [conflicts]);

  // Emit resolution changes to parent
  useEffect(() => {
    on_resolution_change(resolutions);
  }, [resolutions, on_resolution_change]);

  // Handle "Keep Majority" quick action
  const handle_keep_majority = () => {
    set_resolutions(majority_answers);
  };

  // Handle individual question resolution
  const handle_question_resolution = (
    question_id: string,
    selected_answer: string
  ) => {
    set_resolutions((prev) => ({
      ...prev,
      [question_id]: selected_answer,
    }));
  };

  // Check if all conflicts are resolved
  const all_resolved =
    conflicts.length > 0 &&
    conflicts.every((conflict) => resolutions[conflict.question_id]);

  // Check if current resolutions match majority
  const is_majority_selected = useMemo(() => {
    return conflicts.every(
      (conflict) =>
        resolutions[conflict.question_id] === majority_answers[conflict.question_id]
    );
  }, [conflicts, resolutions, majority_answers]);

  if (conflicts.length === 0) {
    return (
      <div className="p-4 text-center text-gray-500">
        No conflicts detected. All assets can receive the same answers.
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Header with Quick Action */}
      <div className="flex items-center justify-between p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
        <div>
          <h3 className="font-medium text-yellow-900">
            {conflicts.length} Question{conflicts.length !== 1 ? "s" : ""} with Conflicts
          </h3>
          <p className="text-sm text-yellow-700 mt-1">
            Selected assets have different existing answers. Choose which answer to keep.
          </p>
        </div>
        <button
          onClick={handle_keep_majority}
          disabled={is_majority_selected}
          className={`px-4 py-2 rounded-md font-medium ${
            is_majority_selected
              ? "bg-gray-200 text-gray-500 cursor-not-allowed"
              : "bg-blue-600 text-white hover:bg-blue-700"
          }`}
        >
          Keep Majority
        </button>
      </div>

      {/* Conflict List */}
      <div className="space-y-4">
        {conflicts.map((conflict) => {
          const question_text =
            question_texts[conflict.question_id] ||
            `Question ${conflict.question_id}`;
          const selected_answer = resolutions[conflict.question_id];
          const majority_answer = majority_answers[conflict.question_id];

          // Sort answers by asset count (descending)
          const sorted_answers = Object.entries(conflict.existing_answers).sort(
            ([, a_ids], [, b_ids]) => b_ids.length - a_ids.length
          );

          return (
            <div
              key={conflict.question_id}
              className="p-4 border border-gray-200 rounded-lg"
            >
              {/* Question Text */}
              <h4 className="font-medium text-gray-900 mb-3">{question_text}</h4>

              {/* Answer Variants */}
              <div className="space-y-2 mb-3">
                {sorted_answers.map(([answer, asset_ids]) => {
                  const is_majority = answer === majority_answer;
                  const is_selected = answer === selected_answer;

                  return (
                    <label
                      key={answer}
                      className={`flex items-center p-3 border-2 rounded-md cursor-pointer transition-colors ${
                        is_selected
                          ? "border-blue-500 bg-blue-50"
                          : "border-gray-200 hover:border-gray-300"
                      }`}
                    >
                      <input
                        type="radio"
                        name={`conflict-${conflict.question_id}`}
                        checked={is_selected}
                        onChange={() =>
                          handle_question_resolution(conflict.question_id, answer)
                        }
                        className="mr-3 text-blue-600 focus:ring-blue-500"
                      />
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <span className="font-medium text-gray-900">
                            {answer}
                          </span>
                          {is_majority && (
                            <span className="px-2 py-0.5 text-xs font-medium text-blue-700 bg-blue-100 rounded-full">
                              Majority
                            </span>
                          )}
                        </div>
                        <span className="text-sm text-gray-500">
                          {asset_ids.length} asset{asset_ids.length !== 1 ? "s" : ""}
                        </span>
                      </div>
                    </label>
                  );
                })}
              </div>

              {/* Manual Dropdown Override (if needed for complex cases) */}
              {sorted_answers.length > 3 && (
                <div className="mt-3 pt-3 border-t border-gray-200">
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Or select from all answers:
                  </label>
                  <select
                    value={selected_answer || ""}
                    onChange={(e) =>
                      handle_question_resolution(
                        conflict.question_id,
                        e.target.value
                      )
                    }
                    className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="">-- Select answer --</option>
                    {sorted_answers.map(([answer]) => (
                      <option key={answer} value={answer}>
                        {answer}
                      </option>
                    ))}
                  </select>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Resolution Status */}
      <div
        className={`p-3 rounded-md ${
          all_resolved
            ? "bg-green-50 border border-green-200 text-green-700"
            : "bg-gray-50 border border-gray-200 text-gray-600"
        }`}
      >
        {all_resolved ? (
          <span className="font-medium">✓ All conflicts resolved</span>
        ) : (
          <span>
            {conflicts.filter((c) => !resolutions[c.question_id]).length} conflict
            {conflicts.filter((c) => !resolutions[c.question_id]).length !== 1
              ? "s"
              : ""}{" "}
            remaining
          </span>
        )}
      </div>
    </div>
  );
};
