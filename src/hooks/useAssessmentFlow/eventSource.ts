/**
 * Event Source Service
 * 
 * Service for handling real-time updates via Server-Sent Events.
 */

// API base URL
const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Event source service for real-time updates
export const eventSourceService = {
  subscribe(url: string, options: {
    onMessage: (event: MessageEvent) => void;
    onError: (error: Event) => void;
  }): EventSource {
    const eventSource = new EventSource(`${API_BASE}${url}`);
    
    eventSource.onmessage = options.onMessage;
    eventSource.onerror = options.onError;
    
    return eventSource;
  }
};