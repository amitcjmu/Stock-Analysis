import { useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useToast } from '../use-toast';
import { DependencyData, DependencyNavigationOptions } from '../../types/dependency';
import { FlowState } from '../../types/discovery';

export const useDependencyNavigation = (
  flowState: FlowState | null,
  dependencyData: DependencyData | null
) => {
  const navigate = useNavigate();
  const { toast } = useToast();

  const validateDependencyCompletion = useCallback((dependency_progress: DependencyData) => {
    const appServerComplete = dependency_progress.app_server_mapping.hosting_relationships.every(
      r => r.status === 'confirmed'
    );
    const appAppComplete = dependency_progress.cross_application_mapping.cross_app_dependencies.every(
      d => d.status === 'confirmed'
    );

    return appServerComplete && appAppComplete;
  }, []);

  const handleContinueToNextPhase = useCallback(async (options: DependencyNavigationOptions = {}) => {
    const { skipValidation = false, forceComplete = false } = options;

    if (!dependencyData && !skipValidation) {
      toast({
        title: 'Validation Error',
        description: 'Please complete the dependency analysis before continuing.',
        variant: 'destructive'
      });
      return;
    }

    if (!skipValidation && !forceComplete) {
      const isComplete = validateDependencyCompletion(dependencyData!);
      if (!isComplete) {
        toast({
          title: 'Incomplete Dependencies',
          description: 'Please confirm all dependencies before continuing.',
          variant: 'destructive'
        });
        return;
      }
    }

    // Navigate to the next phase based on flow state
    const nextPhase = flowState?.next_phase || 'tech-debt';
    navigate(`/discovery/${nextPhase}`);
  }, [dependencyData, flowState, navigate, toast, validateDependencyCompletion]);

  const handleNavigateToInventory = useCallback(() => {
    navigate('/discovery/inventory');
  }, [navigate]);

  const handleNavigateToDataCleansing = useCallback(() => {
    navigate('/discovery/data-cleansing');
  }, [navigate]);

  const handleNavigateToAttributeMapping = useCallback(() => {
    navigate('/discovery/attribute-mapping');
  }, [navigate]);

  return {
    handleContinueToNextPhase,
    handleNavigateToInventory,
    handleNavigateToDataCleansing,
    handleNavigateToAttributeMapping,
    validateDependencyCompletion,
    getDependencyProgress: validateDependencyCompletion
  };
}; 