import React from 'react';
import { Outlet } from 'react-router-dom';
import Sidebar from './Sidebar';
import ContextBreadcrumbs from './context/ContextBreadcrumbs';

const MainLayout: React.FC = () => {
  return (
    <div className="flex h-screen bg-gray-100 dark:bg-gray-900">
      <Sidebar />
      <div className="flex-1 flex flex-col overflow-hidden">
        <header className="bg-white dark:bg-gray-800 shadow-md p-4">
          <ContextBreadcrumbs />
        </header>
        <main className="flex-1 overflow-x-hidden overflow-y-auto bg-gray-100 dark:bg-gray-900">
          <div className="container mx-auto px-6 py-8">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
};

export default MainLayout; 