import React from 'react';
import { Database, MapPin, Target, Brain } from 'lucide-react';

interface NavigationTabsProps {
  activeTab: string;
  onTabChange: (tabId: string) => void;
}

const NavigationTabs: React.FC<NavigationTabsProps> = ({ activeTab, onTabChange }) => {
  const tabs = [
    { id: 'data', label: 'Imported Data', icon: Database },
    { id: 'mappings', label: 'Field Mappings', icon: MapPin },
    { id: 'critical', label: 'Critical Attributes', icon: Target },
    { id: 'progress', label: 'Training Progress', icon: Brain }
  ];

  return (
    <div className="mb-6">
      <nav className="flex space-x-8">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          return (
            <button
              key={tab.id}
              onClick={() => onTabChange(tab.id)}
              className={`flex items-center space-x-2 px-4 py-2 rounded-lg font-medium ${
                activeTab === tab.id
                  ? 'bg-blue-600 text-white'
                  : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
              }`}
            >
              <Icon className="h-4 w-4" />
              <span>{tab.label}</span>
            </button>
          );
        })}
      </nav>
    </div>
  );
};

export default NavigationTabs; 