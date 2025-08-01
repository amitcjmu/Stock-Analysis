import React from 'react'
import { useState } from 'react'
import { useEffect } from 'react'
import { useLocation } from 'react-router-dom';
import type { ChatFeedbackContextType } from './types';
import { ChatFeedbackContext } from './context';
import { generatePageContext } from './utils';

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


// Re-export types for convenience
export type { ChatFeedbackContextType } from './types';
