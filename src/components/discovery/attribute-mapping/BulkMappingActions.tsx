import React, { useState } from "react";
import {
  CheckCircle,
  XCircle,
  RotateCcw,
  Download,
  Loader2,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import type { FieldMappingItem } from "@/types/api/discovery/field-mapping-types";
import { useToast } from "@/hooks/use-toast";

/**
 * BulkMappingActions Component
 *
 * Displays mapping statistics and provides bulk operations for field mappings.
 * Part of Issue #1079 - AG Grid Attribute Mapping enhancement.
 *
 * Features:
 * - Statistics display (auto-mapped, needs review, approved, unmapped counts)
 * - Bulk approve all AI-suggested mappings
 * - Bulk reject all mappings with confirmation
 * - Reset mappings to restore AI suggestions with confirmation
 * - Export mappings to CSV
 */

interface BulkMappingActionsProps {
  /** Discovery flow ID for API calls */
  flow_id: string;
  /** All field mappings for statistics calculation and export */
  field_mappings: FieldMappingItem[];
  /** Selected source fields from grid */
  selectedSourceFields: string[];
  /** Callback to approve selected mappings */
  onApproveSelected: () => Promise<void>;
  /** Callback to reject selected mappings */
  onRejectSelected: () => Promise<void>;
  /** Callback to reset mappings to AI suggestions */
  onReset: () => Promise<void>;
  /** Optional callback for custom export logic (falls back to CSV export) */
  onExport?: () => void;
}

interface MappingStatistics {
  auto_mapped: number;
  needs_review: number;
  approved: number;
  unmapped: number;
}

/**
 * Calculate mapping statistics from field mappings array
 */
const calculateStatistics = (
  mappings: FieldMappingItem[],
): MappingStatistics => {
  return mappings.reduce(
    (stats, mapping) => {
      const status = mapping.status.toLowerCase();

      if (status === "suggested") {
        stats.auto_mapped++;
      } else if (status === "approved") {
        stats.approved++;
      } else if (status === "pending") {
        stats.needs_review++;
      } else if (status === "unmapped") {
        stats.unmapped++;
      }

      return stats;
    },
    { auto_mapped: 0, needs_review: 0, approved: 0, unmapped: 0 },
  );
};

/**
 * Export field mappings to CSV file
 * Follows security pattern from src/components/discovery/inventory/utils/exportHelpers.ts
 */
const exportMappingsToCSV = (mappings: FieldMappingItem[]): void => {
  try {
    console.log("🔄 Starting field mappings CSV export...", {
      count: mappings.length,
    });

    if (!mappings || mappings.length === 0) {
      console.warn("⚠️ No mappings to export");
      return;
    }

    // CSV headers
    const headers = [
      "Source Field",
      "Target Field",
      "Status",
      "Confidence Score",
      "Mapping Type",
      "Agent Reasoning",
    ];
    const csvHeaders = headers.join(",");

    // CSV rows with security measures
    const csvRows = mappings.map((mapping) => {
      const confidencePercent =
        mapping.confidence_score !== undefined
          ? `${(mapping.confidence_score * 100).toFixed(0)}%`
          : "N/A";

      const fields = [
        mapping.source_field,
        mapping.target_field,
        mapping.status,
        confidencePercent,
        mapping.field_type || "auto",
        mapping.agent_reasoning || "",
      ];

      return fields
        .map((value) => {
          let stringValue =
            value !== null && value !== undefined ? String(value) : "";

          // Remove newlines/tabs that could break CSV structure
          stringValue = stringValue.replace(/[\r\n\t]/g, " ");

          // Security: Prevent CSV formula injection
          let needsQuoting = false;
          if (stringValue.length > 0 && /^[=+\-@|]/.test(stringValue)) {
            stringValue = `'${stringValue}`;
            needsQuoting = true;
          }

          // Always wrap in quotes if contains special characters
          if (
            needsQuoting ||
            stringValue.includes(",") ||
            stringValue.includes('"')
          ) {
            return `"${stringValue.replace(/"/g, '""')}"`;
          }
          return stringValue;
        })
        .join(",");
    });

    const csvContent = [csvHeaders, ...csvRows].join("\n");
    const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
    const url = window.URL.createObjectURL(blob);

    // Create and trigger download
    const timestamp = new Date().toISOString().split("T")[0];
    const link = document.createElement("a");
    link.setAttribute("href", url);
    link.setAttribute("download", `field-mappings-${timestamp}.csv`);
    link.style.visibility = "hidden";
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);

    // Clean up
    window.URL.revokeObjectURL(url);

    console.log("✅ CSV export completed successfully");
  } catch (error) {
    console.error("❌ Error exporting CSV:", error);
    throw error; // Let parent handle toast notification
  }
};

