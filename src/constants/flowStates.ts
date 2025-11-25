/**
 * Flow state constants for frontend components.
 * Mirrors backend flow constants with UI-specific additions.
 */

// Flow Status Constants
export const FLOW_STATUSES = {
  PENDING: 'pending',
  INITIALIZING: 'initializing',
  RUNNING: 'running',
  PAUSED: 'paused',
  WAITING: 'waiting',
  COMPLETED: 'completed',
  FAILED: 'failed',
  CANCELLED: 'cancelled',
  TIMEOUT: 'timeout',
  RETRY: 'retry',
  ROLLBACK: 'rollback',
  ARCHIVED: 'archived'
} as const;

export type FlowStatus = typeof FLOW_STATUSES[keyof typeof FLOW_STATUSES];

// Flow Phases Constants
export const FLOW_PHASES = {
  INITIALIZATION: 'initialization',
  DATA_IMPORT: 'data_import',
  DATA_VALIDATION: 'data_validation',
  FIELD_MAPPING: 'field_mapping',
  DATA_CLEANSING: 'data_cleansing',
  ASSET_INVENTORY: 'asset_inventory',
  DEPENDENCY_ANALYSIS: 'dependency_analysis',
  TECH_DEBT_ANALYSIS: 'tech_debt_analysis',
  ASSESSMENT: 'assessment',
  PLANNING: 'planning',
  EXECUTION: 'execution',
  MODERNIZATION: 'modernization',
  FINALIZATION: 'finalization',
  CLEANUP: 'cleanup'
} as const;

export type FlowPhase = typeof FLOW_PHASES[keyof typeof FLOW_PHASES];

// Flow Types Constants
export const FLOW_TYPES = {
  DISCOVERY: 'discovery',
  ASSESSMENT: 'assessment',
  PLANNING: 'planning',
  EXECUTION: 'execution',
  MODERNIZATION: 'modernization',
  FINOPS: 'finops',
  OBSERVABILITY: 'observability',
  DECOMMISSION: 'decommission'
} as const;

export type FlowType = typeof FLOW_TYPES[keyof typeof FLOW_TYPES];

// Flow Priority Constants
export const FLOW_PRIORITIES = {
  LOW: 'low',
  NORMAL: 'normal',
  HIGH: 'high',
  CRITICAL: 'critical',
  URGENT: 'urgent'
} as const;

export type FlowPriority = typeof FLOW_PRIORITIES[keyof typeof FLOW_PRIORITIES];

// UI-specific Flow Status Mappings
export const FLOW_STATUS_COLORS = {
  [FLOW_STATUSES.PENDING]: 'gray',
  [FLOW_STATUSES.INITIALIZING]: 'blue',
  [FLOW_STATUSES.RUNNING]: 'green',
  [FLOW_STATUSES.PAUSED]: 'yellow',
  [FLOW_STATUSES.WAITING]: 'orange',
  [FLOW_STATUSES.COMPLETED]: 'green',
  [FLOW_STATUSES.FAILED]: 'red',
  [FLOW_STATUSES.CANCELLED]: 'gray',
  [FLOW_STATUSES.TIMEOUT]: 'red',
  [FLOW_STATUSES.RETRY]: 'yellow',
  [FLOW_STATUSES.ROLLBACK]: 'orange',
  [FLOW_STATUSES.ARCHIVED]: 'gray'
} as const;

export const FLOW_STATUS_ICONS = {
  [FLOW_STATUSES.PENDING]: 'clock',
  [FLOW_STATUSES.INITIALIZING]: 'loading',
  [FLOW_STATUSES.RUNNING]: 'play',
  [FLOW_STATUSES.PAUSED]: 'pause',
  [FLOW_STATUSES.WAITING]: 'clock',
  [FLOW_STATUSES.COMPLETED]: 'check-circle',
  [FLOW_STATUSES.FAILED]: 'x-circle',
  [FLOW_STATUSES.CANCELLED]: 'x',
  [FLOW_STATUSES.TIMEOUT]: 'clock',
  [FLOW_STATUSES.RETRY]: 'refresh-cw',
  [FLOW_STATUSES.ROLLBACK]: 'undo',
  [FLOW_STATUSES.ARCHIVED]: 'archive'
} as const;

export const FLOW_STATUS_LABELS = {
  [FLOW_STATUSES.PENDING]: 'Pending',
  [FLOW_STATUSES.INITIALIZING]: 'Initializing',
  [FLOW_STATUSES.RUNNING]: 'Running',
  [FLOW_STATUSES.PAUSED]: 'Paused',
  [FLOW_STATUSES.WAITING]: 'Waiting',
  [FLOW_STATUSES.COMPLETED]: 'Completed',
  [FLOW_STATUSES.FAILED]: 'Failed',
  [FLOW_STATUSES.CANCELLED]: 'Cancelled',
  [FLOW_STATUSES.TIMEOUT]: 'Timed Out',
  [FLOW_STATUSES.RETRY]: 'Retrying',
  [FLOW_STATUSES.ROLLBACK]: 'Rolling Back',
  [FLOW_STATUSES.ARCHIVED]: 'Archived'
} as const;

