import React from 'react'
import { useState } from 'react'
import { ClientFormData } from '../../types';
import { BasicInfoTab } from './BasicInfoTab';
import { BusinessContextTab } from './BusinessContextTab';
import { TechnicalPreferencesTab } from './TechnicalPreferencesTab';
import { AdvancedSettingsTab } from './AdvancedSettingsTab';

interface ClientFormProps {
  formData: ClientFormData;
  onFormChange: (field: keyof ClientFormData, value: ClientFormData[keyof ClientFormData]) => void;
}

type TabType = 'basic' | 'business' | 'technical' | 'advanced';

const tabs: Array<{ id: TabType; label: string }> = [
  { id: 'basic', label: 'Basic Information' },
  { id: 'business', label: 'Business Context' },
  { id: 'technical', label: 'Technical Preferences' },
  { id: 'advanced', label: 'Advanced Settings' }
];

export const ClientForm: React.FC<ClientFormProps> = React.memo(({ formData, onFormChange }) => {
  const [activeTab, setActiveTab] = useState<TabType>('basic');

  return (
    <div className="space-y-6 max-h-[600px] overflow-y-auto">
      {/* Tab Navigation */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`whitespace-nowrap py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === tab.id
                  ? 'border-indigo-500 text-indigo-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content */}
      {activeTab === 'basic' && (
        <BasicInfoTab formData={formData} onFormChange={onFormChange} />
      )}
      {activeTab === 'business' && (
        <BusinessContextTab formData={formData} onFormChange={onFormChange} />
      )}
      {activeTab === 'technical' && (
        <TechnicalPreferencesTab formData={formData} onFormChange={onFormChange} />
      )}
      {activeTab === 'advanced' && (
        <AdvancedSettingsTab formData={formData} onFormChange={onFormChange} />
      )}
    </div>
  );
});