/**
 * StatDisplay Component - Displays individual statistic with badge
 */
interface StatDisplayProps {
  label: string;
  count: number;
  variant: "default" | "secondary" | "destructive" | "outline";
}

const StatDisplay: React.FC<StatDisplayProps> = ({ label, count, variant }) => {
  // Color-coded circular badges matching EXACT grid colors
  const getCircleStyle = () => {
    switch (variant) {
      case "default": // Auto-Mapped - Blue (suggested mapping)
        return "bg-blue-500 text-white";
      case "secondary": // Needs Review - Yellow (matches grid yellow #fef3c7 border)
        return "bg-yellow-500 text-black";
      case "outline": // Approved - Green (matches grid green #d1fae5)
        return "bg-green-500 text-white";
      case "destructive": // Unmapped - Gray (no mapping)
        return "bg-gray-500 text-white";
      default:
        return "bg-gray-600 text-white";
    }
  };

  return (
    <div className="flex items-center gap-3 px-4 py-2 bg-white rounded-lg border border-gray-300 shadow-sm">
      <span className="text-sm font-semibold text-gray-800 whitespace-nowrap">
        {label}:
      </span>
      <div
        className={`flex items-center justify-center w-8 h-8 rounded-full font-bold text-sm ${getCircleStyle()}`}
      >
        {count}
      </div>
    </div>
  );
};

