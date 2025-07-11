import React from 'react';
import { Link } from 'react-router-dom';
import { User } from 'lucide-react';
import { AuthenticationIndicatorProps } from './types';

const AuthenticationIndicator: React.FC<AuthenticationIndicatorProps> = ({
  isAuthenticated,
  user
}) => {
  if (!isAuthenticated) {
    return null;
  }

  return (
    <div className="mb-3">
      <Link
        to="/profile"
        className="flex items-center space-x-3 px-3 py-2 rounded-lg transition-colors duration-200 text-gray-300 hover:bg-gray-700 hover:text-white"
      >
        <User className="h-4 w-4" />
        <span className="text-sm">User Profile</span>
      </Link>
    </div>
  );
};

export default AuthenticationIndicator;