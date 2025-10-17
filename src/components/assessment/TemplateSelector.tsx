import React from 'react'
import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { Label } from '@/components/ui/label';
import type { ArchitectureStandard } from '@/hooks/useAssessmentFlow';
import { Network } from 'lucide-react'
import { Building2, Cloud, Shield, Cpu, Database } from 'lucide-react'

interface Template {
  id: string;
  name: string;
  description: string;
  category: 'enterprise' | 'cloud-native' | 'security-first' | 'performance';
  icon: React.ComponentType<{ className?: string }>;
  standards: ArchitectureStandard[];
}

interface TemplateSelectorProps {
  onTemplateSelect: (template: Template) => void;
}

const ARCHITECTURE_TEMPLATES: Template[] = [
  {
    id: 'enterprise-standard',
    name: 'Enterprise Standard',
    description: 'Comprehensive enterprise architecture requirements with high availability and security',
    category: 'enterprise',
    icon: Building2,
    standards: [
      {
        requirement_type: 'security',
        description: 'SSL/TLS encryption required for all communications',
        mandatory: true,
        supported_versions: { 'TLS': '1.2+' },
        requirement_details: { 'encryption_level': 'AES-256' }
      },
      {
        requirement_type: 'availability',
        description: '99.9% uptime SLA requirement',
        mandatory: true,
        requirement_details: { 'sla_percentage': 99.9, 'downtime_tolerance': '8.76 hours/year' }
      },
      {
        requirement_type: 'backup',
        description: 'Daily automated backups with 30-day retention',
        mandatory: true,
        requirement_details: { 'frequency': 'daily', 'retention_days': 30 }
      },
      {
        requirement_type: 'monitoring',
        description: 'Comprehensive application and infrastructure monitoring',
        mandatory: true,
        requirement_details: { 'metrics_collection': true, 'alerting': true }
      }
    ]
  },
  {
    id: 'cloud-native',
    name: 'Cloud-Native Optimized',
    description: 'Modern cloud-first architecture with microservices and containerization',
    category: 'cloud-native',
    icon: Cloud,
    standards: [
      {
        requirement_type: 'containerization',
        description: 'All applications must be containerized (Docker/Kubernetes)',
        mandatory: true,
        supported_versions: { 'Docker': '20.0+', 'Kubernetes': '1.20+' },
        requirement_details: { 'orchestration': 'kubernetes' }
      },
      {
        requirement_type: 'scalability',
        description: 'Horizontal auto-scaling capability required',
        mandatory: true,
        requirement_details: { 'min_replicas': 2, 'max_replicas': 50 }
      },
      {
        requirement_type: 'api',
        description: 'RESTful APIs with OpenAPI 3.0 documentation',
        mandatory: true,
        supported_versions: { 'OpenAPI': '3.0+' },
        requirement_details: { 'versioning': 'semantic' }
      },
      {
        requirement_type: 'observability',
        description: 'Distributed tracing and metrics collection',
        mandatory: true,
        requirement_details: { 'tracing': 'opentelemetry', 'metrics': 'prometheus' }
      }
    ]
  },
  {
    id: 'security-first',
    name: 'Security-First',
    description: 'High-security requirements for sensitive data and compliance',
    category: 'security-first',
    icon: Shield,
    standards: [
      {
        requirement_type: 'authentication',
        description: 'Multi-factor authentication required for all access',
        mandatory: true,
        requirement_details: { 'mfa_methods': ['totp', 'sms', 'hardware_token'] }
      },
      {
        requirement_type: 'encryption',
        description: 'Data encryption at rest and in transit',
        mandatory: true,
        requirement_details: { 'at_rest': 'AES-256', 'in_transit': 'TLS 1.3' }
      },
      {
        requirement_type: 'compliance',
        description: 'SOC 2 Type II compliance required',
        mandatory: true,
        requirement_details: { 'frameworks': ['SOC2', 'ISO27001'] }
      },
      {
        requirement_type: 'audit',
        description: 'Comprehensive audit logging and retention',
        mandatory: true,
        requirement_details: { 'retention_years': 7, 'immutable_logs': true }
      }
    ]
  },
  {
    id: 'performance-optimized',
    name: 'Performance Optimized',
    description: 'High-performance requirements for latency-sensitive applications',
    category: 'performance',
    icon: Cpu,
    standards: [
      {
        requirement_type: 'latency',
        description: 'API response time under 100ms for 95th percentile',
        mandatory: true,
        requirement_details: { 'p95_latency_ms': 100, 'p99_latency_ms': 500 }
      },
      {
        requirement_type: 'caching',
        description: 'Multi-layer caching strategy implementation',
        mandatory: true,
        requirement_details: { 'cdn': true, 'application_cache': true, 'database_cache': true }
      },
      {
        requirement_type: 'database',
        description: 'Database optimization and query performance',
        mandatory: true,
        requirement_details: { 'query_timeout_ms': 1000, 'connection_pooling': true }
      },
      {
        requirement_type: 'load_balancing',
        description: 'Intelligent load balancing with health checks',
        mandatory: true,
        requirement_details: { 'algorithm': 'least_connections', 'health_check_interval': 30 }
      }
    ]
  }
];

