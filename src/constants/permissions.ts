/**
 * Permission constants for role-based access control
 */

export const PERMISSIONS = {
  // System permissions
  SYSTEM: {
    ADMIN: 'system.admin',
    MANAGE_USERS: 'system.manage_users',
    MANAGE_CLIENTS: 'system.manage_clients',
    MANAGE_ENGAGEMENTS: 'system.manage_engagements',
    VIEW_LOGS: 'system.view_logs',
    MANAGE_SETTINGS: 'system.manage_settings'
  },
  
  // Discovery permissions
  DISCOVERY: {
    VIEW: 'discovery.view',
    CREATE: 'discovery.create',
    EDIT: 'discovery.edit',
    DELETE: 'discovery.delete',
    ANALYZE: 'discovery.analyze',
    EXPORT: 'discovery.export',
    MANAGE_ASSETS: 'discovery.manage_assets',
    MANAGE_APPLICATIONS: 'discovery.manage_applications'
  },
  
  // Collection permissions
  COLLECTION: {
    VIEW: 'collection.view',
    CREATE: 'collection.create',
    EDIT: 'collection.edit',
    DELETE: 'collection.delete',
    UPLOAD: 'collection.upload',
    MANAGE_FLOWS: 'collection.manage_flows',
    EXECUTE_FLOWS: 'collection.execute_flows'
  },
  
  // Assessment permissions
  ASSESSMENT: {
    VIEW: 'assessment.view',
    CREATE: 'assessment.create',
    EDIT: 'assessment.edit',
    DELETE: 'assessment.delete',
    EXECUTE: 'assessment.execute',
    APPROVE: 'assessment.approve'
  },
  
  // Monitoring permissions
  MONITORING: {
    VIEW: 'monitoring.view',
    VIEW_ALL_AGENTS: 'monitoring.view_all_agents',
    MANAGE_AGENTS: 'monitoring.manage_agents',
    VIEW_METRICS: 'monitoring.view_metrics',
    EXPORT_METRICS: 'monitoring.export_metrics'
  },
  
  // Agent permissions
  AGENT: {
    VIEW: 'agent.view',
    EXECUTE: 'agent.execute',
    CONFIGURE: 'agent.configure',
    TRAIN: 'agent.train',
    VIEW_LEARNING: 'agent.view_learning'
  },
  
  // Report permissions
  REPORT: {
    VIEW: 'report.view',
    CREATE: 'report.create',
    EDIT: 'report.edit',
    DELETE: 'report.delete',
    EXPORT: 'report.export',
    SHARE: 'report.share'
  },
  
  // Client permissions
  CLIENT: {
    VIEW: 'client.view',
    EDIT: 'client.edit',
    MANAGE_USERS: 'client.manage_users',
    MANAGE_ENGAGEMENTS: 'client.manage_engagements'
  },
  
  // Engagement permissions
  ENGAGEMENT: {
    VIEW: 'engagement.view',
    EDIT: 'engagement.edit',
    MANAGE_USERS: 'engagement.manage_users',
    MANAGE_WORKFLOWS: 'engagement.manage_workflows'
  }
} as const;

// Permission groups for roles
export const PERMISSION_GROUPS = {
  ADMIN: [
    ...Object.values(PERMISSIONS.SYSTEM),
    ...Object.values(PERMISSIONS.DISCOVERY),
    ...Object.values(PERMISSIONS.COLLECTION),
    ...Object.values(PERMISSIONS.ASSESSMENT),
    ...Object.values(PERMISSIONS.MONITORING),
    ...Object.values(PERMISSIONS.AGENT),
    ...Object.values(PERMISSIONS.REPORT),
    ...Object.values(PERMISSIONS.CLIENT),
    ...Object.values(PERMISSIONS.ENGAGEMENT)
  ],
  
  CLIENT_ADMIN: [
    PERMISSIONS.CLIENT.VIEW,
    PERMISSIONS.CLIENT.EDIT,
    PERMISSIONS.CLIENT.MANAGE_USERS,
    PERMISSIONS.CLIENT.MANAGE_ENGAGEMENTS,
    ...Object.values(PERMISSIONS.ENGAGEMENT),
    ...Object.values(PERMISSIONS.DISCOVERY),
    ...Object.values(PERMISSIONS.COLLECTION),
    ...Object.values(PERMISSIONS.ASSESSMENT),
    PERMISSIONS.MONITORING.VIEW,
    PERMISSIONS.MONITORING.VIEW_METRICS,
    ...Object.values(PERMISSIONS.REPORT)
  ],
  
  ENGAGEMENT_LEAD: [
    PERMISSIONS.ENGAGEMENT.VIEW,
    PERMISSIONS.ENGAGEMENT.EDIT,
    PERMISSIONS.ENGAGEMENT.MANAGE_WORKFLOWS,
    ...Object.values(PERMISSIONS.DISCOVERY),
    ...Object.values(PERMISSIONS.COLLECTION),
    ...Object.values(PERMISSIONS.ASSESSMENT),
    PERMISSIONS.MONITORING.VIEW,
    PERMISSIONS.MONITORING.VIEW_METRICS,
    ...Object.values(PERMISSIONS.REPORT)
  ],
  
  ANALYST: [
    PERMISSIONS.DISCOVERY.VIEW,
    PERMISSIONS.DISCOVERY.CREATE,
    PERMISSIONS.DISCOVERY.EDIT,
    PERMISSIONS.DISCOVERY.ANALYZE,
    PERMISSIONS.COLLECTION.VIEW,
    PERMISSIONS.COLLECTION.CREATE,
    PERMISSIONS.COLLECTION.EDIT,
    PERMISSIONS.COLLECTION.UPLOAD,
    PERMISSIONS.ASSESSMENT.VIEW,
    PERMISSIONS.ASSESSMENT.CREATE,
    PERMISSIONS.ASSESSMENT.EDIT,
    PERMISSIONS.MONITORING.VIEW,
    PERMISSIONS.REPORT.VIEW,
    PERMISSIONS.REPORT.CREATE
  ],
  
  VIEWER: [
    PERMISSIONS.DISCOVERY.VIEW,
    PERMISSIONS.COLLECTION.VIEW,
    PERMISSIONS.ASSESSMENT.VIEW,
    PERMISSIONS.MONITORING.VIEW,
    PERMISSIONS.REPORT.VIEW,
    PERMISSIONS.CLIENT.VIEW,
    PERMISSIONS.ENGAGEMENT.VIEW
  ]
} as const;

// Default permissions for new users
export const DEFAULT_PERMISSIONS = PERMISSION_GROUPS.VIEWER;