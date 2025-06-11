import { User } from '@/contexts/AuthContext';

const API_BASE_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';

interface LoginResponse {
  user: User;
  token: string;
}

export const authService = {
  async login(email: string, password: string): Promise<LoginResponse> {
    try {
      // First try to authenticate against the database
      const response = await fetch(`${API_BASE_URL}/api/v1/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email, password }),
      });

      if (response.ok) {
        const result = await response.json();
        if (result.status === 'success' && result.user) {
          return {
            user: result.user,
            token: result.token,
          };
        }
      }

      // Fall back to demo authentication if database auth fails
      if (email === 'admin@aiforce.com' && password === 'admin123') {
        return {
          user: {
            id: '2a0de3df-7484-4fab-98b9-2ca126e2ab21',
            username: 'admin',
            email: 'admin@aiforce.com',
            full_name: 'Admin User',
            role: 'admin',
            status: 'approved',
            default_engagement_id: 'default-engagement-1',
          },
          token: 'demo-admin-token',
        };
      }

      throw new Error('Invalid email or password');
    } catch (error) {
      console.error('Login error:', error);
      throw new Error('Login failed. Please try again.');
    }
  },

  async getCurrentUser(): Promise<User> {
    const token = localStorage.getItem('auth_token');
    if (!token) {
      throw new Error('No authentication token found');
    }

    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/auth/me`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch user data');
      }

      const data = await response.json();
      return data.user;
    } catch (error) {
      console.error('Error fetching current user:', error);
      throw new Error('Failed to load user data');
    }
  },

  async register(userData: any): Promise<void> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/auth/register`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(userData),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.message || 'Registration failed');
      }
    } catch (error) {
      console.error('Registration error:', error);
      throw error;
    }
  },

  async logout(): Promise<void> {
    try {
      const token = localStorage.getItem('auth_token');
      if (token) {
        await fetch(`${API_BASE_URL}/api/v1/auth/logout`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
        });
      }
    } catch (error) {
      console.error('Logout error:', error);
      // Even if logout API fails, we still want to clear local storage
    } finally {
      localStorage.removeItem('auth_token');
      localStorage.removeItem('user_data');
      localStorage.removeItem('selectedEngagementId');
      localStorage.removeItem('selectedSessionId');
    }
  },
};
