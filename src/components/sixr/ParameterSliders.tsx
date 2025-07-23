import React from 'react'
import { useState } from 'react'
import { useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Slider } from '../ui/slider';
import { Label } from '../ui/label';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '../ui/tooltip';
import { Badge } from '../ui/badge';
import { Button } from '../ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { Info } from 'lucide-react'
import { RotateCcw, Save } from 'lucide-react'
import { toast } from 'sonner';

export interface SixRParameters {
  business_value: number;
  technical_complexity: number;
  migration_urgency: number;
  compliance_requirements: number;
  cost_sensitivity: number;
  risk_tolerance: number;
  innovation_priority: number;
  application_type: 'custom' | 'cots' | 'hybrid';
}

interface ParameterSliderProps {
  parameters: SixRParameters;
  onParametersChange: (parameters: SixRParameters) => void;
  onSave?: () => void;
  disabled?: boolean;
  showApplicationType?: boolean;
  className?: string;
}

interface ParameterConfig {
  key: keyof Omit<SixRParameters, 'application_type'>;
  label: string;
  description: string;
  tooltip: string;
  lowLabel: string;
  highLabel: string;
  color: string;
}

const parameterConfigs: ParameterConfig[] = [
  {
    key: 'business_value',
    label: 'Business Value',
    description: 'Strategic importance and business impact of the application',
    tooltip: 'How critical is this application to business operations and revenue generation?',
    lowLabel: 'Low Impact',
    highLabel: 'Mission Critical',
    color: 'bg-blue-500'
  },
  {
    key: 'technical_complexity',
    label: 'Technical Complexity',
    description: 'Complexity of the application architecture and technology stack',
    tooltip: 'How complex is the application in terms of architecture, dependencies, and technology?',
    lowLabel: 'Simple',
    highLabel: 'Highly Complex',
    color: 'bg-red-500'
  },
  {
    key: 'migration_urgency',
    label: 'Migration Urgency',
    description: 'Timeline pressure and urgency for cloud migration',
    tooltip: 'How urgent is the need to migrate this application to the cloud?',
    lowLabel: 'No Rush',
    highLabel: 'Immediate',
    color: 'bg-orange-500'
  },
  {
    key: 'compliance_requirements',
    label: 'Compliance Requirements',
    description: 'Regulatory and compliance constraints affecting migration',
    tooltip: 'What level of regulatory compliance and security requirements apply?',
    lowLabel: 'Minimal',
    highLabel: 'Strict',
    color: 'bg-purple-500'
  },
  {
    key: 'cost_sensitivity',
    label: 'Cost Sensitivity',
    description: 'Budget constraints and cost optimization priorities',
    tooltip: 'How sensitive is the organization to migration and operational costs?',
    lowLabel: 'Cost Flexible',
    highLabel: 'Cost Critical',
    color: 'bg-green-500'
  },
  {
    key: 'risk_tolerance',
    label: 'Risk Tolerance',
    description: 'Organizational appetite for migration risk and change',
    tooltip: 'What is the tolerance for risk and potential disruption during migration?',
    lowLabel: 'Risk Averse',
    highLabel: 'Risk Accepting',
    color: 'bg-yellow-500'
  },
  {
    key: 'innovation_priority',
    label: 'Innovation Priority',
    description: 'Desire for modernization and cloud-native capabilities',
    tooltip: 'How important is leveraging modern cloud-native features and innovation?',
    lowLabel: 'Stability Focus',
    highLabel: 'Innovation Focus',
    color: 'bg-indigo-500'
  }
];

const applicationTypeOptions = [
  {
    value: 'custom' as const,
    label: 'Custom Application',
    description: 'Built in-house or custom-developed application'
  },
  {
    value: 'cots' as const,
    label: 'COTS Application',
    description: 'Commercial Off-The-Shelf application'
  },
  {
    value: 'hybrid' as const,
    label: 'Hybrid Application',
    description: 'Mix of custom and COTS components'
  }
];

const getParameterLevel = (value: number): { level: string; color: string } => {
  if (value <= 2) return { level: 'Very Low', color: 'bg-gray-500' };
  if (value <= 4) return { level: 'Low', color: 'bg-blue-500' };
  if (value <= 6) return { level: 'Medium', color: 'bg-yellow-500' };
  if (value <= 8) return { level: 'High', color: 'bg-orange-500' };
  return { level: 'Very High', color: 'bg-red-500' };
};

const defaultParameters: SixRParameters = {
  business_value: 5,
  technical_complexity: 5,
  migration_urgency: 5,
  compliance_requirements: 5,
  cost_sensitivity: 5,
  risk_tolerance: 5,
  innovation_priority: 5,
  application_type: 'custom'
};

