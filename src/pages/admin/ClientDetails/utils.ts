/**
 * Utility functions for ClientDetails component
 * Generated with CC for UI modularization
 */

export const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });
};

export const getProviderLabel = (provider: string) => {
  const providerMap: Record<string, string> = {
    'aws': 'Amazon Web Services (AWS)',
    'azure': 'Microsoft Azure',
    'gcp': 'Google Cloud Platform (GCP)',
    'multi_cloud': 'Multi-Cloud Strategy',
    'hybrid': 'Hybrid Cloud',
    'private_cloud': 'Private Cloud'
  };
  return providerMap[provider] || provider;
};

export const getPriorityLabel = (priority: string) => {
  const priorityMap: Record<string, string> = {
    'cost_reduction': 'Cost Reduction',
    'agility_speed': 'Agility & Speed',
    'security_compliance': 'Security & Compliance',
    'innovation': 'Innovation',
    'scalability': 'Scalability',
    'reliability': 'Reliability'
  };
  return priorityMap[priority] || priority;
};
