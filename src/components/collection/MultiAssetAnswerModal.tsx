/**
 * MultiAssetAnswerModal Component
 *
 * Modal for bulk answering questions across multiple assets
 * with a 4-step wizard flow and conflict resolution.
 *
 * Wizard Steps:
 * 1. Asset Selection - Pick assets to update
 * 2. Questions - Answer questions with dropdown enforcement
 * 3. Conflicts - Resolve any conflicting existing answers
 * 4. Confirmation - Review and submit
 *
 * Features:
 * - Progress indicator (Question 3 of 12)
 * - Dropdown enforcement (no free text)
 * - "Other" option with validation (100 chars max)
 * - Preview-submit correlation (preview_id)
 */

import React, { useState, useEffect } from "react";
import { AssetPickerTable } from "./AssetPickerTable";
import { AnswerVariantReconciler } from "./AnswerVariantReconciler";
import {
  useBulkAnswerPreview,
  useBulkAnswerSubmit,
} from "@/hooks/collection/adaptive-questionnaire";
import type {
  QuestionDetail,
  AnswerInput,
} from "@/services/api/collection-flow";

export interface MultiAssetAnswerModalProps {
  flow_id: string;
  questions: QuestionDetail[];
  is_open: boolean;
  on_close: () => void;
  on_success?: (updated_count: number) => void;
}

type WizardStep = "select_assets" | "answer_questions" | "resolve_conflicts" | "confirm";

