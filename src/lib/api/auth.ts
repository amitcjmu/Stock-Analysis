// API Configuration
const getApiBaseUrl = (): string => {
  // First, check for environment-specific variables
  const backendUrl = import.meta.env.VITE_BACKEND_URL || import.meta.env.VITE_API_BASE_URL;
  
  if (backendUrl) {
    return backendUrl;
  }
  
  // In development mode, use relative path to utilize Vite proxy
  if (import.meta.env.DEV || import.meta.env.MODE === 'development') {
    return '';  // Empty string means use same origin with proxy
  }
  
  // For production without explicit backend URL, use same origin
  console.warn('No VITE_BACKEND_URL environment variable found. Using same origin as fallback.');
  return window.location.origin;
};

const API_BASE_URL = getApiBaseUrl();

// Types
export interface User {
  id: string;
  username: string;
  email: string;
  full_name: string;
  role: string;
  status: string;
  organization: string;
  role_description: string;
  client_account_id?: string; // From user_associations[0].client_account_id
  client_accounts: Array<{
    id: string;
    name: string;
    role: string;
  }>;
}

export interface Token {
  access_token: string;
  token_type: string;
}

export interface LoginResponse {
  status: string;
  message: string;
  user: User | null;
  token: Token | null;
}

// Auth API
export const authApi = {
  async login(email: string, password: string): Promise<LoginResponse> {
    const response = await fetch(`${API_BASE_URL}/api/v1/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ email, password }),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Login failed');
    }

    return response.json();
  },

  async register(userData: unknown): Promise<any> {
    const response = await fetch(`${API_BASE_URL}/api/v1/auth/register`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(userData),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Registration failed');
    }

    return response.json();
  },

  async validateToken(token: string): Promise<User | null> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/context/me`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        return null;
      }

      const data = await response.json();
      return data.user || null;
    } catch (error) {
      console.error('Token validation error:', error);
      return null;
    }
  },

  async changePassword(userId: string, currentPassword: string, newPassword: string): Promise<any> {
    const response = await fetch(`${API_BASE_URL}/api/v1/auth/change-password`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        user_id: userId,
        current_password: currentPassword,
        new_password: newPassword,
      }),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Password change failed');
    }

    return response.json();
  },
};