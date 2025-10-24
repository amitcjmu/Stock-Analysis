/**
 * BulkImportWizard Component
 *
 * Guided CSV/JSON import wizard with intelligent field mapping
 * and gap analysis integration.
 *
 * Wizard Steps:
 * 1. File Upload - Drag-drop upload (10 MB limit)
 * 2. Field Mapping - AI-suggested mappings with confidence badges
 * 3. Configuration - Overwrite/fill strategy + gap analysis mode
 * 4. Progress - Real-time import progress with stage indicator
 * 5. Results - Summary with gap analysis results
 */

import React, { useState, useCallback, useEffect } from "react";
import {
  useBulkImportAnalyze,
  useBulkImportExecute,
  useImportTaskStatus,
} from "@/hooks/collection/adaptive-questionnaire";
import type {
  ImportAnalysisResponse,
  FieldMappingSuggestion,
} from "@/services/api/collection-flow";

export interface BulkImportWizardProps {
  flow_id: string;
  import_type: "application" | "server" | "database";
  is_open: boolean;
  on_close: () => void;
  on_success?: (rows_imported: number) => void;
}

type WizardStep = "upload" | "mapping" | "config" | "progress" | "results";

const MAX_FILE_SIZE_MB = 10;
const MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024;

export const BulkImportWizard: React.FC<BulkImportWizardProps> = ({
  flow_id,
  import_type,
  is_open,
  on_close,
  on_success,
}) => {
  const [current_step, set_current_step] = useState<WizardStep>("upload");
  const [selected_file, set_selected_file] = useState<File | null>(null);
  const [drag_active, set_drag_active] = useState(false);

  const [analysis_result, set_analysis_result] = useState<ImportAnalysisResponse | null>(null);
  const [field_mappings, set_field_mappings] = useState<Record<string, string>>({});
  const [overwrite_existing, set_overwrite_existing] = useState(false);
  const [gap_recalculation_mode, set_gap_recalculation_mode] = useState<"fast" | "thorough">("fast");
  const [task_id, set_task_id] = useState<string | null>(null);

  const analyze_mutation = useBulkImportAnalyze();
  const execute_mutation = useBulkImportExecute();
  const { data: task_status } = useImportTaskStatus({
    task_id: task_id || undefined,
    enabled: !!task_id,
  });

  // Reset state when modal opens/closes
  useEffect(() => {
    if (!is_open) {
      set_current_step("upload");
      set_selected_file(null);
      set_analysis_result(null);
      set_field_mappings({});
      set_overwrite_existing(false);
      set_gap_recalculation_mode("fast");
      set_task_id(null);
    }
  }, [is_open]);

  // Auto-advance to results when import completes
  useEffect(() => {
    if (task_status && (task_status.status === "completed" || task_status.status === "failed")) {
      set_current_step("results");
      if (task_status.status === "completed" && task_status.rows_processed) {
        on_success?.(task_status.rows_processed);
      }
    }
  }, [task_status, on_success]);

  // Handle file selection
  const handle_file_select = (file: File) => {
    // Validate file size
    if (file.size > MAX_FILE_SIZE_BYTES) {
      alert(`File size exceeds ${MAX_FILE_SIZE_MB} MB limit`);
      return;
    }

    // Validate file type
    const extension = file.name.split(".").pop()?.toLowerCase();
    if (extension !== "csv" && extension !== "json") {
      alert("Only CSV and JSON files are supported");
      return;
    }

    set_selected_file(file);
  };

  // Handle drag events
  const handle_drag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();

    if (e.type === "dragenter" || e.type === "dragover") {
      set_drag_active(true);
    } else if (e.type === "dragleave") {
      set_drag_active(false);
    }
  }, []);

  const handle_drop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    set_drag_active(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handle_file_select(e.dataTransfer.files[0]);
    }
  }, []);

  // Handle analyze step
  const handle_analyze = async () => {
    if (!selected_file) return;

    try {
      const result = await analyze_mutation.mutateAsync({
        file: selected_file,
        import_type,
      });

      set_analysis_result(result);

      // Pre-populate field mappings from suggestions
      const mappings: Record<string, string> = {};
      result.suggested_mappings.forEach((suggestion) => {
        if (suggestion.suggested_field) {
          mappings[suggestion.csv_column] = suggestion.suggested_field;
        }
      });
      set_field_mappings(mappings);

      set_current_step("mapping");
    } catch (error) {
      console.error("Analysis failed:", error);
      alert("Failed to analyze file. Please check the file format and try again.");
    }
  };

  // Handle execute import
  const handle_execute = async () => {
    if (!analysis_result) return;

    try {
      const result = await execute_mutation.mutateAsync({
        child_flow_id: flow_id,
        import_batch_id: analysis_result.import_batch_id,
        confirmed_mappings: field_mappings,
        import_type,
        overwrite_existing,
        gap_recalculation_mode,
      });

      set_task_id(result.id);
      set_current_step("progress");
    } catch (error) {
      console.error("Import execution failed:", error);
      alert("Failed to start import. Please try again.");
    }
  };

  // Get confidence badge color
  const get_confidence_color = (confidence: number): string => {
    if (confidence >= 0.9) return "bg-green-100 text-green-800";
    if (confidence >= 0.7) return "bg-yellow-100 text-yellow-800";
    return "bg-red-100 text-red-800";
  };

  if (!is_open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-4xl max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="px-6 py-4 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold text-gray-900">
              Bulk Import - {import_type.charAt(0).toUpperCase() + import_type.slice(1)}s
            </h2>
            <button
              onClick={on_close}
              className="text-gray-400 hover:text-gray-600"
            >
              ✕
            </button>
          </div>

          {/* Step Indicator */}
          <div className="mt-4 flex items-center justify-between text-sm">
            {["upload", "mapping", "config", "progress", "results"].map((step, index) => (
              <div
                key={step}
                className={`flex items-center ${index < 4 ? "flex-1" : ""}`}
              >
                <div
                  className={`w-8 h-8 rounded-full flex items-center justify-center font-medium ${
                    current_step === step
                      ? "bg-blue-600 text-white"
                      : ["upload", "mapping", "config", "progress", "results"].indexOf(current_step) >
                        index
                      ? "bg-green-600 text-white"
                      : "bg-gray-200 text-gray-600"
                  }`}
                >
                  {index + 1}
                </div>
                {index < 4 && (
                  <div
                    className={`flex-1 h-1 mx-2 ${
                      ["upload", "mapping", "config", "progress", "results"].indexOf(current_step) >
                      index
                        ? "bg-green-600"
                        : "bg-gray-200"
                    }`}
                  />
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto px-6 py-4">
          {/* Step 1: File Upload */}
          {current_step === "upload" && (
            <div>
              <h3 className="text-lg font-medium text-gray-900 mb-4">
                Step 1: Upload File
              </h3>

              <div
                onDragEnter={handle_drag}
                onDragLeave={handle_drag}
                onDragOver={handle_drag}
                onDrop={handle_drop}
                className={`border-2 border-dashed rounded-lg p-8 text-center ${
                  drag_active
                    ? "border-blue-500 bg-blue-50"
                    : "border-gray-300"
                }`}
              >
                {selected_file ? (
                  <div>
                    <p className="text-lg font-medium text-gray-900">
                      {selected_file.name}
                    </p>
                    <p className="text-sm text-gray-600 mt-1">
                      {(selected_file.size / 1024 / 1024).toFixed(2)} MB
                    </p>
                    <button
                      onClick={() => set_selected_file(null)}
                      className="mt-4 px-4 py-2 text-sm text-red-600 hover:text-red-700"
                    >
                      Remove File
                    </button>
                  </div>
                ) : (
                  <div>
                    <p className="text-gray-600 mb-4">
                      Drag and drop a CSV or JSON file here, or
                    </p>
                    <input
                      type="file"
                      accept=".csv,.json"
                      onChange={(e) =>
                        e.target.files && handle_file_select(e.target.files[0])
                      }
                      className="hidden"
                      id="file-upload"
                    />
                    <label
                      htmlFor="file-upload"
                      className="inline-block px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 cursor-pointer"
                    >
                      Browse Files
                    </label>
                    <p className="text-sm text-gray-500 mt-4">
                      Maximum file size: {MAX_FILE_SIZE_MB} MB
                    </p>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Step 2: Field Mapping */}
          {current_step === "mapping" && analysis_result && (
            <div>
              <h3 className="text-lg font-medium text-gray-900 mb-4">
                Step 2: Field Mapping
              </h3>

              {analysis_result.validation_warnings.length > 0 && (
                <div className="p-4 mb-4 bg-yellow-50 border border-yellow-200 rounded-lg">
                  <h4 className="font-medium text-yellow-900 mb-2">Warnings</h4>
                  <ul className="text-sm text-yellow-700 space-y-1">
                    {analysis_result.validation_warnings.map((warning, index) => (
                      <li key={index}>• {warning}</li>
                    ))}
                  </ul>
                </div>
              )}

              <div className="space-y-3">
                {analysis_result.suggested_mappings.map((suggestion) => (
                  <div
                    key={suggestion.csv_column}
                    className="p-4 border border-gray-200 rounded-lg"
                  >
                    <div className="flex items-center justify-between mb-2">
                      <span className="font-medium text-gray-900">
                        {suggestion.csv_column}
                      </span>
                      {suggestion.suggested_field && (
                        <span
                          className={`px-2 py-1 text-xs font-medium rounded ${get_confidence_color(
                            suggestion.confidence
                          )}`}
                        >
                          {Math.round(suggestion.confidence * 100)}% confidence
                        </span>
                      )}
                    </div>

                    <select
                      value={field_mappings[suggestion.csv_column] || ""}
                      onChange={(e) =>
                        set_field_mappings((prev) => ({
                          ...prev,
                          [suggestion.csv_column]: e.target.value,
                        }))
                      }
                      className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
                    >
                      <option value="">-- Skip this column --</option>
                      {suggestion.suggestions.map((s) => (
                        <option key={s.field} value={s.field}>
                          {s.field} ({Math.round(s.confidence * 100)}% - {s.reason})
                        </option>
                      ))}
                    </select>
                  </div>
                ))}
              </div>

              {analysis_result.unmapped_columns.length > 0 && (
                <div className="mt-4 p-4 bg-gray-50 border border-gray-200 rounded-lg">
                  <h4 className="font-medium text-gray-900 mb-2">
                    Unmapped Columns ({analysis_result.unmapped_columns.length})
                  </h4>
                  <p className="text-sm text-gray-600">
                    The following columns will be stored as custom attributes:
                  </p>
                  <div className="mt-2 flex flex-wrap gap-2">
                    {analysis_result.unmapped_columns.map((col) => (
                      <span
                        key={col}
                        className="px-2 py-1 text-xs bg-gray-200 text-gray-700 rounded"
                      >
                        {col}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Step 3: Configuration */}
          {current_step === "config" && analysis_result && (
            <div>
              <h3 className="text-lg font-medium text-gray-900 mb-4">
                Step 3: Configuration
              </h3>

              <div className="space-y-4">
                <div className="p-4 border border-gray-200 rounded-lg">
                  <h4 className="font-medium text-gray-900 mb-3">
                    Conflict Resolution Strategy
                  </h4>
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={overwrite_existing}
                      onChange={(e) => set_overwrite_existing(e.target.checked)}
                      className="mr-3 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                    />
                    <span className="text-sm text-gray-700">
                      Overwrite existing data (unchecked = fill gaps only)
                    </span>
                  </label>
                </div>

                <div className="p-4 border border-gray-200 rounded-lg">
                  <h4 className="font-medium text-gray-900 mb-3">
                    Gap Analysis Mode
                  </h4>
                  <div className="space-y-2">
                    <label className="flex items-center">
                      <input
                        type="radio"
                        checked={gap_recalculation_mode === "fast"}
                        onChange={() => set_gap_recalculation_mode("fast")}
                        className="mr-3 border-gray-300 text-blue-600 focus:ring-blue-500"
                      />
                      <span className="text-sm text-gray-700">
                        Fast (immediate assets only)
                      </span>
                    </label>
                    <label className="flex items-center">
                      <input
                        type="radio"
                        checked={gap_recalculation_mode === "thorough"}
                        onChange={() => set_gap_recalculation_mode("thorough")}
                        className="mr-3 border-gray-300 text-blue-600 focus:ring-blue-500"
                      />
                      <span className="text-sm text-gray-700">
                        Thorough (includes dependencies, may take longer)
                      </span>
                    </label>
                  </div>
                </div>

                <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
                  <h4 className="font-medium text-blue-900 mb-2">
                    Ready to Import
                  </h4>
                  <ul className="text-sm text-blue-700 space-y-1">
                    <li>• {analysis_result.total_rows} rows will be imported</li>
                    <li>
                      • {Object.keys(field_mappings).filter((k) => field_mappings[k]).length} columns mapped
                    </li>
                    <li>
                      • Strategy: {overwrite_existing ? "Overwrite existing" : "Fill gaps only"}
                    </li>
                    <li>
                      • Gap analysis: {gap_recalculation_mode === "fast" ? "Fast" : "Thorough"}
                    </li>
                  </ul>
                </div>
              </div>
            </div>
          )}

          {/* Step 4: Progress */}
          {current_step === "progress" && task_status && (
            <div>
              <h3 className="text-lg font-medium text-gray-900 mb-4">
                Step 4: Import Progress
              </h3>

              <div className="space-y-4">
                <div className="p-4 border border-gray-200 rounded-lg">
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-medium text-gray-900">
                      {task_status.current_stage}
                    </span>
                    <span className="text-sm text-gray-600">
                      {task_status.progress_percent}%
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-3">
                    <div
                      className="bg-blue-600 h-3 rounded-full transition-all duration-300"
                      style={{ width: `${task_status.progress_percent}%` }}
                    />
                  </div>
                </div>

                {task_status.rows_processed !== undefined && task_status.total_rows && (
                  <div className="text-center text-sm text-gray-600">
                    {task_status.rows_processed} / {task_status.total_rows} rows processed
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Step 5: Results */}
          {current_step === "results" && task_status && (
            <div>
              <h3 className="text-lg font-medium text-gray-900 mb-4">
                Step 5: Results
              </h3>

              {task_status.status === "completed" ? (
                <div className="space-y-4">
                  <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
                    <h4 className="font-medium text-green-900 mb-2">
                      ✓ Import Completed Successfully
                    </h4>
                    <ul className="text-sm text-green-700 space-y-1">
                      <li>• {task_status.rows_processed} rows imported</li>
                      {task_status.result_data && (
                        <>
                          <li>
                            • {task_status.result_data.assets_created || 0} assets created
                          </li>
                          <li>
                            • {task_status.result_data.assets_updated || 0} assets updated
                          </li>
                        </>
                      )}
                    </ul>
                  </div>

                  {task_status.result_data?.gap_analysis && (
                    <div className="p-4 border border-gray-200 rounded-lg">
                      <h4 className="font-medium text-gray-900 mb-2">
                        Gap Analysis Results
                      </h4>
                      <pre className="text-xs text-gray-600 overflow-auto">
                        {JSON.stringify(task_status.result_data.gap_analysis, null, 2)}
                      </pre>
                    </div>
                  )}
                </div>
              ) : (
                <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
                  <h4 className="font-medium text-red-900 mb-2">✗ Import Failed</h4>
                  <p className="text-sm text-red-700">
                    {task_status.error_message || "An unknown error occurred"}
                  </p>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-gray-200 flex justify-between">
          <button
            onClick={() => {
              if (current_step === "mapping") {
                set_current_step("upload");
              } else if (current_step === "config") {
                set_current_step("mapping");
              }
            }}
            disabled={
              current_step === "upload" ||
              current_step === "progress" ||
              current_step === "results"
            }
            className="px-4 py-2 text-gray-700 border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Previous
          </button>

          {current_step === "upload" ? (
            <button
              onClick={handle_analyze}
              disabled={!selected_file || analyze_mutation.isPending}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {analyze_mutation.isPending ? "Analyzing..." : "Analyze File"}
            </button>
          ) : current_step === "mapping" ? (
            <button
              onClick={() => set_current_step("config")}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
            >
              Next
            </button>
          ) : current_step === "config" ? (
            <button
              onClick={handle_execute}
              disabled={execute_mutation.isPending}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {execute_mutation.isPending ? "Starting..." : "Start Import"}
            </button>
          ) : current_step === "results" ? (
            <button
              onClick={on_close}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
            >
              Close
            </button>
          ) : null}
        </div>
      </div>
    </div>
  );
};
