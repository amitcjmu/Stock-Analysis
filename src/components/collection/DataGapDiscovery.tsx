import React, { useEffect, useState, useCallback, useMemo } from "react";
import { AgGridReact } from "ag-grid-react";
import type {
  ColDef,
  GridReadyEvent,
  CellEditingStoppedEvent,
} from "ag-grid-community";
import { ModuleRegistry, AllCommunityModule } from "ag-grid-community";
// AG Grid CSS imported globally in main.tsx
import {
  Sparkles,
  RefreshCw,
  Save,
  CheckCircle,
  X,
  AlertCircle,
} from "lucide-react";

// Register AG Grid modules
ModuleRegistry.registerModules([AllCommunityModule]);

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useToast } from "@/hooks/use-toast";
import {
  collectionFlowApi,
  type DataGap,
  type GapUpdate,
} from "@/services/api/collection-flow";
import { AssetAPI } from "@/lib/api/assets";

interface DataGapDiscoveryProps {
  flowId: string;
  selectedAssetIds: string[];
  onComplete?: () => void;
}

interface GapRowData extends DataGap {
  id?: string;
  isModified?: boolean;
}

const DataGapDiscovery: React.FC<DataGapDiscoveryProps> = ({
  flowId,
  selectedAssetIds,
  onComplete,
}) => {
  // Add custom tooltip styling
  React.useEffect(() => {
    const style = document.createElement('style');
    style.textContent = `
      .ag-tooltip {
        background-color: #1f2937 !important;
        color: white !important;
        border: 1px solid #374151 !important;
        border-radius: 4px !important;
        padding: 8px 12px !important;
        font-size: 13px !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06) !important;
        max-width: 400px !important;
        word-wrap: break-word !important;
        z-index: 9999 !important;
      }
    `;
    document.head.appendChild(style);
    return () => {
      document.head.removeChild(style);
    };
  }, []);
  const { toast } = useToast();
  const [gaps, setGaps] = useState<GapRowData[]>([]);
  const [isLoadingGaps, setIsLoadingGaps] = useState(true); // Bug #757 Fix: Track initial load state
  const [isScanning, setIsScanning] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [scanSummary, setScanSummary] = useState<{
    total_gaps: number;
    critical_gaps: number;
    execution_time_ms: number;
  } | null>(null);
  const [agenticScanTime, setAgenticScanTime] = useState<number | null>(null);
  const [modifiedGaps, setModifiedGaps] = useState<Set<string>>(new Set());
  const [enhancementProgress, setEnhancementProgress] = useState<{
    job_id: string;
    status: string;
    processed: number;
    total: number;
    current_asset?: string;
    percentage: number;
  } | null>(null);
  const [selectedGaps, setSelectedGaps] = useState<GapRowData[]>([]);
  const [isContinuing, setIsContinuing] = useState(false);
  // AI gap analysis status tracking (Issue #1043)
  const [hasAIAnalysis, setHasAIAnalysis] = useState(false);
  const [showQuestionnaireButton, setShowQuestionnaireButton] = useState(false);
  // Option 3: AI completion detection (Issue #1067)
  const [aiAnalysisProgress, setAiAnalysisProgress] = useState<{
    total: number;
    completed: number;
    percentage: number;
  } | null>(null);

  // Fetch existing gaps on mount, or scan if none exist
  useEffect(() => {
    const loadGaps = async () => {
      try {
        setIsLoadingGaps(true); // Bug #757 Fix: Set loading state
        // First try to fetch existing gaps from database
        const existingGaps = await collectionFlowApi.getGaps(flowId);

        if (existingGaps && existingGaps.length > 0) {
          // Backend always returns database UUIDs - no transformation needed
          setGaps(existingGaps);

          // Try to retrieve scan summary from collection flow's gap_analysis_results
          try {
            const flowDetails = await collectionFlowApi.getFlow(flowId);
            const gapAnalysisResults = flowDetails.gap_analysis_results;

            if (gapAnalysisResults && gapAnalysisResults.summary) {
              // Use persisted scan summary if available
              setScanSummary({
                total_gaps: gapAnalysisResults.summary.total_gaps || existingGaps.length,
                critical_gaps: gapAnalysisResults.summary.critical_gaps || existingGaps.filter(g => g.priority === 1).length,
                execution_time_ms: gapAnalysisResults.summary.execution_time_ms || 0,
              });
            } else {
              // Fallback: Generate summary from existing gaps
              const criticalCount = existingGaps.filter(g => g.priority === 1).length;
              setScanSummary({
                total_gaps: existingGaps.length,
                critical_gaps: criticalCount,
                execution_time_ms: 0, // Not available
              });
            }
          } catch (flowError) {
            console.error("Failed to load flow details:", flowError);
            // Fallback: Generate summary from existing gaps
            const criticalCount = existingGaps.filter(g => g.priority === 1).length;
            setScanSummary({
              total_gaps: existingGaps.length,
              critical_gaps: criticalCount,
              execution_time_ms: 0, // Not available
            });
          }
        } else if (selectedAssetIds.length > 0) {
          // No existing gaps, trigger a scan if assets are selected
          handleScanGaps();
        }
      } catch (error) {
        console.error("Failed to load gaps:", error);
        // If fetching fails and we have assets, try scanning
        if (selectedAssetIds.length > 0) {
          handleScanGaps();
        }
      } finally {
        setIsLoadingGaps(false); // Bug #757 Fix: Clear loading state
      }
    };

    loadGaps();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [flowId, selectedAssetIds]);

  // Check if selected assets have AI analysis completed (status = 2)
  useEffect(() => {
    const checkAIStatus = async () => {
      if (selectedAssetIds.length === 0) {
        setHasAIAnalysis(false);
        return;
      }

      try {
        // Fetch assets to check ai_gap_analysis_status
        const assetPromises = selectedAssetIds.map(id => AssetAPI.getAsset(id));
        const assets = await Promise.all(assetPromises);

        // Check if all selected assets have completed AI analysis (status = 2)
        const allCompleted = assets.every(asset => asset.ai_gap_analysis_status === 2);
        setHasAIAnalysis(allCompleted);

        console.log(`📊 AI analysis status check - ${allCompleted ? 'All assets analyzed' : 'Some assets need analysis'}`);
      } catch (error) {
        console.error('Failed to check AI analysis status:', error);
        setHasAIAnalysis(false);
      }
    };

    checkAIStatus();
  }, [selectedAssetIds]);

  const handleScanGaps = async () => {
    try {
      setIsScanning(true);
      const response = await collectionFlowApi.scanGaps(
        flowId,
        selectedAssetIds,
      );

      // Backend now returns gaps with database UUIDs - no synthetic keys needed
      setGaps(response.gaps);
      setScanSummary(response.summary);

      // CRITICAL FIX: Refetch gaps from database to ensure component state is synchronized
      // This prevents race condition where user clicks "Accept Selected" before state updates
      try {
        const dbGaps = await collectionFlowApi.getGaps(flowId);
        setGaps(dbGaps);
        console.log(`✅ Refetched ${dbGaps.length} gaps from database after scan (race condition fix)`);
      } catch (refetchError) {
        console.error("Failed to refetch gaps after scan:", refetchError);
        // Don't fail the whole operation, just log the error
      }

      toast({
        title: "Gap Scan Complete",
        description: `Found ${response.summary.total_gaps} gaps across ${response.summary.assets_analyzed} assets (${response.summary.execution_time_ms}ms)`,
        variant: "default",
      });
    } catch (error: unknown) {
      const errorMessage =
        error instanceof Error ? error.message : "Failed to scan gaps";
      toast({
        title: "Scan Failed",
        description: errorMessage,
        variant: "destructive",
      });
    } finally {
      setIsScanning(false);
    }
  };

  const handleAnalyzeGaps = async () => {
    // Use selected gaps if available, otherwise all gaps
    const gapsToAnalyze = selectedGaps.length > 0 ? selectedGaps : gaps;

    if (gapsToAnalyze.length === 0) {
      toast({
        title: "No Gaps to Analyze",
        description: selectedGaps.length > 0 ? "Please select gaps to analyze" : "Run a gap scan first",
        variant: "destructive",
      });
      return;
    }

    // Check for >200 gaps limit
    if (gapsToAnalyze.length > 200) {
      toast({
        title: "Too Many Gaps",
        description: `Please select fewer gaps (${gapsToAnalyze.length}/200 max). Use row selection to choose specific gaps.`,
        variant: "destructive",
      });
      return;
    }

    try {
      setIsAnalyzing(true);

      // Start enhancement job (returns 202 Accepted immediately)
      const response = await collectionFlowApi.analyzeGaps(
        flowId,
        gapsToAnalyze,
        selectedAssetIds,
      );

      toast({
        title: "Enhancement Started",
        description: response.message,
        variant: "default",
      });

      // Start polling for progress
      let attempts = 0;
      const maxAttempts = 24; // 12 minutes max (30s interval)

      const pollProgress = setInterval(async () => {
        try {
          const progress = await collectionFlowApi.getEnhancementProgress(flowId);

          setEnhancementProgress({
            job_id: response.job_id,
            status: progress.status,
            processed: progress.processed,
            total: progress.total,
            current_asset: progress.current_asset,
            percentage: progress.percentage,
          });

          if (progress.status === "completed") {
            clearInterval(pollProgress);

            // Calculate agentic scan time if we have job timestamps
            if (progress.updated_at && enhancementProgress) {
              const startTime = new Date(enhancementProgress.job_id.split('_')[2] * 1000); // Extract timestamp from job ID
              const endTime = new Date(progress.updated_at);
              const durationMs = endTime.getTime() - startTime.getTime();
              setAgenticScanTime(Math.round(durationMs));
            }

            // Re-scan gaps to get AI enhancements from database
            try {
              const updatedGaps = await collectionFlowApi.getGaps(flowId);
              // Backend always returns database UUIDs - no transformation needed
              setGaps(updatedGaps);

              toast({
                title: "Enhancement Complete",
                description: `Enhanced ${progress.processed} assets successfully`,
                variant: "default",
              });
            } catch (fetchError) {
              console.error("Failed to fetch enhanced gaps:", fetchError);
            }

            setIsAnalyzing(false);
            setEnhancementProgress(null);
          } else if (progress.status === "failed") {
            clearInterval(pollProgress);
            // Bug #892 Fix: Display specific error message from backend
            const errorDescription = progress.user_message ||
              progress.error ||
              "AI enhancement encountered an error. Please try again.";
            toast({
              title: "Enhancement Failed",
              description: errorDescription,
              variant: "destructive",
            });
            setIsAnalyzing(false);
            setEnhancementProgress(null);
          }

          attempts++;
          if (attempts >= maxAttempts) {
            clearInterval(pollProgress);
            toast({
              title: "Enhancement Timeout",
              description: "Enhancement is taking longer than 12 minutes. Check flow status or backend logs.",
              variant: "destructive",
            });
            setIsAnalyzing(false);
            setEnhancementProgress(null);
          }
        } catch (error) {
          console.error("Progress polling error:", error);
        }
      }, 30000); // Poll every 30 seconds

    } catch (error: unknown) {
      // Bug #892 Fix: Provide more actionable error messages
      let errorMessage = "Failed to start enhancement. Please try again.";
      if (error && typeof error === 'object') {
        const status = (error as { response?: { status?: number } }).response?.status;
        if (status === 409) {
          errorMessage = "An enhancement job is already running. Please wait for it to complete.";
        } else if (status === 429) {
          errorMessage = "Rate limit reached. Please wait a few seconds before retrying.";
        } else if (error instanceof Error) {
          if (error.message.toLowerCase().includes("timeout")) {
            errorMessage = "Request timed out. Please check your connection and try again.";
          } else {
            errorMessage = error.message;
          }
        }
      }
      toast({
        title: "Enhancement Failed",
        description: errorMessage,
        variant: "destructive",
      });
      setIsAnalyzing(false);
      setEnhancementProgress(null);
    }
  };

  // ✅ Auto-trigger handler (non-blocking)
  const handleAnalyzeGapsAuto = useCallback(async () => {
    try {
      setIsAnalyzing(true);

      console.log('📤 Auto-triggering analyze-gaps with null gaps (comprehensive analysis mode)');

      // Call existing endpoint with null gaps
      // Backend will perform comprehensive AI analysis on assets
      // force_refresh = false to skip assets with ai_gap_analysis_status = 2
      const response = await collectionFlowApi.analyzeGaps(
        flowId,
        null, // null - triggers comprehensive analysis in backend
        selectedAssetIds,
        false // force_refresh = false (skip completed assets)
      );

      console.log('✅ AI enhancement job queued:', response.job_id);

      // Start polling for progress (same pattern as handleAnalyzeGaps)
      let attempts = 0;
      const maxAttempts = 24; // 12 minutes max (30s interval)

      const pollProgress = setInterval(async () => {
        try {
          const progress = await collectionFlowApi.getEnhancementProgress(flowId);

          setEnhancementProgress({
            job_id: response.job_id,
            status: progress.status,
            processed: progress.processed,
            total: progress.total,
            current_asset: progress.current_asset,
            percentage: progress.percentage,
          });

          if (progress.status === "completed") {
            clearInterval(pollProgress);

            // Re-fetch gaps to get AI enhancements from database
            try {
              const updatedGaps = await collectionFlowApi.getGaps(flowId);
              setGaps(updatedGaps);

              toast({
                title: "Auto-Enhancement Complete",
                description: `Enhanced ${progress.processed} assets successfully`,
                variant: "default",
              });
            } catch (fetchError) {
              console.error("Failed to fetch enhanced gaps:", fetchError);
            }

            setIsAnalyzing(false);
            setEnhancementProgress(null);
          } else if (progress.status === "failed") {
            clearInterval(pollProgress);
            const errorDescription = progress.user_message ||
              progress.error ||
              "AI enhancement encountered an error. You can manually trigger it again.";
            toast({
              title: "Auto-Enhancement Failed",
              description: errorDescription,
              variant: "destructive",
            });
            setIsAnalyzing(false);
            setEnhancementProgress(null);
          }

          attempts++;
          if (attempts >= maxAttempts) {
            clearInterval(pollProgress);
            toast({
              title: "Enhancement Timeout",
              description: "Enhancement is taking longer than expected. You can manually trigger it again.",
              variant: "destructive",
            });
            setIsAnalyzing(false);
            setEnhancementProgress(null);
          }
        } catch (error) {
          console.error("Progress polling error:", error);
        }
      }, 30000); // Poll every 30 seconds

    } catch (error: unknown) {
      console.error('Failed to auto-trigger AI analysis:', error);

      // Non-blocking error - user can still manually trigger via "Analyze with AI" button
      if (error instanceof Error && error.message.includes('already running')) {
        // Job already exists - existing polling will pick it up
        console.log('Job already running - existing polling will track progress');
      } else {
        toast({
          title: "Background Analysis",
          description: "AI enhancement could not auto-start. You can manually trigger it using the button.",
          variant: "default"
        });
      }
      setIsAnalyzing(false);
    }
  }, [flowId, selectedAssetIds, toast]);

  // Force re-analysis handler (for manual re-triggering)
  const handleForceReAnalysis = async () => {
    try {
      setIsAnalyzing(true);

      console.log('🔄 Force re-analysis triggered by user');

      const response = await collectionFlowApi.analyzeGaps(
        flowId,
        null,
        selectedAssetIds,
        true // force_refresh = true (re-analyze all assets)
      );

      console.log('✅ Force re-analysis job queued:', response.job_id);

      toast({
        title: "Re-Analysis Started",
        description: "All assets will be re-analyzed with AI. This may take a few minutes.",
        variant: "default",
      });

      // Start polling for progress (same pattern as auto-trigger)
      let attempts = 0;
      const maxAttempts = 24; // 12 minutes max (30s interval)

      const pollProgress = setInterval(async () => {
        try {
          const progress = await collectionFlowApi.getEnhancementProgress(flowId);

          setEnhancementProgress({
            job_id: response.job_id,
            status: progress.status,
            processed: progress.processed,
            total: progress.total,
            current_asset: progress.current_asset,
            percentage: progress.percentage,
          });

          if (progress.status === "completed") {
            clearInterval(pollProgress);

            // Re-fetch gaps to get updated AI enhancements
            try {
              const updatedGaps = await collectionFlowApi.getGaps(flowId);
              setGaps(updatedGaps);

              // Update AI analysis status
              setHasAIAnalysis(true);

              toast({
                title: "Re-Analysis Complete",
                description: `Re-analyzed ${progress.processed} assets successfully`,
                variant: "default",
              });
            } catch (fetchError) {
              console.error("Failed to fetch enhanced gaps:", fetchError);
            }

            setIsAnalyzing(false);
            setEnhancementProgress(null);
          } else if (progress.status === "failed") {
            clearInterval(pollProgress);
            const errorDescription = progress.user_message ||
              progress.error ||
              "Re-analysis failed. Please try again.";
            toast({
              title: "Re-Analysis Failed",
              description: errorDescription,
              variant: "destructive",
            });
            setIsAnalyzing(false);
            setEnhancementProgress(null);
          }

          attempts++;
          if (attempts >= maxAttempts) {
            clearInterval(pollProgress);
            toast({
              title: "Re-Analysis Timeout",
              description: "Re-analysis is taking longer than expected.",
              variant: "destructive",
            });
            setIsAnalyzing(false);
            setEnhancementProgress(null);
          }
        } catch (error) {
          console.error("Progress polling error:", error);
        }
      }, 30000); // Poll every 30 seconds

    } catch (error: unknown) {
      console.error('Failed to force re-analysis:', error);

      const errorMessage =
        error instanceof Error ? error.message : "Failed to start re-analysis. Please try again.";
      toast({
        title: "Re-Analysis Failed",
        description: errorMessage,
        variant: "destructive",
      });
      setIsAnalyzing(false);
    }
  };

  // ✅ Auto-trigger AI-enhanced gap analysis after heuristic scan completes
  useEffect(() => {
    // Only auto-trigger if:
    // 1. Heuristic gaps exist (scan completed)
    // 2. Not already analyzing
    // 3. No enhancement progress (not already running)
    // 4. Scan summary exists (scan just completed)
    if (
      gaps.length > 0 &&
      !isAnalyzing &&
      !enhancementProgress &&
      scanSummary
    ) {
      // Check if gaps already have AI enhancements (confidence_score is populated by AI)
      const hasAIEnhancements = gaps.some(gap =>
        gap.confidence_score !== null && gap.confidence_score !== undefined
      );

      if (!hasAIEnhancements) {
        console.log('🚀 Auto-triggering AI-enhanced gap analysis');
        handleAnalyzeGapsAuto();
      } else {
        console.log('✅ Gaps already have AI enhancements - skipping auto-trigger');
      }
    }
  }, [gaps, scanSummary, isAnalyzing, enhancementProgress, handleAnalyzeGapsAuto]);

  // Delay showing questionnaire button for 20 seconds to encourage gap review
  useEffect(() => {
    if (gaps.length > 0 && !showQuestionnaireButton) {
      const timer = setTimeout(() => {
        setShowQuestionnaireButton(true);
      }, 20000); // 20 seconds delay

      return () => clearTimeout(timer);
    }
  }, [gaps, showQuestionnaireButton]);

  // Option 3: Poll AI analysis status after button appears (Issue #1067)
  useEffect(() => {
    if (!showQuestionnaireButton || !flowId) return;

    const pollAIStatus = async () => {
      try {
        // Get assets with gaps to check their AI analysis status
        const response = await AssetAPI.getAssets({ page: 1, page_size: 100 });
        const assetsWithGaps = new Set(gaps.map(g => g.asset_id).filter(Boolean));
        const relevantAssets = response.assets.filter(a => assetsWithGaps.has(a.id));

        if (relevantAssets.length === 0) {
          // No assets with gaps - enable button immediately
          setAiAnalysisProgress({ total: 0, completed: 0, percentage: 100 });
          return;
        }

        // Count assets that completed AI analysis (status = 2)
        const completedCount = relevantAssets.filter(a => a.ai_gap_analysis_status === 2).length;
        const percentage = Math.round((completedCount / relevantAssets.length) * 100);

        setAiAnalysisProgress({
          total: relevantAssets.length,
          completed: completedCount,
          percentage
        });

        console.log(`🤖 AI Analysis Progress: ${completedCount}/${relevantAssets.length} assets (${percentage}%)`);
      } catch (error) {
        console.error('Failed to poll AI analysis status:', error);
        // On error, assume analysis is complete to not block user
        setAiAnalysisProgress({ total: 0, completed: 0, percentage: 100 });
      }
    };

    // Poll immediately
    pollAIStatus();

    // Then poll every 5 seconds until 100%
    const interval = setInterval(() => {
      if (aiAnalysisProgress?.percentage === 100) {
        clearInterval(interval);
      } else {
        pollAIStatus();
      }
    }, 5000);

    return () => clearInterval(interval);
  }, [showQuestionnaireButton, flowId, gaps, aiAnalysisProgress?.percentage]);

  const handleCellEditingStopped = useCallback(
    (event: CellEditingStoppedEvent<GapRowData>) => {
      if (event.oldValue !== event.newValue) {
        const gapId = event.data?.id;
        if (gapId) {
          setModifiedGaps((prev) => new Set(prev).add(gapId));

          // Mark row as modified
          setGaps((prevGaps) =>
            prevGaps.map((gap) =>
              gap.id === gapId ? { ...gap, isModified: true } : gap,
            ),
          );
        }
      }
    },
    [],
  );

  const handleSaveGap = useCallback(
    async (gap: GapRowData) => {
      if (!gap.id || !gap.current_value) return;

      try {
        setIsSaving(true);

        const update: GapUpdate = {
          gap_id: gap.id,
          field_name: gap.field_name,
          resolved_value: String(gap.current_value),
          resolution_status: "resolved",
          resolution_method: "manual_entry",
        };

        await collectionFlowApi.updateGaps(flowId, [update]);

        // Remove from modified set
        setModifiedGaps((prev) => {
          const newSet = new Set(prev);
          newSet.delete(gap.id);
          return newSet;
        });

        // Update gap status
        setGaps((prevGaps) =>
          prevGaps.map((g) =>
            g.id === gap.id ? { ...g, isModified: false } : g,
          ),
        );

        toast({
          title: "Gap Saved",
          description: `Saved resolution for ${gap.field_name}`,
          variant: "default",
        });
      } catch (error: unknown) {
        const errorMessage =
          error instanceof Error ? error.message : "Failed to save gap";
        toast({
          title: "Save Failed",
          description: errorMessage,
          variant: "destructive",
        });
      } finally {
        setIsSaving(false);
      }
    },
    [flowId, toast],
  );

  const handleBulkAccept = async () => {
    // Accept all AI suggestions with high confidence
    const highConfidenceGaps = gaps.filter(
      (gap) => gap.confidence_score !== null && gap.confidence_score >= 0.8,
    );

    if (highConfidenceGaps.length === 0) {
      toast({
        title: "No High Confidence Suggestions",
        description: "Run AI analysis first or lower confidence threshold",
        variant: "destructive",
      });
      return;
    }

    try {
      setIsSaving(true);

      const updates: GapUpdate[] = highConfidenceGaps.map((gap) => {
        if (!gap.id) {
          throw new Error(`Gap ID missing for ${gap.field_name}`);
        }

        return {
          gap_id: gap.id,  // Backend always returns database UUID
          field_name: gap.field_name,
          resolved_value: gap.suggested_resolution,
          resolution_status: "resolved",
          resolution_method: "ai_suggestion",
        };
      });

      const response = await collectionFlowApi.updateGaps(flowId, updates);

      toast({
        title: "Bulk Accept Complete",
        description: `Accepted ${response.gaps_resolved} high-confidence suggestions`,
        variant: "default",
      });

      // Fetch remaining unresolved gaps (don't re-scan, which would recreate them!)
      const updatedGaps = await collectionFlowApi.getGaps(flowId);
      setGaps(updatedGaps);
    } catch (error: unknown) {
      const errorMessage =
        error instanceof Error ? error.message : "Failed to bulk accept";
      toast({
        title: "Bulk Accept Failed",
        description: errorMessage,
        variant: "destructive",
      });
    } finally {
      setIsSaving(false);
    }
  };

  // Accept only the selected gaps from AG Grid row selection
  const handleAcceptSelected = async () => {
    if (selectedGaps.length === 0) {
      toast({
        title: "No Gaps Selected",
        description: "Please select gaps from the table to accept",
        variant: "destructive",
      });
      return;
    }

    // Validate that selected gaps have suggested resolutions
    const gapsWithResolutions = selectedGaps.filter(
      (gap) => gap.suggested_resolution && gap.suggested_resolution.trim() !== ''
    );

    if (gapsWithResolutions.length === 0) {
      toast({
        title: "No Resolutions Available",
        description: "Selected gaps need AI suggestions before accepting. Run AI analysis first.",
        variant: "destructive",
      });
      return;
    }

    if (gapsWithResolutions.length < selectedGaps.length) {
      toast({
        title: "Some Gaps Missing Resolutions",
        description: `${selectedGaps.length - gapsWithResolutions.length} selected gap(s) don't have AI suggestions. Only accepting ${gapsWithResolutions.length} gap(s).`,
        variant: "default",
      });
    }

    try {
      setIsSaving(true);

      // Debug: Log current state
      console.log('🔍 Accept Selected Debug:', {
        selectedGapsCount: selectedGaps.length,
        gapsArrayCount: gaps.length,
        gapsWithResolutionsCount: gapsWithResolutions.length,
        sampleSelectedGap: selectedGaps[0],
        sampleGapFromArray: gaps[0],
      });

      // CRITICAL FIX: Look up full gap data from gaps state to get database IDs
      // AG Grid selection may not preserve all fields, so we use asset_id + field_name as key
      const updates: GapUpdate[] = [];
      const missingGaps: string[] = [];

      for (const selectedGap of gapsWithResolutions) {
        // Find the full gap object in the gaps array using composite key
        const fullGap = gaps.find(
          (g) => g.asset_id === selectedGap.asset_id && g.field_name === selectedGap.field_name
        );

        if (!fullGap || !fullGap.id) {
          console.warn(
            `Gap not found in state: ${selectedGap.field_name} (asset: ${selectedGap.asset_id})`
          );
          missingGaps.push(selectedGap.field_name);
          continue; // Skip this gap instead of throwing
        }

        updates.push({
          gap_id: fullGap.id,  // Use ID from gaps state
          field_name: selectedGap.field_name,
          resolved_value: selectedGap.suggested_resolution,
          resolution_status: "resolved",
          resolution_method: "ai_suggestion",
        });
      }

      if (updates.length === 0) {
        toast({
          title: "No Gaps Could Be Processed",
          description: `Could not find gap IDs for selected gaps. Try refreshing the page.`,
          variant: "destructive",
        });
        return;
      }

      if (missingGaps.length > 0) {
        console.warn(
          `Skipping ${missingGaps.length} gaps that could not be found: ${missingGaps.join(", ")}`
        );
        toast({
          title: "Some Gaps Skipped",
          description: `Processing ${updates.length} of ${gapsWithResolutions.length} gaps (${missingGaps.length} skipped due to missing data)`,
          variant: "default",
        });
      }

      // Debug log to see what we're sending
      console.log('📤 Sending gap updates:', JSON.stringify(updates, null, 2));

      const response = await collectionFlowApi.updateGaps(flowId, updates);

      toast({
        title: "Accept Selected Complete",
        description: `Accepted ${response.gaps_resolved} selected gap(s)`,
        variant: "default",
      });

      // Clear selection after successful acceptance
      setSelectedGaps([]);

      // Fetch remaining unresolved gaps (don't re-scan, which would recreate them!)
      const updatedGaps = await collectionFlowApi.getGaps(flowId);
      setGaps(updatedGaps);
    } catch (error: unknown) {
      const errorMessage =
        error instanceof Error ? error.message : "Failed to accept selected gaps";
      toast({
        title: "Accept Selected Failed",
        description: errorMessage,
        variant: "destructive",
      });
    } finally {
      setIsSaving(false);
    }
  };

  const handleBulkReject = async () => {
    // Reject all AI suggestions (mark as skipped)
    const aiSuggestedGaps = gaps.filter((gap) => gap.confidence_score !== null);

    if (aiSuggestedGaps.length === 0) {
      toast({
        title: "No AI Suggestions",
        description: "Run AI analysis first",
        variant: "destructive",
      });
      return;
    }

    try {
      setIsSaving(true);

      const updates: GapUpdate[] = aiSuggestedGaps.map((gap) => {
        if (!gap.id) {
          throw new Error(`Gap ID missing for ${gap.field_name}`);
        }

        return {
          gap_id: gap.id,  // Backend always returns database UUID
          field_name: gap.field_name,
          resolved_value: "",
          resolution_status: "skipped",
          resolution_method: "manual_entry",
        };
      });

      await collectionFlowApi.updateGaps(flowId, updates);

      toast({
        title: "Bulk Reject Complete",
        description: `Rejected ${aiSuggestedGaps.length} AI suggestions`,
        variant: "default",
      });

      // Clear AI suggestions from UI
      setGaps((prevGaps) =>
        prevGaps.map((gap) => ({
          ...gap,
          confidence_score: null,
          ai_suggestions: undefined,
        })),
      );
    } catch (error: unknown) {
      const errorMessage =
        error instanceof Error ? error.message : "Failed to bulk reject";
      toast({
        title: "Bulk Reject Failed",
        description: errorMessage,
        variant: "destructive",
      });
    } finally {
      setIsSaving(false);
    }
  };

  // Confidence score color renderer
  const confidenceRenderer = (params: { value: number | null }) => {
    if (params.value === null || params.value === undefined) {
      return <span className="text-gray-400">No AI</span>;
    }

    const percentage = Math.round(params.value * 100);
    let colorClass = "text-red-600";
    if (params.value >= 0.8) colorClass = "text-green-600";
    else if (params.value >= 0.6) colorClass = "text-yellow-600";

    return <span className={`${colorClass} font-semibold`}>{percentage}%</span>;
  };

  // Save button renderer - wrapped in useCallback for performance
  const actionRenderer = useCallback(
    (params: { data: GapRowData }) => {
      const gap = params.data;
      const isModified = gap.isModified || modifiedGaps.has(gap.id || "");

      if (!isModified) {
        return <span className="text-gray-400">-</span>;
      }

      return (
        <button
          className="save-btn px-2 py-1 bg-blue-600 text-white rounded hover:bg-blue-700 text-sm"
          data-gap-id={gap.id}
          onClick={(e) => {
            e.stopPropagation();
            handleSaveGap(gap);
          }}
        >
          Save
        </button>
      );
    },
    [modifiedGaps, handleSaveGap],
  );

  const columnDefs = useMemo<Array<ColDef<GapRowData>>>(
    () => [
      {
        width: 50,
        pinned: "left",
        lockPosition: "left",
        suppressMovable: true,
      },
      {
        field: "asset_name",
        headerName: "Asset",
        width: 150,
        pinned: "left",
      },
      {
        field: "field_name",
        headerName: "Field",
        width: 180,
      },
      {
        field: "gap_category",
        headerName: "Category",
        width: 130,
      },
      {
        field: "priority",
        headerName: "Priority",
        width: 100,
        cellRenderer: (params: { value: number }) => {
          const badges = {
            1: (
              <span className="px-2 py-1 bg-red-100 text-red-800 rounded text-xs font-medium">
                Critical
              </span>
            ),
            2: (
              <span className="px-2 py-1 bg-orange-100 text-orange-800 rounded text-xs font-medium">
                High
              </span>
            ),
            3: (
              <span className="px-2 py-1 bg-yellow-100 text-yellow-800 rounded text-xs font-medium">
                Medium
              </span>
            ),
            4: (
              <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded text-xs font-medium">
                Low
              </span>
            ),
          };
          return badges[params.value as 1 | 2 | 3 | 4] || badges[4];
        },
      },
      {
        field: "current_value",
        headerName: "Current Value",
        width: 200,
        editable: true,
        cellEditor: "agTextCellEditor",
      },
      {
        field: "suggested_resolution",
        headerName: "Suggested Resolution",
        width: 250,
      },
      {
        field: "confidence_score",
        headerName: "AI Confidence",
        width: 130,
        cellRenderer: confidenceRenderer,
      },
      {
        headerName: "Actions",
        width: 100,
        cellRenderer: actionRenderer,
        pinned: "right",
      },
    ],
    [actionRenderer],
  );

  const onGridReady = useCallback(
    (params: GridReadyEvent) => {
      // Add click handler for save buttons
      params.api.getRenderedNodes().forEach((node) => {
        const eGui = node.eGridCell?.querySelector(".save-btn");
        if (eGui) {
          eGui.addEventListener("click", (event) => {
            event.stopPropagation();
            const gapId = (event.target as HTMLElement).getAttribute(
              "data-gap-id",
            );
            const gap = gaps.find((g) => g.id === gapId);
            if (gap) {
              handleSaveGap(gap);
            }
          });
        }
      });
    },
    [gaps, handleSaveGap],
  );

  const onSelectionChanged = useCallback((event: unknown) => {
    const selectedRows = (event as { api: { getSelectedRows: () => GapRowData[] } }).api.getSelectedRows();
    setSelectedGaps(selectedRows);
  }, []);

  const handleContinueToQuestionnaire = async () => {
    if (!onComplete) return;

    try {
      setIsContinuing(true);
      await onComplete();
    } catch (error) {
      console.error('Failed to continue to questionnaire:', error);
      toast({
        title: "Navigation Failed",
        description: "Failed to proceed to questionnaire. Please try again.",
        variant: "destructive",
      });
      // Re-throw the error so parent components can handle it if needed
      throw error;
    } finally {
      setIsContinuing(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Gap Analysis Status Message */}
      {scanSummary && (
        <div className="mb-4 p-4 bg-blue-50 rounded-lg border border-blue-200">
          {hasAIAnalysis ? (
            <p className="text-green-700 font-medium">
              ✅ AI-enhanced gap analysis is complete.
              Review gaps below and accept/reject AI classifications.
            </p>
          ) : (
            <p className="text-blue-700 font-medium">
              📊 Heuristic gap analysis is complete.
              AI enhancement {isAnalyzing ? 'is running' : 'will run automatically'}.
            </p>
          )}
        </div>
      )}

      {/* Summary Card */}
      {scanSummary && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <AlertCircle className="w-5 h-5 text-orange-600 mr-2" />
              Gap Analysis Summary
            </CardTitle>
            <CardDescription>
              {agenticScanTime
                ? `Heuristic + AI analysis complete across ${gaps.length} final gaps`
                : `Fast programmatic scan across ${scanSummary.total_gaps} gaps`}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-5 gap-4">
              {/* Single row with all metrics */}
              <div>
                <div className="text-sm text-gray-600">Assets</div>
                <div className="text-2xl font-bold">
                  {selectedAssetIds.length}
                </div>
                <div className="text-xs text-gray-500 mt-1">Analyzed</div>
              </div>
              <div>
                <div className="text-sm text-gray-600">Initial Gaps</div>
                <div className="text-2xl font-bold">
                  {scanSummary.total_gaps}
                </div>
                <div className="text-xs text-gray-500 mt-1">Heuristic scan</div>
              </div>
              <div>
                <div className="text-sm text-gray-600">Agentic Gaps</div>
                <div className="text-2xl font-bold text-purple-600">
                  {gaps.length}
                </div>
                <div className="text-xs text-gray-500 mt-1">After AI analysis</div>
              </div>
              <div>
                <div className="text-sm text-gray-600">Critical Gaps</div>
                <div className="text-2xl font-bold text-red-600">
                  {scanSummary.critical_gaps}
                </div>
                <div className="text-xs text-gray-500 mt-1">Heuristic priority</div>
              </div>
              <div>
                <div className="text-sm text-gray-600">
                  {agenticScanTime ? 'Agentic Scan Time' : 'Scan Time'}
                </div>
                <div className="text-2xl font-bold text-purple-600">
                  {agenticScanTime ? (
                    agenticScanTime < 1000
                      ? `${agenticScanTime}ms`
                      : `${(agenticScanTime / 1000).toFixed(1)}s`
                  ) : (
                    scanSummary.execution_time_ms > 0 ? `${scanSummary.execution_time_ms}ms` : 'N/A'
                  )}
                </div>
                <div className="text-xs text-gray-500 mt-1">
                  {agenticScanTime ? 'AI analysis' : 'Heuristic'}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Action Buttons */}
      <Card>
        <CardHeader>
          <CardTitle>Gap Resolution Actions</CardTitle>
          <CardDescription>
            Scan for gaps, enhance with AI, or manually resolve
            {selectedGaps.length > 0 && (
              <span className="ml-2 text-purple-600 font-medium">
                ({selectedGaps.length} gap{selectedGaps.length !== 1 ? 's' : ''} selected for AI analysis)
              </span>
            )}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {/* Row 1: Scan and Analysis Actions */}
            <div className="flex items-center gap-3 flex-wrap">
              <Button
                onClick={handleScanGaps}
                disabled={isScanning || selectedAssetIds.length === 0}
                variant="outline"
              >
                {isScanning ? (
                  <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                ) : (
                  <RefreshCw className="w-4 h-4 mr-2" />
                )}
                {isScanning ? "Scanning..." : "Re-scan Gaps"}
              </Button>

              <Button
                onClick={handleAnalyzeGaps}
                disabled={isAnalyzing || gaps.length === 0}
                className="bg-purple-600 hover:bg-purple-700"
              >
                {isAnalyzing ? (
                  <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                ) : (
                  <Sparkles className="w-4 h-4 mr-2" />
                )}
                {isAnalyzing ? "Analyzing..." : "Agentic Gap Resolution Analysis"}
              </Button>

              {/* Force Re-Analysis Button - Only show when AI analysis completed */}
              {hasAIAnalysis && (
                <Button
                  onClick={handleForceReAnalysis}
                  disabled={isAnalyzing}
                  variant="outline"
                  className="text-yellow-600 hover:bg-yellow-50"
                >
                  <RefreshCw className="w-4 h-4 mr-2" />
                  Force Re-Analysis
                </Button>
              )}

              {/* Progress Display for Non-Blocking AI Enhancement */}
              {enhancementProgress && (
                <div className="flex items-center gap-2 px-3 py-1 bg-purple-50 border border-purple-200 rounded-md text-sm text-purple-700">
                  <RefreshCw className="w-3 h-3 animate-spin" />
                  <span>
                    Processing: {enhancementProgress.processed}/{enhancementProgress.total} assets
                    {enhancementProgress.current_asset && ` - ${enhancementProgress.current_asset}`}
                    ({Math.round((enhancementProgress.processed / enhancementProgress.total) * 100)}%)
                  </span>
                </div>
              )}
            </div>

            {/* Row 2: Accept/Reject Actions - Only show when AI analysis completed */}
            {hasAIAnalysis && (
              <div className="flex items-center gap-3 flex-wrap pt-2 border-t border-gray-200">
                <div className="text-sm text-gray-600 font-medium mr-2">
                  AI Recommendations:
                </div>

                {/* Accept Selected Button - Only show when gaps are selected */}
                {selectedGaps.length > 0 && (
                  <Button
                    onClick={handleAcceptSelected}
                    disabled={isSaving}
                    className="bg-green-600 hover:bg-green-700 text-white"
                  >
                    <CheckCircle className="w-4 h-4 mr-2" />
                    Accept Selected ({selectedGaps.length})
                  </Button>
                )}

                <Button
                  onClick={handleBulkAccept}
                  disabled={isSaving || gaps.length === 0}
                  variant="outline"
                  className="text-green-600 hover:bg-green-50"
                >
                  <CheckCircle className="w-4 h-4 mr-2" />
                  Accept All (High Confidence)
                </Button>

                <Button
                  onClick={handleBulkReject}
                  disabled={isSaving || gaps.length === 0}
                  variant="outline"
                  className="text-red-600 hover:bg-red-50"
                >
                  <X className="w-4 h-4 mr-2" />
                  Reject All AI Suggestions
                </Button>
              </div>
            )}
          </div>

          {/* Continue to Questionnaire Button - Option 3: Show after 20s but disable until AI complete (Issue #1067) */}
          {scanSummary && onComplete && showQuestionnaireButton && (
            <div className="pt-4 mt-4 border-t border-gray-200">
              <div className="flex items-center justify-between">
                <div className="text-sm text-gray-600">
                  {aiAnalysisProgress && aiAnalysisProgress.percentage < 100 ? (
                    <>
                      <p className="font-medium mb-1">
                        🤖 AI analyzing gaps: {aiAnalysisProgress.completed}/{aiAnalysisProgress.total} assets complete ({aiAnalysisProgress.percentage}%)
                      </p>
                      <p className="text-xs">Button will enable when AI analysis completes...</p>
                    </>
                  ) : (
                    <>
                      <p className="font-medium mb-1">Gap analysis complete!</p>
                      <p>You can continue to the questionnaire phase or keep resolving gaps.</p>
                    </>
                  )}
                </div>
                <Button
                  onClick={handleContinueToQuestionnaire}
                  disabled={isContinuing || (aiAnalysisProgress ? aiAnalysisProgress.percentage < 100 : false)}
                  className="bg-blue-600 hover:bg-blue-700 text-white disabled:bg-gray-400 disabled:cursor-not-allowed"
                  size="lg"
                >
                  {isContinuing ? (
                    <>
                      <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                      Proceeding...
                    </>
                  ) : aiAnalysisProgress && aiAnalysisProgress.percentage < 100 ? (
                    <>
                      <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                      AI Analysis in Progress ({aiAnalysisProgress.percentage}%)
                    </>
                  ) : (
                    <>
                      Continue to Questionnaire →
                    </>
                  )}
                </Button>
              </div>
            </div>
          )}

          {/* Timer message while waiting for questionnaire button */}
          {scanSummary && onComplete && !showQuestionnaireButton && (
            <div className="pt-4 mt-4 border-t border-gray-200">
              <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg text-center">
                <p className="text-sm text-yellow-800 font-medium">
                  ⏱️ Please review the data gaps above before proceeding.
                </p>
                <p className="text-xs text-yellow-700 mt-1">
                  Continue button will appear shortly...
                </p>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* AG Grid */}
      <Card>
        <CardHeader>
          <CardTitle>Data Gaps ({gaps.length})</CardTitle>
          <div className="text-sm text-muted-foreground">
            Click cells to edit, then save individually. Color-coded AI
            confidence:
            <Badge className="ml-2 bg-green-100 text-green-800">≥80%</Badge>
            <Badge className="ml-1 bg-yellow-100 text-yellow-800">60-79%</Badge>
            <Badge className="ml-1 bg-red-100 text-red-800">&lt;60%</Badge>
          </div>
        </CardHeader>
        <CardContent>
          <div
            className="ag-theme-quartz"
            style={{ height: 500, width: "100%" }}
          >
            <AgGridReact
              theme="legacy"
              rowData={gaps}
              columnDefs={columnDefs}
              defaultColDef={{
                sortable: true,
                filter: true,
                resizable: true,
                tooltipValueGetter: (params) => params.value,
              }}
              getRowId={(params) =>
                params.data.id ||
                `${params.data.asset_id}-${params.data.field_name}`
              }
              onGridReady={onGridReady}
              onCellEditingStopped={handleCellEditingStopped}
              onSelectionChanged={onSelectionChanged}
              rowSelection={{
                mode: "multiRow",
                checkboxes: true,
                headerCheckbox: true,
                enableClickSelection: false,
              }}
            />
          </div>
        </CardContent>
      </Card>

      {/* Completion Section - Bug #757 Fix: Only show after loading completes */}
      {gaps.length === 0 && !isScanning && !isLoadingGaps && (
        <Card>
          <CardContent className="pt-6">
            <div className="text-center">
              <CheckCircle className="h-12 w-12 text-green-500 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                No Gaps Identified
              </h3>
              <p className="text-gray-600 mb-4">
                All selected assets have complete critical attributes. Ready to
                proceed.
              </p>
              {onComplete && (
                <Button
                  onClick={onComplete}
                  className="bg-blue-600 hover:bg-blue-700"
                >
                  Continue to Next Phase
                </Button>
              )}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default DataGapDiscovery;
