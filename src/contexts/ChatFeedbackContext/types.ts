/**
 * ChatFeedback Context Types
 */

export interface ChatFeedbackContextType {
  isChatOpen: boolean;
  setIsChatOpen: (open: boolean) => void;
  currentPageName: string;
  breadcrumbPath: string;
}
