/**
 * Example usage of the updated API client with properly typed interfaces
 * This file demonstrates how to use the new shared types and API client
 */

import type { 
  ApiResponse, 
  ApiError,
  PaginatedResponse
} from '../utils/api';
import { createApiClient } from '../utils/api';

// Example: Discovery Flow API Usage
interface DiscoveryFlowData {
  flowId: string;
  status: 'pending' | 'in_progress' | 'completed' | 'failed';
  results: DiscoveryResult[];
  metadata: {
    createdAt: string;
    updatedAt: string;
    createdBy: string;
  };
}

interface DiscoveryResult {
  id: string;
  type: string;
  data: Record<string, unknown>;
}

interface UserData {
  id: string;
  name: string;
  email: string;
  role: string;
}

// Example API client usage
const apiClient = createApiClient({
  baseURL: process.env.NEXT_PUBLIC_API_URL,
  timeout: 30000,
  retries: 3
});

// Example: Properly typed API responses
export async function getDiscoveryFlow(flowId: string): Promise<DiscoveryFlowData> {
  try {
    const response: ApiResponse<DiscoveryFlowData> = await apiClient.get(
      `/api/v1/discovery/flows/${flowId}`
    );
    
    if (response.success) {
      return response.data;
    } else {
      throw new Error(response.error?.message || 'Failed to fetch discovery flow');
    }
  } catch (error) {
    console.error('Error fetching discovery flow:', error);
    throw error;
  }
}

// Example: Paginated response handling
export async function getUsers(page: number = 1, pageSize: number = 10): Promise<{
  users: UserData[];
  pagination: {
    total_items: number;
    page: number;
    page_size: number;
    total_pages: number;
    has_next: boolean;
    has_previous: boolean;
  };
}> {
  try {
    const response: ApiResponse<UserData[]> = await apiClient.get('/api/v1/users', {
      params: {
        page,
        page_size: pageSize
      }
    });
    
    if (response.success) {
      // For this example, we'll assume the response includes pagination info
      const paginationData = response.pagination;
      return {
        users: response.data,
        pagination: {
          total_items: paginationData?.total || 0,
          page: paginationData?.page || page,
          page_size: paginationData?.pageSize || pageSize,
          total_pages: paginationData?.totalPages || 1,
          has_next: paginationData?.hasNext || false,
          has_previous: paginationData?.hasPrevious || false
        }
      };
    } else {
      throw new Error(response.error?.message || 'Failed to fetch users');
    }
  } catch (error) {
    console.error('Error fetching users:', error);
    throw error;
  }
}

// Example: Error handling with proper types
export async function createUser(userData: Omit<UserData, 'id'>): Promise<UserData> {
  try {
    const response: ApiResponse<UserData> = await apiClient.post('/api/v1/users', userData);
    
    if (response.success) {
      return response.data;
    } else {
      // Handle specific error types
      if (response.error?.code === 'VALIDATION_ERROR') {
        const validationError = response.error as ApiError;
        throw new Error(`Validation failed: ${validationError.message}`);
      }
      throw new Error(response.error?.message || 'Failed to create user');
    }
  } catch (error) {
    console.error('Error creating user:', error);
    throw error;
  }
}

// Example: Multi-tenant context usage
export async function setupMultiTenantClient(
  clientAccountId: string, 
  engagementId: string, 
  userId: string
): Promise<void> {
  apiClient.setMultiTenantContext({
    clientAccountId,
    engagementId,
    userId,
    userRole: 'admin',
    permissions: ['read', 'write', 'admin']
  });
}

// Example: File upload with proper typing
export async function uploadFile(file: File, metadata?: Record<string, unknown>): Promise<{
  fileId: string;
  url: string;
}> {
  try {
    const response = await apiClient.upload('/api/v1/files/upload', {
      file,
      fieldName: 'document',
      data: metadata,
      onProgress: (progress) => {
        console.log(`Upload progress: ${progress.percentage}%`);
      }
    });
    
    if (response.success) {
      return response.data as { fileId: string; url: string; };
    } else {
      throw new Error(response.error?.message || 'Upload failed');
    }
  } catch (error) {
    console.error('Error uploading file:', error);
    throw error;
  }
}

// Example: Batch operations
export async function batchCreateUsers(users: Array<Omit<UserData, 'id'>>): Promise<Array<UserData>> {
  const requests = users.map((user, index) => ({
    id: `user-${index}`,
    method: 'POST',
    url: '/api/v1/users',
    data: user
  }));
  
  try {
    const responses = await apiClient.batch(requests);
    const successfulUsers: UserData[] = [];
    
    responses.forEach((response, index) => {
      if (response.status === 200 && response.data) {
        successfulUsers.push((response.data as ApiResponse<UserData>).data);
      } else {
        console.error(`Failed to create user ${index}:`, response.error);
      }
    });
    
    return successfulUsers;
  } catch (error) {
    console.error('Error in batch user creation:', error);
    throw error;
  }
}