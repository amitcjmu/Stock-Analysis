/**
 * Subscription Hook Types
 * 
 * Hook types for real-time data subscriptions including
 * WebSocket, Server-Sent Events (SSE), and polling.
 */

// Subscription Hook Types
export interface UseSubscriptionParams<TData = unknown> {
  endpoint: string;
  protocol?: 'websocket' | 'sse' | 'polling';
  options?: SubscriptionOptions;
  enabled?: boolean;
  onData?: (data: TData) => void;
  onError?: (error: Error) => void;
  onConnect?: () => void;
  onDisconnect?: () => void;
  onReconnect?: () => void;
  transformData?: (rawData: unknown) => TData;
  filterData?: (data: TData) => boolean;
  bufferSize?: number;
  reconnectAttempts?: number;
  reconnectDelay?: number;
}

export interface UseSubscriptionReturn<TData = unknown> {
  data: TData | undefined;
  error: Error | null;
  isConnected: boolean;
  isConnecting: boolean;
  isReconnecting: boolean;
  connectionState: ConnectionState;
  lastMessage?: TData;
  messageCount: number;
  connect: () => void;
  disconnect: () => void;
  reconnect: () => void;
  send: (message: unknown) => void;
  subscribe: (event: string, handler: (data: unknown) => void) => () => void;
  unsubscribe: (event: string) => void;
}

// Supporting Types
export interface SubscriptionOptions {
  protocols?: string[];
  headers?: Record<string, string>;
  query?: Record<string, string>;
  timeout?: number;
  heartbeat?: boolean;
  heartbeatInterval?: number;
  compression?: boolean;
}

export type ConnectionState = 'connecting' | 'connected' | 'disconnecting' | 'disconnected' | 'reconnecting' | 'error';