export const BulkMappingActions: React.FC<BulkMappingActionsProps> = ({
  flow_id,
  field_mappings,
  selectedSourceFields,
  onApproveSelected,
  onRejectSelected,
  onReset,
  onExport,
}) => {
  const { toast } = useToast();
  const [isProcessing, setIsProcessing] = useState(false);
  const [showRejectDialog, setShowRejectDialog] = useState(false);
  const [showResetDialog, setShowResetDialog] = useState(false);

  // Calculate statistics
  const stats = calculateStatistics(field_mappings);

  /**
   * Handle approve selected mappings
   */
  const handleApproveSelected = async (): Promise<void> => {
    if (selectedSourceFields.length === 0) {
      toast({
        title: "No mappings selected",
        description: "Please select one or more columns to approve.",
        variant: "default",
      });
      return;
    }

    setIsProcessing(true);
    try {
      await onApproveSelected();
      toast({
        title: "Success",
        description: `Approved ${selectedSourceFields.length} selected mapping(s).`,
        variant: "default",
      });
    } catch (error) {
      console.error("❌ Error approving mappings:", error);
      toast({
        title: "Error",
        description: "Failed to approve mappings. Please try again.",
        variant: "destructive",
      });
    } finally {
      setIsProcessing(false);
    }
  };

  /**
   * Handle reject selected mappings (with confirmation)
   */
  const handleRejectSelected = async (): Promise<void> => {
    setShowRejectDialog(false);
    setIsProcessing(true);
    try {
      await onRejectSelected();
      toast({
        title: "Success",
        description: `Rejected ${selectedSourceFields.length} selected mapping(s).`,
        variant: "default",
      });
    } catch (error) {
      console.error("❌ Error rejecting mappings:", error);
      toast({
        title: "Error",
        description: "Failed to reject mappings. Please try again.",
        variant: "destructive",
      });
    } finally {
      setIsProcessing(false);
    }
  };

  /**
   * Handle reset mappings (with confirmation)
   */
  const handleReset = async (): Promise<void> => {
    setShowResetDialog(false);
    setIsProcessing(true);
    try {
      await onReset();
      toast({
        title: "Success",
        description: "Mappings have been reset to AI suggestions.",
        variant: "default",
      });
    } catch (error) {
      console.error("❌ Error resetting mappings:", error);
      toast({
        title: "Error",
        description: "Failed to reset mappings. Please try again.",
        variant: "destructive",
      });
    } finally {
      setIsProcessing(false);
    }
  };

  /**
   * Handle export mappings to CSV
   */
  const handleExport = (): void => {
    try {
      if (onExport) {
        // Use custom export logic if provided
        onExport();
      } else {
        // Default to CSV export
        exportMappingsToCSV(field_mappings);
        toast({
          title: "Export Successful",
          description: `Exported ${field_mappings.length} mapping(s) to CSV.`,
          variant: "default",
        });
      }
    } catch (error) {
      console.error("❌ Error exporting mappings:", error);
      toast({
        title: "Export Failed",
        description: "Failed to export mappings. Please try again.",
        variant: "destructive",
      });
    }
  };

  return (
    <>
      <div className="flex items-center justify-between p-6 bg-gradient-to-r from-gray-50 to-white border-b-2 border-gray-200">
        {/* Statistics Section */}
        <div className="flex items-center gap-4">
          <StatDisplay
            label="Auto-Mapped"
            count={stats.auto_mapped}
            variant="default"
          />
          <StatDisplay
            label="Needs Review"
            count={stats.needs_review}
            variant="secondary"
          />
          <StatDisplay
            label="Approved"
            count={stats.approved}
            variant="outline"
          />
          <StatDisplay
            label="Unmapped"
            count={stats.unmapped}
            variant="destructive"
          />
        </div>

        {/* Actions Section */}
        <div className="flex items-center gap-3">
          <Button
            onClick={handleApproveSelected}
            disabled={isProcessing || selectedSourceFields.length === 0}
            className="bg-green-600 hover:bg-green-700 text-white"
            size="sm"
          >
            {isProcessing ? (
              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
            ) : (
              <CheckCircle className="w-4 h-4 mr-2" />
            )}
            Approve Selected
          </Button>

          <Button
            onClick={() => setShowRejectDialog(true)}
            disabled={isProcessing || selectedSourceFields.length === 0}
            className="bg-red-600 hover:bg-red-700 text-white"
            size="sm"
          >
            <XCircle className="w-4 h-4 mr-2" />
            Reject Selected
          </Button>

          <Button
            onClick={() => setShowResetDialog(true)}
            disabled={isProcessing || field_mappings.length === 0}
            variant="ghost"
            size="sm"
          >
            <RotateCcw className="w-4 h-4 mr-2" />
            Reset
          </Button>

          <Button
            onClick={handleExport}
            disabled={field_mappings.length === 0}
            variant="secondary"
            size="sm"
          >
            <Download className="w-4 h-4 mr-2" />
            Export Mappings
          </Button>
        </div>
      </div>

      {/* Reject Selected Confirmation Dialog */}
      <AlertDialog open={showRejectDialog} onOpenChange={setShowRejectDialog}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Reject Selected Mappings?</AlertDialogTitle>
            <AlertDialogDescription>
              This will reject {selectedSourceFields.length} selected field
              mapping(s). You can recreate them later by running the mapping
              process again. This action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleRejectSelected}
              className="bg-red-600 hover:bg-red-700"
            >
              Reject Selected
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Reset Confirmation Dialog */}
      <AlertDialog open={showResetDialog} onOpenChange={setShowResetDialog}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Reset All Mappings?</AlertDialogTitle>
            <AlertDialogDescription>
              This will clear all manual overrides and restore the original
              AI-suggested mappings. Any approved or manually modified mappings
              will be reset to their suggested state. This action cannot be
              undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleReset}
              className="bg-orange-600 hover:bg-orange-700"
            >
              Reset Mappings
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
};
