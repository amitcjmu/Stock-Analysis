import { useNavigate } from 'react-router-dom';
import { useCallback } from 'react';
import { useToast } from '../use-toast';

interface InventoryProgress {
  total_assets: number;
  classified_assets: number;
  servers: number;
  applications: number;
  devices: number;
  databases: number;
  unknown: number;
  classification_accuracy: number;
  crew_completion_status: Record<string, boolean>;
}

interface InventoryNavigationOptions {
  flow_session_id?: string;
  inventory_progress: InventoryProgress;
  client_account_id: string;
  engagement_id: string;
}

export const useInventoryNavigation = () => {
  const navigate = useNavigate();
  const { toast } = useToast();

  const handleContinueToAppServerDependencies = useCallback(async (options: InventoryNavigationOptions) => {
    const { flow_session_id, inventory_progress, client_account_id, engagement_id } = options;

    try {
      // Validate inventory completion
      if (inventory_progress.classification_accuracy < 80) {
        toast({
          title: "⚠️ Classification Incomplete",
          description: `Asset classification is ${inventory_progress.classification_accuracy.toFixed(1)}%. Please achieve at least 80% classification accuracy before continuing.`,
          variant: "destructive"
        });
        return;
      }

      if (inventory_progress.total_assets === 0) {
        toast({
          title: "⚠️ No Assets Available",
          description: "Please ensure assets are discovered and classified before proceeding to dependency analysis.",
          variant: "destructive"
        });
        return;
      }

      // Show progress toast
      toast({
        title: "🚀 Navigating to App-Server Dependencies",
        description: "Inventory building complete. Preparing dependency analysis phase...",
      });

      // Navigate to App-Server Dependencies phase with state
      navigate('/discovery/dependencies', {
        state: {
          from_phase: 'inventory_building',
          flow_session_id: flow_session_id,
          inventory_progress: inventory_progress,
          client_account_id: client_account_id,
          engagement_id: engagement_id,
          timestamp: new Date().toISOString()
        }
      });

      // Success toast after navigation
      setTimeout(() => {
        toast({
          title: "✅ Phase Transition Complete",
          description: "Now analyzing application-to-server dependencies.",
        });
      }, 1000);

    } catch (error) {
      console.error('❌ Error navigating to App-Server Dependencies:', error);
      toast({
        title: "❌ Navigation Failed",
        description: "Could not proceed to dependency analysis. Please try again.",
        variant: "destructive"
      });
    }
  }, [navigate, toast]);

  const handleNavigateToDataCleansing = useCallback(() => {
    navigate('/discovery/data-cleansing');
  }, [navigate]);

  const handleNavigateToAttributeMapping = useCallback(() => {
    navigate('/discovery/attribute-mapping');
  }, [navigate]);

  const validateInventoryCompletion = useCallback((inventory_progress: InventoryProgress): boolean => {
    const isComplete = inventory_progress.classification_accuracy >= 80 && 
                      inventory_progress.total_assets > 0 &&
                      inventory_progress.unknown < inventory_progress.total_assets * 0.2; // Less than 20% unknown

    return isComplete;
  }, []);

  const getInventoryCompletionMessage = useCallback((inventory_progress: InventoryProgress): string => {
    if (inventory_progress.total_assets === 0) {
      return "No assets discovered. Please run inventory building analysis.";
    }
    
    if (inventory_progress.classification_accuracy < 80) {
      return `Classification accuracy is ${inventory_progress.classification_accuracy.toFixed(1)}%. Need 80%+ to continue.`;
    }
    
    if (inventory_progress.unknown > inventory_progress.total_assets * 0.2) {
      return `Too many unclassified assets (${inventory_progress.unknown}). Please improve classification.`;
    }
    
    return "Inventory building complete. Ready for dependency analysis.";
  }, []);

  return {
    handleContinueToAppServerDependencies,
    handleNavigateToDataCleansing,
    handleNavigateToAttributeMapping,
    validateInventoryCompletion,
    getInventoryCompletionMessage,
  };
}; 