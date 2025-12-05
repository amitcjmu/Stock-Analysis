import React from 'react';
import { Card, CardContent, CardHeader } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import {
  Home,
  RefreshCw,
  Wrench,
  ShoppingCart,
  Trash2,
  Package,
  CheckCircle,
  AlertTriangle,
  Clock,
  DollarSign,
  ChevronDown,
  ChevronUp,
  Eye,
  UserCheck
} from 'lucide-react';
import { cn } from '@/lib/utils';

/**
 * 6R Strategy Configuration
 * Each strategy has an icon, color scheme, and description
 */
export const SIX_R_STRATEGIES = {
  rehost: {
    value: 'rehost',
    label: 'Rehost',
    shortLabel: 'Lift & Shift',
    description: 'Move to cloud without changes',
    icon: Home,
    color: 'blue',
    bgColor: 'bg-blue-50',
    borderColor: 'border-blue-200',
    textColor: 'text-blue-700',
    badgeColor: 'bg-blue-100 text-blue-800 border-blue-300',
    iconBg: 'bg-blue-100'
  },
  replatform: {
    value: 'replatform',
    label: 'Replatform',
    shortLabel: 'Lift-Tinker-Shift',
    description: 'Minor optimizations for cloud',
    icon: RefreshCw,
    color: 'purple',
    bgColor: 'bg-purple-50',
    borderColor: 'border-purple-200',
    textColor: 'text-purple-700',
    badgeColor: 'bg-purple-100 text-purple-800 border-purple-300',
    iconBg: 'bg-purple-100'
  },
  refactor: {
    value: 'refactor',
    label: 'Refactor',
    shortLabel: 'Cloud-Native',
    description: 'Significant code changes for cloud-native',
    icon: Wrench,
    color: 'green',
    bgColor: 'bg-green-50',
    borderColor: 'border-green-200',
    textColor: 'text-green-700',
    badgeColor: 'bg-green-100 text-green-800 border-green-300',
    iconBg: 'bg-green-100'
  },
  repurchase: {
    value: 'repurchase',
    label: 'Repurchase',
    shortLabel: 'SaaS',
    description: 'Replace with SaaS solution',
    icon: ShoppingCart,
    color: 'amber',
    bgColor: 'bg-amber-50',
    borderColor: 'border-amber-200',
    textColor: 'text-amber-700',
    badgeColor: 'bg-amber-100 text-amber-800 border-amber-300',
    iconBg: 'bg-amber-100'
  },
  retire: {
    value: 'retire',
    label: 'Retire',
    shortLabel: 'Decommission',
    description: 'Decommission the application',
    icon: Trash2,
    color: 'red',
    bgColor: 'bg-red-50',
    borderColor: 'border-red-200',
    textColor: 'text-red-700',
    badgeColor: 'bg-red-100 text-red-800 border-red-300',
    iconBg: 'bg-red-100'
  },
  retain: {
    value: 'retain',
    label: 'Retain',
    shortLabel: 'Keep On-Prem',
    description: 'Keep on-premises for now',
    icon: Package,
    color: 'gray',
    bgColor: 'bg-gray-50',
    borderColor: 'border-gray-200',
    textColor: 'text-gray-700',
    badgeColor: 'bg-gray-100 text-gray-800 border-gray-300',
    iconBg: 'bg-gray-100'
  }
} as const;

export type SixRStrategyType = keyof typeof SIX_R_STRATEGIES;

/**
 * Effort Level Configuration
 */
export const EFFORT_LEVELS = {
  S: { label: 'Small', shortLabel: 'S', days: '1-5 days', color: 'text-green-600', bgColor: 'bg-green-100' },
  M: { label: 'Medium', shortLabel: 'M', days: '1-2 weeks', color: 'text-yellow-600', bgColor: 'bg-yellow-100' },
  L: { label: 'Large', shortLabel: 'L', days: '2-4 weeks', color: 'text-orange-600', bgColor: 'bg-orange-100' },
  XL: { label: 'Extra Large', shortLabel: 'XL', days: '1-2 months', color: 'text-red-600', bgColor: 'bg-red-100' }
} as const;

export type EffortLevel = keyof typeof EFFORT_LEVELS;

/**
 * Cost Range Configuration
 */
export const COST_RANGES = {
  low: { label: 'Low', range: '$10K - $25K', color: 'text-green-600' },
  medium: { label: 'Medium', range: '$25K - $75K', color: 'text-yellow-600' },
  high: { label: 'High', range: '$75K - $150K', color: 'text-orange-600' },
  very_high: { label: 'Very High', range: '$150K+', color: 'text-red-600' }
} as const;

export type CostRange = keyof typeof COST_RANGES;

/**
 * Alternative Strategy with confidence
 */
export interface AlternativeStrategy {
  strategy: SixRStrategyType;
  confidence: number;
  effort?: EffortLevel;
  cost_range?: CostRange;
}

/**
 * RecommendationCard Props
 */
