import { useQuery, useMutation } from '@tanstack/react-query'
import { useQueryClient } from '@tanstack/react-query'
import type { fetchScanProgress, fetchScanLogs , ScanProgress, ScanLog } from '@/services/scanService'
import { startScan, pauseScan, resumeScan, stopScan } from '@/services/scanService'
import { useAuth } from '@/contexts/AuthContext';
import { useToast } from '@/components/ui/use-toast';
import { logger } from '@/utils/logger';

const SCAN_QUERY_KEYS = {
  SCAN_PROGRESS: ['scan', 'progress'],
  SCAN_LOGS: ['scan', 'logs'],
} as const;

export const useScanProgress = () => {
  const { isAuthenticated } = useAuth();

  return useQuery<ScanProgress, Error>({
    queryKey: SCAN_QUERY_KEYS.SCAN_PROGRESS,
    queryFn: fetchScanProgress,
    enabled: isAuthenticated,
    refetchInterval: false, // Disable aggressive polling - use manual refresh
    staleTime: 30000, // Data is considered fresh for 30 seconds
    refetchOnWindowFocus: false, // Disable focus refetching
    onError: (error) => {
      logger.error('Error fetching scan progress:', error);
    },
  });
};

export const useScanLogs = (options = {}) => {
  const { isAuthenticated } = useAuth();
  const { enabled = true, ...queryOptions } = options;

  return useQuery<ScanLog[], Error>({
    queryKey: SCAN_QUERY_KEYS.SCAN_LOGS,
    queryFn: fetchScanLogs,
    enabled: isAuthenticated && enabled,
    refetchInterval: false, // Disable aggressive polling - use manual refresh
    staleTime: 30000, // Data is considered fresh for 30 seconds
    refetchOnWindowFocus: false, // Disable focus refetching
    ...queryOptions,
    onError: (error) => {
      logger.error('Error fetching scan logs:', error);
    },
  });
};

export const useScanMutations = () => {
  const queryClient = useQueryClient();
  const { toast } = useToast();
  const { isAuthenticated } = useAuth();

  const invalidateScanQueries = () => {
    queryClient.invalidateQueries({ queryKey: SCAN_QUERY_KEYS.SCAN_PROGRESS });
    queryClient.invalidateQueries({ queryKey: SCAN_QUERY_KEYS.SCAN_LOGS });
  };

  const startScanMutation = useMutation({
    mutationFn: startScan,
    onSuccess: (data) => {
      toast({
        title: 'Scan Started',
        description: data.message || 'Scan has been started successfully',
        variant: 'default',
      });
      invalidateScanQueries();
    },
    onError: (error: Error) => {
      logger.error('Error starting scan:', error);
      toast({
        title: 'Error',
        description: error.message || 'Failed to start scan',
        variant: 'destructive',
      });
    },
  });

  const pauseScanMutation = useMutation({
    mutationFn: pauseScan,
    onSuccess: (data) => {
      toast({
        title: 'Scan Paused',
        description: data.message || 'Scan has been paused',
        variant: 'default',
      });
      invalidateScanQueries();
    },
    onError: (error: Error) => {
      logger.error('Error pausing scan:', error);
      toast({
        title: 'Error',
        description: error.message || 'Failed to pause scan',
        variant: 'destructive',
      });
    },
  });

  const resumeScanMutation = useMutation({
    mutationFn: resumeScan,
    onSuccess: (data) => {
      toast({
        title: 'Scan Resumed',
        description: data.message || 'Scan has been resumed',
        variant: 'default',
      });
      invalidateScanQueries();
    },
    onError: (error: Error) => {
      logger.error('Error resuming scan:', error);
      toast({
        title: 'Error',
        description: error.message || 'Failed to resume scan',
        variant: 'destructive',
      });
    },
  });

  const stopScanMutation = useMutation({
    mutationFn: stopScan,
    onSuccess: (data) => {
      toast({
        title: 'Scan Stopped',
        description: data.message || 'Scan has been stopped',
        variant: 'default',
      });
      invalidateScanQueries();
    },
    onError: (error: Error) => {
      logger.error('Error stopping scan:', error);
      toast({
        title: 'Error',
        description: error.message || 'Failed to stop scan',
        variant: 'destructive',
      });
    },
  });

  return {
    startScan: startScanMutation.mutateAsync,
    pauseScan: pauseScanMutation.mutateAsync,
    resumeScan: resumeScanMutation.mutateAsync,
    stopScan: stopScanMutation.mutateAsync,
    isLoading:
      startScanMutation.isPending ||
      pauseScanMutation.isPending ||
      resumeScanMutation.isPending ||
      stopScanMutation.isPending,
  };
};

export const useScanControls = () => {
  const { data: scanProgress, isLoading: isLoadingProgress } = useScanProgress();
  const { data: scanLogs, isLoading: isLoadingLogs } = useScanLogs();
  const {
    startScan,
    pauseScan,
    resumeScan,
    stopScan,
    isLoading: isMutating
  } = useScanMutations();

  const isLoading = isLoadingProgress || isLoadingLogs || isMutating;

  // Determine the current scan state
  const scanState = scanProgress?.status || 'idle';
  const isScanning = scanState === 'scanning';
  const isPaused = scanState === 'paused';
  const isIdle = scanState === 'idle' || !scanState;

  // Handle scan actions
  const handleStartScan = (scanType: 'full' | 'incremental' | 'targeted' = 'full') => {
    return startScan({ scanType });
  };

  const handlePauseScan = (scanId: string) => {
    return pauseScan(scanId);
  };

  const handleResumeScan = (scanId: string) => {
    return resumeScan(scanId);
  };

  const handleStopScan = (scanId: string) => {
    return stopScan(scanId);
  };

  return {
    // State
    scanProgress,
    scanLogs,
    scanState,
    isScanning,
    isPaused,
    isIdle,
    isLoading,

    // Actions
    startScan: handleStartScan,
    pauseScan: handlePauseScan,
    resumeScan: handleResumeScan,
    stopScan: handleStopScan,
  };
};
