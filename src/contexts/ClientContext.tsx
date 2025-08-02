/**
 * ClientContext Index
 * Central export file for ClientContext
 */

// Components
export { ClientProvider } from './ClientContext/provider';

// Hooks
// eslint-disable-next-line react-refresh/only-export-components
export { useClient, withClient } from './ClientContext/hooks';

// Types
export type { Client, ClientContextType } from './ClientContext/types';