export const ParameterSliders: React.FC<ParameterSliderProps> = ({
  parameters,
  onParametersChange,
  onSave,
  disabled = false,
  showApplicationType = true,
  className = ''
}) => {
  const [localParameters, setLocalParameters] = useState<SixRParameters>(parameters);
  const [hasChanges, setHasChanges] = useState(false);

  useEffect(() => {
    setLocalParameters(parameters);
    setHasChanges(false);
  }, [parameters]);

  const handleParameterChange = (key: keyof SixRParameters, value: number | string) => {
    const newParameters = { ...localParameters, [key]: value };
    setLocalParameters(newParameters);
    setHasChanges(true);
    onParametersChange(newParameters);
  };

  const handleReset = () => {
    setLocalParameters(defaultParameters);
    setHasChanges(true);
    onParametersChange(defaultParameters);
    toast.success('Parameters reset to defaults');
  };

  const handleSave = () => {
    if (onSave) {
      onSave();
      setHasChanges(false);
      toast.success('Parameters saved successfully');
    }
  };

  const renderParameterSlider = (config: ParameterConfig) => {
    const value = localParameters[config.key];
    const { level, color } = getParameterLevel(value);

    return (
      <div key={config.key} className="space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Label htmlFor={config.key} className="text-sm font-medium">
              {config.label}
            </Label>
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger>
                  <Info className="h-4 w-4 text-gray-400 hover:text-gray-600" />
                </TooltipTrigger>
                <TooltipContent>
                  <p className="max-w-xs">{config.tooltip}</p>
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
          </div>
          <div className="flex items-center space-x-2">
            <Badge variant="outline" className={`${color} text-white`}>
              {level}
            </Badge>
            <span className="text-sm font-mono text-gray-600 min-w-[2rem] text-right">
              {value}
            </span>
          </div>
        </div>
        
        <div className="space-y-2">
          <Slider
            id={config.key}
            min={1}
            max={10}
            step={0.5}
            value={[value]}
            onValueChange={(values) => handleParameterChange(config.key, values[0])}
            disabled={disabled}
            className="w-full"
          />
          <div className="flex justify-between text-xs text-gray-500">
            <span>{config.lowLabel}</span>
            <span>{config.highLabel}</span>
          </div>
        </div>
        
        <p className="text-xs text-gray-600">{config.description}</p>
      </div>
    );
  };

  return (
    <Card className={`w-full ${className}`}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="text-lg font-semibold">6R Analysis Parameters</CardTitle>
            <CardDescription>
              Adjust the parameters below to customize the 6R migration strategy analysis
            </CardDescription>
          </div>
          <div className="flex items-center space-x-2">
            {hasChanges && (
              <Badge variant="outline" className="bg-yellow-50 text-yellow-700 border-yellow-200">
                Unsaved Changes
              </Badge>
            )}
            <Button
              variant="outline"
              size="sm"
              onClick={handleReset}
              disabled={disabled}
              className="flex items-center space-x-1"
            >
              <RotateCcw className="h-4 w-4" />
              <span>Reset</span>
            </Button>
            {onSave && (
              <Button
                size="sm"
                onClick={handleSave}
                disabled={disabled || !hasChanges}
                className="flex items-center space-x-1"
              >
                <Save className="h-4 w-4" />
                <span>Save</span>
              </Button>
            )}
          </div>
        </div>
      </CardHeader>
      
      <CardContent className="space-y-6">
        {showApplicationType && (
          <div className="space-y-4 pb-6 border-b border-gray-200">
            <div className="flex items-center space-x-2">
              <Label htmlFor="application_type" className="text-sm font-medium">
                Application Type
              </Label>
              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger>
                    <Info className="h-4 w-4 text-gray-400 hover:text-gray-600" />
                  </TooltipTrigger>
                  <TooltipContent>
                    <p className="max-w-xs">
                      COTS applications cannot be rewritten, only replaced with alternatives
                    </p>
                  </TooltipContent>
                </Tooltip>
              </TooltipProvider>
            </div>
            
            <Select
              value={localParameters.application_type}
              onValueChange={(value) => handleParameterChange('application_type', value)}
              disabled={disabled}
            >
              <SelectTrigger className="w-full">
                <SelectValue placeholder="Select application type" />
              </SelectTrigger>
              <SelectContent>
                {applicationTypeOptions.map((option) => (
                  <SelectItem key={option.value} value={option.value}>
                    <div className="flex flex-col">
                      <span className="font-medium">{option.label}</span>
                      <span className="text-xs text-gray-500">{option.description}</span>
                    </div>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {parameterConfigs.map(renderParameterSlider)}
        </div>

        {/* Parameter Summary */}
        <div className="mt-6 p-4 bg-gray-50 rounded-lg">
          <h4 className="text-sm font-medium text-gray-900 mb-2">Parameter Summary</h4>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-xs">
            {parameterConfigs.map((config) => {
              const value = localParameters[config.key];
              const { level } = getParameterLevel(value);
              return (
                <div key={config.key} className="flex justify-between">
                  <span className="text-gray-600">{config.label}:</span>
                  <span className="font-medium">{value} ({level})</span>
                </div>
              );
            })}
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default ParameterSliders; 