// Flow Phase UI Mappings
export const FLOW_PHASE_COLORS = {
  [FLOW_PHASES.INITIALIZATION]: 'blue',
  [FLOW_PHASES.DATA_IMPORT]: 'purple',
  [FLOW_PHASES.DATA_VALIDATION]: 'indigo',
  [FLOW_PHASES.FIELD_MAPPING]: 'cyan',
  [FLOW_PHASES.DATA_CLEANSING]: 'teal',
  [FLOW_PHASES.ASSET_INVENTORY]: 'green',
  [FLOW_PHASES.DEPENDENCY_ANALYSIS]: 'yellow',
  [FLOW_PHASES.TECH_DEBT_ANALYSIS]: 'orange',
  [FLOW_PHASES.ASSESSMENT]: 'red',
  [FLOW_PHASES.PLANNING]: 'pink',
  [FLOW_PHASES.EXECUTION]: 'emerald',
  [FLOW_PHASES.MODERNIZATION]: 'violet',
  [FLOW_PHASES.FINALIZATION]: 'slate',
  [FLOW_PHASES.CLEANUP]: 'gray'
} as const;

export const FLOW_PHASE_ICONS = {
  [FLOW_PHASES.INITIALIZATION]: 'settings',
  [FLOW_PHASES.DATA_IMPORT]: 'upload',
  [FLOW_PHASES.DATA_VALIDATION]: 'check-square',
  [FLOW_PHASES.FIELD_MAPPING]: 'link',
  [FLOW_PHASES.DATA_CLEANSING]: 'filter',
  [FLOW_PHASES.ASSET_INVENTORY]: 'package',
  [FLOW_PHASES.DEPENDENCY_ANALYSIS]: 'git-branch',
  [FLOW_PHASES.TECH_DEBT_ANALYSIS]: 'alert-triangle',
  [FLOW_PHASES.ASSESSMENT]: 'clipboard',
  [FLOW_PHASES.PLANNING]: 'map',
  [FLOW_PHASES.EXECUTION]: 'play',
  [FLOW_PHASES.MODERNIZATION]: 'zap',
  [FLOW_PHASES.FINALIZATION]: 'check',
  [FLOW_PHASES.CLEANUP]: 'trash-2'
} as const;

export const FLOW_PHASE_LABELS = {
  [FLOW_PHASES.INITIALIZATION]: 'Initialization',
  [FLOW_PHASES.DATA_IMPORT]: 'Data Import',
  [FLOW_PHASES.DATA_VALIDATION]: 'Data Validation',
  [FLOW_PHASES.FIELD_MAPPING]: 'Field Mapping',
  [FLOW_PHASES.DATA_CLEANSING]: 'Data Cleansing',
  [FLOW_PHASES.ASSET_INVENTORY]: 'Asset Inventory',
  [FLOW_PHASES.DEPENDENCY_ANALYSIS]: 'Dependency Analysis',
  [FLOW_PHASES.TECH_DEBT_ANALYSIS]: 'Tech Debt Analysis',
  [FLOW_PHASES.ASSESSMENT]: 'Assessment',
  [FLOW_PHASES.PLANNING]: 'Planning',
  [FLOW_PHASES.EXECUTION]: 'Execution',
  [FLOW_PHASES.MODERNIZATION]: 'Modernization',
  [FLOW_PHASES.FINALIZATION]: 'Finalization',
  [FLOW_PHASES.CLEANUP]: 'Cleanup'
} as const;

// Flow Type UI Mappings
export const FLOW_TYPE_COLORS = {
  [FLOW_TYPES.DISCOVERY]: 'blue',
  [FLOW_TYPES.ASSESSMENT]: 'green',
  [FLOW_TYPES.PLANNING]: 'purple',
  [FLOW_TYPES.EXECUTION]: 'orange',
  [FLOW_TYPES.MODERNIZATION]: 'red',
  [FLOW_TYPES.FINOPS]: 'yellow',
  [FLOW_TYPES.OBSERVABILITY]: 'cyan',
  [FLOW_TYPES.DECOMMISSION]: 'gray'
} as const;

export const FLOW_TYPE_ICONS = {
  [FLOW_TYPES.DISCOVERY]: 'search',
  [FLOW_TYPES.ASSESSMENT]: 'clipboard',
  [FLOW_TYPES.PLANNING]: 'map',
  [FLOW_TYPES.EXECUTION]: 'play',
  [FLOW_TYPES.MODERNIZATION]: 'zap',
  [FLOW_TYPES.FINOPS]: 'dollar-sign',
  [FLOW_TYPES.OBSERVABILITY]: 'eye',
  [FLOW_TYPES.DECOMMISSION]: 'trash-2'
} as const;

