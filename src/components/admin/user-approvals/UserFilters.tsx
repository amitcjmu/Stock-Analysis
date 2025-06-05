import React from 'react';
import { Clock, Plus } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useNavigate } from 'react-router-dom';

interface UserFiltersProps {
  activeTab: 'pending' | 'active';
  pendingUsersCount: number;
  activeUsersCount: number;
  onTabChange: (tab: 'pending' | 'active') => void;
}

export const UserFilters: React.FC<UserFiltersProps> = ({
  activeTab,
  pendingUsersCount,
  activeUsersCount,
  onTabChange
}) => {
  const navigate = useNavigate();

  return (
    <>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">User Approvals</h1>
          <p className="text-muted-foreground">
            Manage user registration requests and platform access
          </p>
        </div>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <Clock className="w-4 h-4 text-orange-500" />
            <span className="text-sm font-medium">{pendingUsersCount} pending</span>
          </div>
          <Button onClick={() => navigate('/admin/users/create')}>
            <Plus className="w-4 h-4 mr-2" />
            Add New User
          </Button>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b">
        <nav className="-mb-px flex space-x-8">
          <button
            onClick={() => onTabChange('pending')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'pending'
                ? 'border-primary text-primary'
                : 'border-transparent text-muted-foreground hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Pending Approvals ({pendingUsersCount})
          </button>
          <button
            onClick={() => onTabChange('active')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'active'
                ? 'border-primary text-primary'
                : 'border-transparent text-muted-foreground hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Active Users ({activeUsersCount})
          </button>
        </nav>
      </div>
    </>
  );
}; 