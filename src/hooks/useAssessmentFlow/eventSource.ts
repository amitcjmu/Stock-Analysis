/**
 * Event Source Service
 *
 * Service for handling real-time updates via Server-Sent Events.
 */

// API base URL
const getApiBase = (): string => {
  // Force proxy usage for development - Docker container on port 8081
  if (typeof window !== 'undefined' && window.location.port === '8081') {
    return '';
  }

  return process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
};

const API_BASE = getApiBase();

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
