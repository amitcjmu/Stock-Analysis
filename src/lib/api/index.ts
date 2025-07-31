// Re-export sixr API and all types
export * from './sixr';
export { sixrApi } from './sixr';

// Export the new simplified API client
export { apiClient, ApiError } from './apiClient';

// Export the generic API call function (backward compatibility)
export { apiCall, apiCallWithFallback } from '@/config/api';

// Default export for backward compatibility
export { sixrApi as default } from './sixr';