export const MultiAssetAnswerModal: React.FC<MultiAssetAnswerModalProps> = ({
  flow_id,
  questions,
  is_open,
  on_close,
  on_success,
}) => {
  const [current_step, set_current_step] = useState<WizardStep>("select_assets");
  const [selected_asset_ids, set_selected_asset_ids] = useState<string[]>([]);
  const [answers, set_answers] = useState<Record<string, string>>({});
  const [other_text_values, set_other_text_values] = useState<Record<string, string>>({});
  const [conflict_resolutions, set_conflict_resolutions] = useState<Record<string, string>>({});

  const preview_mutation = useBulkAnswerPreview();
  const submit_mutation = useBulkAnswerSubmit();

  // Reset state when modal opens/closes
  useEffect(() => {
    if (!is_open) {
      set_current_step("select_assets");
      set_selected_asset_ids([]);
      set_answers({});
      set_other_text_values({});
      set_conflict_resolutions({});
    }
  }, [is_open]);

  // Calculate progress
  const answered_questions = Object.keys(answers).length;
  const total_questions = questions.length;
  const progress_percent = total_questions > 0
    ? Math.round((answered_questions / total_questions) * 100)
    : 0;

  // Handle answer change
  const handle_answer_change = (question_id: string, value: string) => {
    set_answers((prev) => ({
      ...prev,
      [question_id]: value,
    }));

    // Clear "Other" text if switching away from "Other"
    if (value !== "Other") {
      set_other_text_values((prev) => {
        const updated = { ...prev };
        delete updated[question_id];
        return updated;
      });
    }
  };

  // Handle "Other" text input
  const handle_other_text_change = (question_id: string, text: string) => {
    // Enforce 100 character limit
    if (text.length <= 100) {
      set_other_text_values((prev) => ({
        ...prev,
        [question_id]: text,
      }));
    }
  };

  // Validate answers before proceeding
  const validate_answers = (): boolean => {
    // Check all questions are answered
    const unanswered = questions.filter((q) => !answers[q.question_id]);
    if (unanswered.length > 0) {
      alert(`Please answer all questions (${unanswered.length} remaining)`);
      return false;
    }

    // Check "Other" fields have text
    const incomplete_other = questions.filter(
      (q) =>
        answers[q.question_id] === "Other" &&
        (!other_text_values[q.question_id] ||
          other_text_values[q.question_id].trim() === "")
    );
    if (incomplete_other.length > 0) {
      alert("Please provide text for all 'Other' selections");
      return false;
    }

    return true;
  };

  // Handle next step
  const handle_next_step = async () => {
    if (current_step === "select_assets") {
      if (selected_asset_ids.length === 0) {
        alert("Please select at least one asset");
        return;
      }
      set_current_step("answer_questions");
    } else if (current_step === "answer_questions") {
      if (!validate_answers()) {
        return;
      }

      // Preview to check for conflicts
      const question_ids = questions.map((q) => q.question_id);
      try {
        const preview_result = await preview_mutation.mutateAsync({
          child_flow_id: flow_id,
          asset_ids: selected_asset_ids,
          question_ids,
        });

        if (preview_result.potential_conflicts > 0) {
          set_current_step("resolve_conflicts");
        } else {
          set_current_step("confirm");
        }
      } catch (error) {
        console.error("Preview failed:", error);
        alert("Failed to preview bulk answers. Please try again.");
      }
    } else if (current_step === "resolve_conflicts") {
      // Check all conflicts are resolved
      const conflicts = preview_mutation.data?.conflicts || [];
      const all_resolved = conflicts.every(
        (c) => conflict_resolutions[c.question_id]
      );

      if (!all_resolved) {
        alert("Please resolve all conflicts before proceeding");
        return;
      }

      set_current_step("confirm");
    }
  };

  // Handle previous step
  const handle_previous_step = () => {
    if (current_step === "answer_questions") {
      set_current_step("select_assets");
    } else if (current_step === "resolve_conflicts") {
      set_current_step("answer_questions");
    } else if (current_step === "confirm") {
      if (preview_mutation.data?.potential_conflicts) {
        set_current_step("resolve_conflicts");
      } else {
        set_current_step("answer_questions");
      }
    }
  };

  // Handle submit
  const handle_submit = async () => {
    const answer_inputs: AnswerInput[] = questions.map((q) => {
      let answer_value = answers[q.question_id];

      // Use "Other" text if applicable
      if (answer_value === "Other") {
        answer_value = other_text_values[q.question_id] || "";
      }

      return {
        question_id: q.question_id,
        answer_value,
      };
    });

    try {
      const result = await submit_mutation.mutateAsync({
        child_flow_id: flow_id,
        asset_ids: selected_asset_ids,
        answers: answer_inputs,
        conflict_resolution_strategy: "overwrite",
      });

      if (result.success) {
        on_success?.(result.assets_updated);
        on_close();
      } else {
        alert("Some assets failed to update. Please check the results.");
      }
    } catch (error) {
      console.error("Submit failed:", error);
      alert("Failed to submit bulk answers. Please try again.");
    }
  };

  if (!is_open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-4xl max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="px-6 py-4 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold text-gray-900">
              Bulk Answer Multiple Assets
            </h2>
            <button
              onClick={on_close}
              className="text-gray-400 hover:text-gray-600"
            >
              ✕
            </button>
          </div>

          {/* Progress Indicator */}
          {current_step === "answer_questions" && (
            <div className="mt-3">
              <div className="flex items-center justify-between text-sm mb-1">
                <span className="text-gray-600">
                  Question {answered_questions} of {total_questions}
                </span>
                <span className="text-gray-600">{progress_percent}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${progress_percent}%` }}
                />
              </div>
            </div>
          )}
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto px-6 py-4">
          {/* Step 1: Asset Selection */}
          {current_step === "select_assets" && (
            <div>
              <h3 className="text-lg font-medium text-gray-900 mb-4">
                Step 1: Select Assets
              </h3>
              <AssetPickerTable
                flow_id={flow_id}
                selected_asset_ids={selected_asset_ids}
                on_selection_change={set_selected_asset_ids}
                max_selection={1000}
              />
            </div>
          )}

          {/* Step 2: Answer Questions */}
          {current_step === "answer_questions" && (
            <div>
              <h3 className="text-lg font-medium text-gray-900 mb-4">
                Step 2: Answer Questions
              </h3>
              <div className="space-y-4">
                {questions.map((question) => {
                  const current_answer = answers[question.question_id];
                  const has_other = question.answer_options?.includes("Other");

                  return (
                    <div key={question.question_id} className="p-4 border border-gray-200 rounded-lg">
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        {question.question_text}
                        {question.is_required && (
                          <span className="text-red-600 ml-1">*</span>
                        )}
                      </label>

                      <select
                        value={current_answer || ""}
                        onChange={(e) =>
                          handle_answer_change(question.question_id, e.target.value)
                        }
                        className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
                      >
                        <option value="">-- Select answer --</option>
                        {question.answer_options?.map((option) => (
                          <option key={option} value={option}>
                            {option}
                          </option>
                        ))}
                      </select>

                      {/* "Other" text input */}
                      {has_other && current_answer === "Other" && (
                        <div className="mt-2">
                          <input
                            type="text"
                            placeholder="Please specify (max 100 characters)"
                            value={other_text_values[question.question_id] || ""}
                            onChange={(e) =>
                              handle_other_text_change(
                                question.question_id,
                                e.target.value
                              )
                            }
                            maxLength={100}
                            className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
                          />
                          <p className="text-xs text-gray-500 mt-1">
                            {other_text_values[question.question_id]?.length || 0} / 100 characters
                          </p>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Step 3: Resolve Conflicts */}
          {current_step === "resolve_conflicts" && preview_mutation.data && (
            <div>
              <h3 className="text-lg font-medium text-gray-900 mb-4">
                Step 3: Resolve Conflicts
              </h3>
              <AnswerVariantReconciler
                conflicts={preview_mutation.data.conflicts}
                on_resolution_change={set_conflict_resolutions}
                question_texts={Object.fromEntries(
                  questions.map((q) => [q.question_id, q.question_text])
                )}
              />
            </div>
          )}

          {/* Step 4: Confirmation */}
          {current_step === "confirm" && (
            <div>
              <h3 className="text-lg font-medium text-gray-900 mb-4">
                Step 4: Review & Confirm
              </h3>
              <div className="space-y-4">
                <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
                  <h4 className="font-medium text-blue-900 mb-2">Summary</h4>
                  <ul className="text-sm text-blue-700 space-y-1">
                    <li>• {selected_asset_ids.length} assets will be updated</li>
                    <li>• {total_questions} questions will be answered</li>
                    {preview_mutation.data?.potential_conflicts ? (
                      <li>• {preview_mutation.data.potential_conflicts} conflicts resolved</li>
                    ) : null}
                  </ul>
                </div>

                <div className="p-4 border border-gray-200 rounded-lg">
                  <h4 className="font-medium text-gray-900 mb-3">Answers</h4>
                  <div className="space-y-2">
                    {questions.map((q) => {
                      let display_answer = answers[q.question_id];
                      if (display_answer === "Other") {
                        display_answer = other_text_values[q.question_id] || "";
                      }

                      return (
                        <div key={q.question_id} className="flex justify-between text-sm">
                          <span className="text-gray-600">{q.question_text}</span>
                          <span className="font-medium text-gray-900">{display_answer}</span>
                        </div>
                      );
                    })}
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-gray-200 flex justify-between">
          <button
            onClick={handle_previous_step}
            disabled={current_step === "select_assets"}
            className="px-4 py-2 text-gray-700 border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Previous
          </button>

          {current_step === "confirm" ? (
            <button
              onClick={handle_submit}
              disabled={submit_mutation.isPending}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {submit_mutation.isPending ? "Submitting..." : "Submit"}
            </button>
          ) : (
            <button
              onClick={handle_next_step}
              disabled={preview_mutation.isPending}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {preview_mutation.isPending ? "Loading..." : "Next"}
            </button>
          )}
        </div>
      </div>
    </div>
  );
};