export interface RecommendationCardProps {
  application_id: string;
  application_name: string;
  application_version?: string;
  recommended_strategy: SixRStrategyType;
  confidence: number;
  effort?: EffortLevel;
  cost_range?: CostRange;
  rationale: string;
  risk_factors?: string[];
  alternatives?: AlternativeStrategy[];
  is_accepted?: boolean;
  is_expanded?: boolean;
  onAccept?: (applicationId: string) => void;
  onReviewAlternatives?: (applicationId: string) => void;
  onRequestSME?: (applicationId: string) => void;
  onToggleExpand?: (applicationId: string) => void;
  className?: string;
}

/**
 * Get confidence level info for styling
 */
const getConfidenceLevel = (score: number) => {
  if (score >= 0.9) return { level: 'Excellent', color: 'text-green-600', bgColor: 'bg-green-100', progressColor: 'bg-green-500' };
  if (score >= 0.8) return { level: 'Good', color: 'text-green-600', bgColor: 'bg-green-100', progressColor: 'bg-green-500' };
  if (score >= 0.7) return { level: 'Moderate', color: 'text-yellow-600', bgColor: 'bg-yellow-100', progressColor: 'bg-yellow-500' };
  if (score >= 0.6) return { level: 'Low', color: 'text-orange-600', bgColor: 'bg-orange-100', progressColor: 'bg-orange-500' };
  return { level: 'Very Low', color: 'text-red-600', bgColor: 'bg-red-100', progressColor: 'bg-red-500' };
};

/**
 * RecommendationCard Component
 *
 * Displays a rich, intuitive 6R recommendation card with:
 * - Visual strategy icon and color coding
 * - Confidence score with progress indicator
 * - Effort estimates (S/M/L/XL)
 * - Cost range display
 * - Rationale and risk factors
 * - Alternative strategies
 * - Accept/Review/SME actions
 */
