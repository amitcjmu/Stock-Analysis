import React from 'react';
import { renderMarkdown } from './markdownUtils.tsx';

/**
 * Simple markdown renderer component for chat messages
 * Handles basic markdown formatting: bold, italic, code, bullet points, headings
 * 
 * Utility functions moved to ./markdownUtils.ts for react-refresh compatibility.
 */

interface MarkdownProps {
  content: string;
  className?: string;
}

export const Markdown: React.FC<MarkdownProps> = ({ content, className = '' }) => {
  return (
    <div className={`markdown-renderer ${className}`}>
      {renderMarkdown(content)}
    </div>
  );
};
