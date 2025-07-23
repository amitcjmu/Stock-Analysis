import React from 'react';
import { MessageCircle } from 'lucide-react';
import { useChatFeedback } from '../contexts/ChatFeedbackContext';
import type ChatInterface from './ui/ChatInterface';

const GlobalChatFeedback: React.FC = () => {
  const { isChatOpen, setIsChatOpen, currentPageName, breadcrumbPath } = useChatFeedback();

  return (
    <>
      {/* Floating Chat/Feedback Button */}
      <button
        onClick={() => setIsChatOpen(true)}
        className="fixed bottom-6 right-6 bg-blue-600 text-white p-4 rounded-full shadow-lg hover:bg-blue-700 transition-colors z-40"
        title="Chat with AI Assistant or Submit Feedback"
        aria-label="Open AI Assistant and Feedback"
      >
        <MessageCircle className="h-6 w-6" />
      </button>
      
      {/* Chat Interface */}
      <ChatInterface 
        isOpen={isChatOpen} 
        onClose={() => setIsChatOpen(false)}
        currentPage={currentPageName}
        breadcrumbPath={breadcrumbPath}
      />
    </>
  );
};

export default GlobalChatFeedback; 