export const RecommendationCard: React.FC<RecommendationCardProps> = ({
  application_id,
  application_name,
  application_version,
  recommended_strategy,
  confidence,
  effort,
  cost_range,
  rationale,
  risk_factors = [],
  alternatives = [],
  is_accepted = false,
  is_expanded = false,
  onAccept,
  onReviewAlternatives,
  onRequestSME,
  onToggleExpand,
  className
}) => {
  const strategyConfig = SIX_R_STRATEGIES[recommended_strategy] || SIX_R_STRATEGIES.retain;
  const StrategyIcon = strategyConfig.icon;
  const confidenceInfo = getConfidenceLevel(confidence);
  const effortConfig = effort ? EFFORT_LEVELS[effort] : null;
  const costConfig = cost_range ? COST_RANGES[cost_range] : null;
  const percentage = Math.round(confidence * 100);

  return (
    <Card className={cn(
      'transition-all duration-200 hover:shadow-md',
      strategyConfig.borderColor,
      is_accepted && 'ring-2 ring-green-500 ring-opacity-50',
      className
    )}>
      <CardHeader className={cn('pb-3', strategyConfig.bgColor)}>
        <div className="flex items-start justify-between gap-4">
          {/* Application Info */}
          <div className="flex-1 min-w-0">
            <h3 className="text-lg font-semibold text-gray-900 truncate">
              {application_name}
            </h3>
            {application_version && (
              <p className="text-sm text-gray-500">v{application_version}</p>
            )}
          </div>

          {/* Strategy Badge */}
          <div className={cn(
            'flex items-center gap-2 px-3 py-2 rounded-lg border',
            strategyConfig.badgeColor
          )}>
            <div className={cn('p-1.5 rounded-full', strategyConfig.iconBg)}>
              <StrategyIcon className={cn('h-5 w-5', strategyConfig.textColor)} />
            </div>
            <div className="text-right">
              <div className="font-semibold text-sm">{strategyConfig.label}</div>
              <div className="text-xs opacity-80">{strategyConfig.shortLabel}</div>
            </div>
          </div>
        </div>
      </CardHeader>

      <CardContent className="pt-4 space-y-4">
        {/* Metrics Row */}
        <div className="grid grid-cols-3 gap-4">
          {/* Confidence Score */}
          <div className="space-y-1">
            <div className="flex items-center gap-1.5 text-sm font-medium text-gray-600">
              <CheckCircle className="h-4 w-4" />
              <span>Confidence</span>
            </div>
            <div className="flex items-center gap-2">
              <div className={cn('text-xl font-bold', confidenceInfo.color)}>
                {percentage}%
              </div>
              <Badge variant="outline" className={cn('text-xs', confidenceInfo.bgColor, confidenceInfo.color)}>
                {confidenceInfo.level}
              </Badge>
            </div>
            <Progress
              value={percentage}
              className="h-1.5"
            />
          </div>

          {/* Effort Estimate */}
          <div className="space-y-1">
            <div className="flex items-center gap-1.5 text-sm font-medium text-gray-600">
              <Clock className="h-4 w-4" />
              <span>Effort</span>
            </div>
            {effortConfig ? (
              <>
                <div className={cn('text-xl font-bold', effortConfig.color)}>
                  {effortConfig.shortLabel}
                </div>
                <div className="text-xs text-gray-500">{effortConfig.days}</div>
              </>
            ) : (
              <div className="text-sm text-gray-400 italic">Not estimated</div>
            )}
          </div>

          {/* Cost Range */}
          <div className="space-y-1">
            <div className="flex items-center gap-1.5 text-sm font-medium text-gray-600">
              <DollarSign className="h-4 w-4" />
              <span>Est. Cost</span>
            </div>
            {costConfig ? (
              <>
                <div className={cn('text-lg font-bold', costConfig.color)}>
                  {costConfig.label}
                </div>
                <div className="text-xs text-gray-500">{costConfig.range}</div>
              </>
            ) : (
              <div className="text-sm text-gray-400 italic">Not estimated</div>
            )}
          </div>
        </div>

        {/* Rationale */}
        <div className="p-3 bg-gray-50 rounded-lg border border-gray-100">
          <p className="text-sm text-gray-700 leading-relaxed">
            {rationale}
          </p>
        </div>

        {/* Risk Factors (if any) */}
        {risk_factors.length > 0 && (
          <div className="space-y-2">
            <div className="flex items-center gap-1.5 text-sm font-medium text-orange-600">
              <AlertTriangle className="h-4 w-4" />
              <span>Risk Factors ({risk_factors.length})</span>
            </div>
            <div className="flex flex-wrap gap-2">
              {risk_factors.slice(0, 3).map((risk, idx) => (
                <Badge
                  key={idx}
                  variant="outline"
                  className="bg-orange-50 text-orange-700 border-orange-200 text-xs"
                >
                  {risk}
                </Badge>
              ))}
              {risk_factors.length > 3 && (
                <Badge variant="outline" className="text-xs">
                  +{risk_factors.length - 3} more
                </Badge>
              )}
            </div>
          </div>
        )}

        {/* Alternative Strategies (expandable) */}
        {alternatives.length > 0 && (
          <div className="border-t pt-3">
            <button
              onClick={() => onToggleExpand?.(application_id)}
              className="flex items-center justify-between w-full text-sm text-gray-600 hover:text-gray-900"
            >
              <span className="font-medium">Alternative Strategies ({alternatives.length})</span>
              {is_expanded ? (
                <ChevronUp className="h-4 w-4" />
              ) : (
                <ChevronDown className="h-4 w-4" />
              )}
            </button>

            {is_expanded && (
              <div className="mt-3 space-y-2">
                {alternatives.map((alt, idx) => {
                  const altConfig = SIX_R_STRATEGIES[alt.strategy] || SIX_R_STRATEGIES.retain;
                  const AltIcon = altConfig.icon;
                  const altEffort = alt.effort ? EFFORT_LEVELS[alt.effort] : null;
                  const altCost = alt.cost_range ? COST_RANGES[alt.cost_range] : null;

                  return (
                    <div
                      key={idx}
                      className={cn(
                        'flex items-center justify-between p-2 rounded-lg border',
                        altConfig.bgColor,
                        altConfig.borderColor
                      )}
                    >
                      <div className="flex items-center gap-2">
                        <AltIcon className={cn('h-4 w-4', altConfig.textColor)} />
                        <span className={cn('font-medium text-sm', altConfig.textColor)}>
                          {altConfig.label}
                        </span>
                        <Badge variant="outline" className="text-xs">
                          {Math.round(alt.confidence * 100)}%
                        </Badge>
                      </div>
                      <div className="flex items-center gap-3 text-xs text-gray-500">
                        {altEffort && <span>{altEffort.shortLabel}</span>}
                        {altCost && <span>{altCost.range}</span>}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        )}

        {/* Action Buttons */}
        <div className="flex flex-wrap items-center gap-2 pt-2 border-t">
          <Button
            onClick={() => onAccept?.(application_id)}
            disabled={is_accepted}
            className={cn(
              'flex-1 min-w-[120px]',
              is_accepted ? 'bg-green-600 hover:bg-green-600' : ''
            )}
          >
            {is_accepted ? (
              <>
                <CheckCircle className="h-4 w-4 mr-2" />
                Accepted
              </>
            ) : (
              'Accept'
            )}
          </Button>

          <Button
            variant="outline"
            onClick={() => onReviewAlternatives?.(application_id)}
            className="flex-1 min-w-[120px]"
          >
            <Eye className="h-4 w-4 mr-2" />
            Alternatives
          </Button>

          <Button
            variant="ghost"
            onClick={() => onRequestSME?.(application_id)}
            className="flex-1 min-w-[120px]"
          >
            <UserCheck className="h-4 w-4 mr-2" />
            Request SME
          </Button>
        </div>
      </CardContent>
    </Card>
  );
};

export default RecommendationCard;
