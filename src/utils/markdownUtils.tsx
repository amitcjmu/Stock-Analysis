import React from 'react';

/**
 * Simple markdown renderer utility functions
 * Handles basic markdown formatting: bold, italic, code, bullet points, headings
 *
 * Separated from component file to maintain react-refresh compatibility.
 */

const formatInlineMarkdown = (text: string): React.ReactElement => {
  // Handle inline code `code`
  text = text.replace(/`([^`]+)`/g, '<code class="bg-gray-200 px-1 rounded text-sm font-mono">$1</code>');

  // Handle bold **text**
  text = text.replace(/\*\*([^*]+)\*\*/g, '<strong class="font-bold">$1</strong>');

  // Handle italic *text*
  text = text.replace(/\*([^*]+)\*/g, '<em class="italic">$1</em>');

  // Return as JSX
  return <span dangerouslySetInnerHTML={{ __html: text }} />;
};

export const renderMarkdown = (text: string): React.ReactElement => {
  // Split text into lines for processing
  const lines = text.split('\n');
  const elements: React.ReactElement[] = [];

  let listItems: string[] = [];
  let inList = false;

  lines.forEach((line, index) => {
    const trimmedLine = line.trim();

    // Handle bullet points
    if (trimmedLine.startsWith('• ') || trimmedLine.startsWith('* ') || trimmedLine.startsWith('- ')) {
      const listText = trimmedLine.substring(2);
      listItems.push(listText);
      inList = true;
      return;
    }

    // If we were in a list and this line doesn't continue it, render the list
    if (inList && !trimmedLine.startsWith('• ') && !trimmedLine.startsWith('* ') && !trimmedLine.startsWith('- ')) {
      elements.push(
        <ul key={`list-${index}`} className="list-disc list-inside my-2 ml-4">
          {listItems.map((item, i) => (
            <li key={i} className="mb-1">
              {formatInlineMarkdown(item)}
            </li>
          ))}
        </ul>
      );
      listItems = [];
      inList = false;
    }

    // Handle headings
    if (trimmedLine.startsWith('**') && trimmedLine.endsWith('**') && trimmedLine.length > 4) {
      const headingText = trimmedLine.slice(2, -2);
      elements.push(
        <h3 key={index} className="font-bold text-lg my-2">
          {formatInlineMarkdown(headingText)}
        </h3>
      );
      return;
    }

    // Handle regular paragraphs
    if (trimmedLine) {
      elements.push(
        <p key={index} className="mb-2">
          {formatInlineMarkdown(trimmedLine)}
        </p>
      );
    } else {
      // Empty line - add spacing
      elements.push(<br key={index} />);
    }
  });

  // Handle any remaining list items
  if (inList && listItems.length > 0) {
    elements.push(
      <ul key="final-list" className="list-disc list-inside my-2 ml-4">
        {listItems.map((item, i) => (
          <li key={i} className="mb-1">
            {formatInlineMarkdown(item)}
          </li>
        ))}
      </ul>
    );
  }

  return <div className="markdown-content">{elements}</div>;
};
