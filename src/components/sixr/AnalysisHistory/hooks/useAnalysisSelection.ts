import { useState } from 'react'
import { useCallback } from 'react'

export const useAnalysisSelection = () => {
  const [selectedAnalyses, setSelectedAnalyses] = useState<number[]>([]);

  const handleSelectAnalysis = useCallback((analysisId: number) => {
    setSelectedAnalyses(prev => 
      prev.includes(analysisId)
        ? prev.filter(id => id !== analysisId)
        : [...prev, analysisId]
    );
  }, []);

  const handleSelectAll = useCallback((analysisIds: number[]) => {
    setSelectedAnalyses(prev => {
      const allSelected = analysisIds.every(id => prev.includes(id));
      if (allSelected) {
        return prev.filter(id => !analysisIds.includes(id));
      } else {
        return [...new Set([...prev, ...analysisIds])];
      }
    });
  }, []);

  const clearSelection = useCallback(() => {
    setSelectedAnalyses([]);
  }, []);

  const isSelected = useCallback((analysisId: number) => {
    return selectedAnalyses.includes(analysisId);
  }, [selectedAnalyses]);

  return {
    selectedAnalyses,
    handleSelectAnalysis,
    handleSelectAll,
    clearSelection,
    isSelected
  };
};