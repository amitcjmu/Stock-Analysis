import React, { createContext, useContext, useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';

interface ChatFeedbackContextType {
  isChatOpen: boolean;
  setIsChatOpen: (open: boolean) => void;
  currentPageName: string;
  breadcrumbPath: string;
}

const ChatFeedbackContext = createContext<ChatFeedbackContextType | undefined>(undefined);

// Utility function to generate human-readable page names and breadcrumbs from routes
const generatePageContext = (pathname: string): { pageName: string; breadcrumb: string } => {
  const segments = pathname.split('/').filter(Boolean);
  
  // Route to human-readable name mapping
  const routeNameMap: Record<string, string> = {
    '': 'Dashboard',
    'discovery': 'Discovery',
    'assess': 'Assess', 
    'plan': 'Plan',
    'execute': 'Execute',
    'modernize': 'Modernize',
    'decommission': 'Decommission',
    'finops': 'FinOps',
    'observability': 'Observability',
    'overview': 'Overview',
    'data-import': 'Data Import',
    'inventory': 'Asset Inventory',
    'dependencies': 'Dependencies',
    'data-cleansing': 'Data Cleansing',
    'attribute-mapping': 'Attribute Mapping',
    'tech-debt-analysis': 'Tech Debt Analysis',
    'treatment': 'Treatment Analysis',
    'waveplanning': 'Wave Planning',
    'roadmap': 'Migration Roadmap',
    'editor': 'Analysis Editor',
    'timeline': 'Migration Timeline',
    'resource': 'Resource Planning',
    'target': 'Target Architecture',
    'rehost': 'Rehost Execution',
    'replatform': 'Replatform Execution',
    'cutovers': 'Cutover Management',
    'reports': 'Execution Reports',
    'refactor': 'Refactor Projects',
    'rearchitect': 'Rearchitect Projects',
    'rewrite': 'Rewrite Projects',
    'progress': 'Modernization Progress',
    'planning': 'Decommission Planning',
    'dataretention': 'Data Retention',
    'execution': 'Decommission Execution',
    'validation': 'Decommission Validation',
    'cloud-comparison': 'Cloud Comparison',
    'savings-analysis': 'Savings Analysis',
    'cost-analysis': 'Cost Analysis',
    'wave-breakdown': 'Wave Breakdown',
    'cost-trends': 'Cost Trends',
    'budget-alerts': 'Budget Alerts'
  };

  if (segments.length === 0) {
    return { pageName: 'Dashboard', breadcrumb: 'Dashboard' };
  }

  // Generate breadcrumb path
  const breadcrumbParts = segments.map(segment => routeNameMap[segment] || segment);
  const breadcrumb = breadcrumbParts.join(' > ');
  
  // Current page name is the last segment
  const pageName = breadcrumbParts[breadcrumbParts.length - 1];

  return { pageName, breadcrumb };
};

export const ChatFeedbackProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [isChatOpen, setIsChatOpen] = useState(false);
  const location = useLocation();
  const [currentPageName, setCurrentPageName] = useState('Dashboard');
  const [breadcrumbPath, setBreadcrumbPath] = useState('Dashboard');

  useEffect(() => {
    const { pageName, breadcrumb } = generatePageContext(location.pathname);
    setCurrentPageName(pageName);
    setBreadcrumbPath(breadcrumb);
  }, [location.pathname]);

  const value: ChatFeedbackContextType = {
    isChatOpen,
    setIsChatOpen,
    currentPageName,
    breadcrumbPath
  };

  return (
    <ChatFeedbackContext.Provider value={value}>
      {children}
    </ChatFeedbackContext.Provider>
  );
};

export const useChatFeedback = (): ChatFeedbackContextType => {
  const context = useContext(ChatFeedbackContext);
  if (!context) {
    throw new Error('useChatFeedback must be used within a ChatFeedbackProvider');
  }
  return context;
}; 