const getCategoryIcon = (category: Template['category']): unknown => {
  switch (category) {
    case 'enterprise': return Building2;
    case 'cloud-native': return Cloud;
    case 'security-first': return Shield;
    case 'performance': return Cpu;
    default: return Building2;
  }
};

const getCategoryColor = (category: Template['category']): unknown => {
  switch (category) {
    case 'enterprise': return 'bg-blue-100 text-blue-700 border-blue-200';
    case 'cloud-native': return 'bg-green-100 text-green-700 border-green-200';
    case 'security-first': return 'bg-red-100 text-red-700 border-red-200';
    case 'performance': return 'bg-orange-100 text-orange-700 border-orange-200';
    default: return 'bg-gray-100 text-gray-700 border-gray-200';
  }
};

export const TemplateSelector: React.FC<TemplateSelectorProps> = ({ onTemplateSelect }) => {
  const [selectedTemplate, setSelectedTemplate] = useState<string>('');

  const handleTemplateSelect = (templateId: string): void => {
    setSelectedTemplate(templateId);
    const template = ARCHITECTURE_TEMPLATES.find(t => t.id === templateId);
    if (template) {
      onTemplateSelect(template);
    }
  };

  return (
    <div className="space-y-4">
      <RadioGroup value={selectedTemplate} onValueChange={handleTemplateSelect}>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {ARCHITECTURE_TEMPLATES.map((template) => {
            const Icon = template.icon;
            const isSelected = selectedTemplate === template.id;

            return (
              <div key={template.id} className="relative">
                <RadioGroupItem
                  value={template.id}
                  id={template.id}
                  className="sr-only"
                />
                <Label
                  htmlFor={template.id}
                  className="cursor-pointer"
                >
                  <Card className={`transition-all duration-200 hover:shadow-md ${
                    isSelected ? 'ring-2 ring-blue-500 border-blue-200' : ''
                  }`}>
                    <CardHeader className="pb-3">
                      <div className="flex items-start justify-between">
                        <div className="flex items-center space-x-3">
                          <div className={`p-2 rounded-lg ${getCategoryColor(template.category)}`}>
                            <Icon className="h-5 w-5" />
                          </div>
                          <div>
                            <CardTitle className="text-lg">{template.name}</CardTitle>
                            <Badge variant="outline" className="mt-1">
                              {template.category.replace('-', ' ')}
                            </Badge>
                          </div>
                        </div>
                        {isSelected && (
                          <div className="w-5 h-5 bg-blue-500 rounded-full flex items-center justify-center">
                            <div className="w-2 h-2 bg-white rounded-full" />
                          </div>
                        )}
                      </div>
                    </CardHeader>
                    <CardContent>
                      <CardDescription className="text-sm mb-3">
                        {template.description}
                      </CardDescription>

                      <div className="space-y-2">
                        <p className="text-xs font-medium text-gray-700">
                          Key Requirements ({template.standards.length}):
                        </p>
                        <div className="space-y-1">
                          {template.standards.slice(0, 3).map((standard) => (
                            <div key={`${template.id}-${standard.requirement_type}`} className="flex items-center space-x-2">
                              <div className="w-1.5 h-1.5 bg-gray-400 rounded-full" />
                              <span className="text-xs text-gray-600">
                                {standard.requirement_type}: {standard.description.split('.')[0]}
                              </span>
                            </div>
                          ))}
                          {template.standards.length > 3 && (
                            <div className="flex items-center space-x-2">
                              <div className="w-1.5 h-1.5 bg-gray-400 rounded-full" />
                              <span className="text-xs text-gray-500">
                                +{template.standards.length - 3} more requirements
                              </span>
                            </div>
                          )}
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </Label>
              </div>
            );
          })}
        </div>
      </RadioGroup>

      {/* Custom Template Option */}
      <div className="pt-4 border-t border-gray-200">
        <Button
          variant="outline"
          onClick={() => handleTemplateSelect('custom')}
          className="w-full"
        >
          <Database className="h-4 w-4 mr-2" />
          Start with Custom Standards
        </Button>
      </div>
    </div>
  );
};
