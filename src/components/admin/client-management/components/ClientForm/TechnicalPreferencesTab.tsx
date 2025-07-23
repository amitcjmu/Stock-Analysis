import React from 'react';
import { Label } from '@/components/ui/label';
import type { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import type { ClientFormData } from '../../types';

interface TechnicalPreferencesTabProps {
  formData: ClientFormData;
  onFormChange: (field: keyof ClientFormData, value: ClientFormData[keyof ClientFormData]) => void;
}

export const TechnicalPreferencesTab: React.FC<TechnicalPreferencesTabProps> = ({ formData, onFormChange }) => {
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="space-y-4">
          <h3 className="text-lg font-medium">IT Guidelines</h3>
          <div className="space-y-3">
            <div>
              <Label htmlFor="architecture_patterns">Architecture Patterns</Label>
              <Input
                id="architecture_patterns"
                value={formData.it_guidelines?.architecture_patterns?.join(', ') || ''}
                onChange={(e) => onFormChange('it_guidelines', { 
                  ...formData.it_guidelines, 
                  architecture_patterns: e.target.value.split(',').map(s => s.trim()).filter(Boolean)
                })}
                placeholder="Microservices, Containerization, Serverless"
              />
            </div>
            <div>
              <Label htmlFor="security_requirements">Security Requirements</Label>
              <Textarea
                id="security_requirements"
                value={formData.it_guidelines?.security_requirements?.join('\n') || ''}
                onChange={(e) => onFormChange('it_guidelines', { 
                  ...formData.it_guidelines, 
                  security_requirements: e.target.value.split('\n').filter(Boolean)
                })}
                placeholder="Zero Trust Architecture&#10;End-to-end encryption&#10;Multi-factor authentication"
                rows={3}
              />
            </div>
            <div>
              <Label htmlFor="data_residency">Data Residency Requirements</Label>
              <Input
                id="data_residency"
                value={formData.it_guidelines?.data_residency_requirements?.join(', ') || ''}
                onChange={(e) => onFormChange('it_guidelines', { 
                  ...formData.it_guidelines, 
                  data_residency_requirements: e.target.value.split(',').map(s => s.trim()).filter(Boolean)
                })}
                placeholder="US-only, EU data centers, etc."
              />
            </div>
            <div>
              <Label htmlFor="integration_standards">Integration Standards</Label>
              <Input
                id="integration_standards"
                value={formData.it_guidelines?.integration_standards?.join(', ') || ''}
                onChange={(e) => onFormChange('it_guidelines', { 
                  ...formData.it_guidelines, 
                  integration_standards: e.target.value.split(',').map(s => s.trim()).filter(Boolean)
                })}
                placeholder="REST APIs, GraphQL, Event-driven"
              />
            </div>
          </div>
        </div>

        <div className="space-y-4">
          <h3 className="text-lg font-medium">Decision Criteria</h3>
          <div className="space-y-3">
            <div>
              <Label htmlFor="risk_tolerance">Risk Tolerance</Label>
              <Select 
                value={formData.decision_criteria?.risk_tolerance || 'medium'} 
                onValueChange={(value) => onFormChange('decision_criteria', { 
                  ...formData.decision_criteria, 
                  risk_tolerance: value 
                })}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="low">Low Risk</SelectItem>
                  <SelectItem value="medium">Medium Risk</SelectItem>
                  <SelectItem value="high">High Risk</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label htmlFor="cost_sensitivity">Cost Sensitivity</Label>
              <Select 
                value={formData.decision_criteria?.cost_sensitivity || 'medium'} 
                onValueChange={(value) => onFormChange('decision_criteria', { 
                  ...formData.decision_criteria, 
                  cost_sensitivity: value 
                })}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="low">Low Sensitivity</SelectItem>
                  <SelectItem value="medium">Medium Sensitivity</SelectItem>
                  <SelectItem value="high">High Sensitivity</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label htmlFor="timeline_pressure">Timeline Pressure</Label>
              <Select 
                value={formData.decision_criteria?.timeline_pressure || 'medium'} 
                onValueChange={(value) => onFormChange('decision_criteria', { 
                  ...formData.decision_criteria, 
                  timeline_pressure: value 
                })}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="low">Flexible Timeline</SelectItem>
                  <SelectItem value="medium">Moderate Urgency</SelectItem>
                  <SelectItem value="high">Urgent Timeline</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label htmlFor="technical_debt_tolerance">Technical Debt Tolerance</Label>
              <Select 
                value={formData.decision_criteria?.technical_debt_tolerance || 'medium'} 
                onValueChange={(value) => onFormChange('decision_criteria', { 
                  ...formData.decision_criteria, 
                  technical_debt_tolerance: value 
                })}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="low">Minimal Debt Acceptable</SelectItem>
                  <SelectItem value="medium">Moderate Debt Acceptable</SelectItem>
                  <SelectItem value="high">Higher Debt Acceptable</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};