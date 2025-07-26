// Path aliases for commonly used directories
export const Paths = {
  hooks: {
    useClients: '../../hooks/useClients',
    useEngagements: '../../hooks/useEngagements',
    useDiscoveryDashboard: '../../hooks/useDiscoveryDashboard',
  },
  contexts: {
    AuthContext: '../../contexts/AuthContext',
  },
  components: {
    ui: '../../components/ui',
  },
} as const;

// Helper to get the correct import path
export const getImportPath = (path: string): any => {
  // Convert @ alias to relative path if needed
  if (path.startsWith('@/')) {
    return path.replace('@/', '../');
  }
  return path;
};