export const FLOW_TYPE_LABELS = {
  [FLOW_TYPES.DISCOVERY]: 'Discovery',
  [FLOW_TYPES.ASSESSMENT]: 'Assessment',
  [FLOW_TYPES.PLANNING]: 'Planning',
  [FLOW_TYPES.EXECUTION]: 'Execution',
  [FLOW_TYPES.MODERNIZATION]: 'Modernization',
  [FLOW_TYPES.FINOPS]: 'FinOps',
  [FLOW_TYPES.OBSERVABILITY]: 'Observability',
  [FLOW_TYPES.DECOMMISSION]: 'Decommission'
} as const;

// Flow Priority UI Mappings
export const FLOW_PRIORITY_COLORS = {
  [FLOW_PRIORITIES.LOW]: 'gray',
  [FLOW_PRIORITIES.NORMAL]: 'blue',
  [FLOW_PRIORITIES.HIGH]: 'yellow',
  [FLOW_PRIORITIES.CRITICAL]: 'orange',
  [FLOW_PRIORITIES.URGENT]: 'red'
} as const;

export const FLOW_PRIORITY_LABELS = {
  [FLOW_PRIORITIES.LOW]: 'Low',
  [FLOW_PRIORITIES.NORMAL]: 'Normal',
  [FLOW_PRIORITIES.HIGH]: 'High',
  [FLOW_PRIORITIES.CRITICAL]: 'Critical',
  [FLOW_PRIORITIES.URGENT]: 'Urgent'
} as const;

// Flow State Utilities
export const ACTIVE_STATUSES = [
  FLOW_STATUSES.INITIALIZING,
  FLOW_STATUSES.RUNNING,
  FLOW_STATUSES.WAITING,
  FLOW_STATUSES.RETRY
] as const;

export const TERMINAL_STATUSES = [
  FLOW_STATUSES.COMPLETED,
  FLOW_STATUSES.FAILED,
  FLOW_STATUSES.CANCELLED,
  FLOW_STATUSES.ARCHIVED,
  'aborted', // Additional terminal state not in FLOW_STATUSES enum
  'deleted'  // Additional terminal state not in FLOW_STATUSES enum
] as const;

/**
 * Array of all terminal flow states as lowercase strings.
 * Use this for case-insensitive status checks.
 */
export const TERMINAL_STATES = [
  'completed',
  'cancelled',
  'failed',
  'aborted',
  'deleted',
  'archived'
] as const;

export const ERROR_STATUSES = [
  FLOW_STATUSES.FAILED,
  FLOW_STATUSES.TIMEOUT,
  FLOW_STATUSES.ROLLBACK
] as const;

export const SUCCESS_STATUSES = [
  FLOW_STATUSES.COMPLETED
] as const;

// Helper functions for flow state checks
export const isActiveStatus = (status: FlowStatus): boolean => {
  return (ACTIVE_STATUSES as readonly FlowStatus[]).includes(status);
};

/**
 * Check if a flow status (as string) is in a terminal state.
 * Case-insensitive check for compatibility with various API responses.
 * This is the single source of truth for terminal state checking.
 *
 * @param status - Flow status string (can be any case)
 * @returns true if the status is a terminal state
 */
export const isFlowTerminal = (status: string | undefined | null): boolean => {
  if (!status) return false;
  return TERMINAL_STATES.includes(status.toLowerCase() as typeof TERMINAL_STATES[number]);
};

/**
 * Check if a FlowStatus enum value is in a terminal state.
 * Delegates to isFlowTerminal to ensure consistent logic and single source of truth.
 *
 * @param status - FlowStatus enum value
 * @returns true if the status is a terminal state
 */
export const isTerminalStatus = (status: FlowStatus): boolean => {
  return isFlowTerminal(status);
};

export const isErrorStatus = (status: FlowStatus): boolean => {
  return (ERROR_STATUSES as readonly FlowStatus[]).includes(status);
};

export const isSuccessStatus = (status: FlowStatus): boolean => {
  return (SUCCESS_STATUSES as readonly FlowStatus[]).includes(status);
};

// Flow progress calculation
export const PHASE_WEIGHTS = {
  [FLOW_PHASES.INITIALIZATION]: 5,
  [FLOW_PHASES.DATA_IMPORT]: 15,
  [FLOW_PHASES.DATA_VALIDATION]: 10,
  [FLOW_PHASES.FIELD_MAPPING]: 15,
  [FLOW_PHASES.DATA_CLEANSING]: 20,
  [FLOW_PHASES.ASSET_INVENTORY]: 15,
  [FLOW_PHASES.DEPENDENCY_ANALYSIS]: 15,
  [FLOW_PHASES.TECH_DEBT_ANALYSIS]: 15,
  [FLOW_PHASES.ASSESSMENT]: 25,
  [FLOW_PHASES.PLANNING]: 20,
  [FLOW_PHASES.EXECUTION]: 30,
  [FLOW_PHASES.MODERNIZATION]: 25,
  [FLOW_PHASES.FINALIZATION]: 5,
  [FLOW_PHASES.CLEANUP]: 5
} as const;
