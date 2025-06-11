export type TechDebtCategory = 'all' | 'security' | 'performance' | 'maintainability' | 'compliance';
export type RiskLevel = 'all' | 'critical' | 'high' | 'medium' | 'low';
export type StatusFilter = 'all' | 'active' | 'mitigated' | 'planned';

export interface TechDebtSummary {
  // Standardized field names
  critical: number;
  high: number;
  medium: number;
  low: number;
  endOfLife: number;
  deprecated: number;
  totalItems: number;
  
  // Legacy field names - kept for backward compatibility
  criticalRisk?: number;
  highRisk?: number;
  mediumRisk?: number;
  lowRisk?: number;
  total?: number;
}

export interface TechDebtItem {
  id: string;
  name: string;
  description: string;
  category: TechDebtCategory;
  component: string; // Added to match component usage
  securityRisk: RiskLevel;
  status: StatusFilter;
  supportStatus: 'active' | 'end_of_life' | 'deprecated' | 'extended';
  isDeprecated: boolean;
  impact: number;
  effort: number;
  priority: number;
  createdAt: string;
  updatedAt: string;
  lastScanned: string;
  resourceType: string;
  resourceId: string;
  recommendations: string[];
  recommendedAction: string; // Added for table display
  tags: string[];
  currentVersion?: string; // Added for version display
  latestVersion?: string; // Added for version display
  endOfLifeDate?: string; // Added for EOL calculation
  assetName?: string; // Added for display
  technology?: string; // Added for display
}

export interface SupportTimeline {
  id: string;
  name: string;
  version: string;
  currentVersion: string;
  releaseDate: string;
  endOfLife: string;
  status: 'active' | 'maintenance' | 'end_of_life';
  riskLevel: RiskLevel;
  lastChecked: string;
  updateAvailable: boolean;
  updateUrl?: string;
  documentationUrl?: string;
  notes?: string;
  
  // Additional properties for UI and functionality
  technology: string;
  supportEnd: string;
  extendedSupportEnd?: string;
  isExtendedSupport: boolean;
  daysUntilEOL: number;
  supportStatus: 'active' | 'security_updates' | 'end_of_life' | 'extended_support';
  recommendedAction?: string;
  impact?: 'low' | 'medium' | 'high' | 'critical';
}
