// Export the new simplified API client
export { apiClient, ApiError } from './apiClient';

// Export the generic API call function (backward compatibility)
export { apiCall, apiCallWithFallback } from '@/config/api';

// Note: sixrApi has been removed as part of Assessment Flow Migration Phase 5
// Use assessmentFlowApi from './assessmentFlow' instead
