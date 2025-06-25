import React, { useState, useEffect } from 'react';
import { 
  Brain, 
  Users, 
  Loader2, 
  CheckCircle, 
  AlertCircle,
  Clock,
  Zap,
  Network,
  TrendingUp
} from 'lucide-react';
import { useCrewEscalation } from '../../hooks/discovery/useCrewEscalation';

interface ThinkPonderButtonProps {
  flowId: string;
  page: string;
  agentId: string;
  context?: Record<string, any>;
  pageData?: Record<string, any>;
  className?: string;
  disabled?: boolean;
  onEscalationStart?: (escalationId: string, type: 'think' | 'ponder') => void;
  onEscalationComplete?: (escalationId: string, results: any) => void;
}

type ButtonState = 'idle' | 'thinking' | 'pondering' | 'completed' | 'error';

const ThinkPonderButton: React.FC<ThinkPonderButtonProps> = ({
  flowId,
  page,
  agentId,
  context = {},
  pageData = {},
  className = "",
  disabled = false,
  onEscalationStart,
  onEscalationComplete
}) => {
  const [buttonState, setButtonState] = useState<ButtonState>('idle');
  const [currentEscalationId, setCurrentEscalationId] = useState<string | null>(null);
  const [progress, setProgress] = useState(0);
  const [currentPhase, setCurrentPhase] = useState<string>('');
  const [crewActivity, setCrewActivity] = useState<any[]>([]);
  const [results, setResults] = useState<any>(null);

  // Use the crew escalation hooks
  const {
    triggerThink,
    triggerPonderMore,
    getEscalationStatus,
    isThinking,
    isPondering,
    thinkError,
    ponderError
  } = useCrewEscalation(flowId);

  // Poll for escalation status when active
  useEffect(() => {
    if (!currentEscalationId || buttonState === 'idle') return;

    const pollInterval = setInterval(async () => {
      try {
        const status = await getEscalationStatus(currentEscalationId);
        
        if (status) {
          setProgress(status.progress || 0);
          setCurrentPhase(status.current_phase || '');
          setCrewActivity(status.crew_activity || []);
          
          if (status.status === 'completed') {
            setButtonState('completed');
            setResults(status.results);
            onEscalationComplete?.(currentEscalationId, status.results);
            clearInterval(pollInterval);
          } else if (status.status === 'failed') {
            setButtonState('error');
            clearInterval(pollInterval);
          }
        }
      } catch (error) {
        console.error('Error polling escalation status:', error);
      }
    }, 2000); // Poll every 2 seconds

    return () => clearInterval(pollInterval);
  }, [currentEscalationId, buttonState, getEscalationStatus, onEscalationComplete]);

  const handleThink = async () => {
    if (disabled || buttonState !== 'idle') return;

    try {
      setButtonState('thinking');
      setProgress(0);
      setCurrentPhase('Initializing...');
      
      const response = await triggerThink({
        agent_id: agentId,
        context: { ...context, page, action: 'deeper_analysis' },
        complexity_level: 'standard',
        page_data: pageData
      });

      if (response.escalation_id) {
        setCurrentEscalationId(response.escalation_id);
        onEscalationStart?.(response.escalation_id, 'think');
      }
    } catch (error) {
      console.error('Failed to trigger thinking:', error);
      setButtonState('error');
    }
  };

  const handlePonderMore = async () => {
    if (disabled || buttonState !== 'idle') return;

    try {
      setButtonState('pondering');
      setProgress(0);
      setCurrentPhase('Setting up collaboration...');
      
      const response = await triggerPonderMore({
        agent_id: agentId,
        context: { ...context, page, action: 'crew_collaboration' },
        collaboration_type: 'cross_agent',
        page_data: pageData
      });

      if (response.escalation_id) {
        setCurrentEscalationId(response.escalation_id);
        onEscalationStart?.(response.escalation_id, 'ponder');
      }
    } catch (error) {
      console.error('Failed to trigger pondering:', error);
      setButtonState('error');
    }
  };

  const resetButtons = () => {
    setButtonState('idle');
    setCurrentEscalationId(null);
    setProgress(0);
    setCurrentPhase('');
    setCrewActivity([]);
    setResults(null);
  };

  const getButtonContent = (type: 'think' | 'ponder') => {
    const isActive = (type === 'think' && buttonState === 'thinking') || 
                     (type === 'ponder' && buttonState === 'pondering');
    const isCompleted = buttonState === 'completed';
    const hasError = buttonState === 'error';

    if (hasError) {
      return {
        icon: <AlertCircle className="w-4 h-4" />,
        text: 'Error',
        className: 'bg-red-100 hover:bg-red-200 text-red-700 border-red-300'
      };
    }

    if (isCompleted) {
      return {
        icon: <CheckCircle className="w-4 h-4" />,
        text: 'Completed',
        className: 'bg-green-100 hover:bg-green-200 text-green-700 border-green-300'
      };
    }

    if (isActive) {
      return {
        icon: <Loader2 className="w-4 h-4 animate-spin" />,
        text: type === 'think' ? 'Thinking...' : 'Pondering...',
        className: type === 'think' ? 
          'bg-blue-100 text-blue-700 border-blue-300' : 
          'bg-purple-100 text-purple-700 border-purple-300'
      };
    }

    return {
      icon: type === 'think' ? <Brain className="w-4 h-4" /> : <Users className="w-4 h-4" />,
      text: type === 'think' ? 'Think' : 'Ponder More',
      className: type === 'think' ? 
        'bg-blue-50 hover:bg-blue-100 text-blue-700 border-blue-200 hover:border-blue-300' : 
        'bg-purple-50 hover:bg-purple-100 text-purple-700 border-purple-200 hover:border-purple-300'
    };
  };

  const thinkContent = getButtonContent('think');
  const ponderContent = getButtonContent('ponder');

  const isProcessing = buttonState === 'thinking' || buttonState === 'pondering';
  const canInteract = buttonState === 'idle' && !disabled;

  return (
    <div className={`bg-white rounded-lg border shadow-sm p-4 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-2">
          <Zap className="w-5 h-5 text-orange-500" />
          <h3 className="font-semibold text-gray-900">Progressive Intelligence</h3>
        </div>
        {buttonState === 'completed' && (
          <button
            onClick={resetButtons}
            className="text-sm text-gray-500 hover:text-gray-700 underline"
          >
            Reset
          </button>
        )}
      </div>

      {/* Action Buttons */}
      <div className="grid grid-cols-2 gap-3 mb-4">
        <button
          onClick={handleThink}
          disabled={!canInteract || isThinking}
          className={`
            flex items-center justify-center space-x-2 px-4 py-3 rounded-lg border transition-all duration-200
            disabled:opacity-50 disabled:cursor-not-allowed
            ${thinkContent.className}
          `}
        >
          {thinkContent.icon}
          <span className="font-medium">{thinkContent.text}</span>
        </button>

        <button
          onClick={handlePonderMore}
          disabled={!canInteract || isPondering}
          className={`
            flex items-center justify-center space-x-2 px-4 py-3 rounded-lg border transition-all duration-200
            disabled:opacity-50 disabled:cursor-not-allowed
            ${ponderContent.className}
          `}
        >
          {ponderContent.icon}
          <span className="font-medium">{ponderContent.text}</span>
        </button>
      </div>

      {/* Progress Visualization */}
      {isProcessing && (
        <div className="mb-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-gray-700">
              {currentPhase || 'Processing...'}
            </span>
            <span className="text-sm text-gray-500">{progress}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className={`h-2 rounded-full transition-all duration-300 ${
                buttonState === 'thinking' ? 'bg-blue-500' : 'bg-purple-500'
              }`}
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>
      )}

      {/* Crew Activity */}
      {crewActivity.length > 0 && (
        <div className="mb-4">
          <h4 className="text-sm font-medium text-gray-700 mb-2 flex items-center">
            <Network className="w-4 h-4 mr-1" />
            Crew Activity
          </h4>
          <div className="space-y-1 max-h-32 overflow-y-auto">
            {crewActivity.slice(-3).map((activity, index) => (
              <div key={index} className="text-xs text-gray-600 flex items-center space-x-2">
                <Clock className="w-3 h-3 text-gray-400" />
                <span>{activity.activity}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Results Summary */}
      {results && buttonState === 'completed' && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-3">
          <h4 className="text-sm font-medium text-green-800 mb-2 flex items-center">
            <TrendingUp className="w-4 h-4 mr-1" />
            Results Summary
          </h4>
          <div className="text-sm text-green-700 space-y-1">
            {results.insights_generated && (
              <div>Generated {results.insights_generated} new insights</div>
            )}
            {results.recommendations && results.recommendations.length > 0 && (
              <div>{results.recommendations.length} recommendations provided</div>
            )}
            {results.confidence_improvements && (
              <div>
                Confidence improved by {Math.round((results.confidence_improvements.average_confidence_increase || 0) * 100)}%
              </div>
            )}
          </div>
        </div>
      )}

      {/* Error State */}
      {buttonState === 'error' && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-3">
          <div className="flex items-center space-x-2 text-red-700">
            <AlertCircle className="w-4 h-4" />
            <span className="text-sm font-medium">
              {thinkError || ponderError || 'An error occurred during processing'}
            </span>
          </div>
          <button
            onClick={resetButtons}
            className="mt-2 text-sm text-red-600 hover:text-red-800 underline"
          >
            Try again
          </button>
        </div>
      )}

      {/* Help Text */}
      {buttonState === 'idle' && (
        <div className="text-xs text-gray-500 text-center">
          Use <strong>Think</strong> for deeper analysis or <strong>Ponder More</strong> for crew collaboration
        </div>
      )}
    </div>
  );
};

export default ThinkPonderButton; 