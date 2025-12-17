import React from 'react';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { Brain } from 'lucide-react';

export type ModelType = 'auto' | 'gemini' | 'llama4_maverick' | 'gemma3_4b';

interface ModelSelectorProps {
  value: ModelType;
  onChange: (value: ModelType) => void;
  className?: string;
}

const MODEL_OPTIONS: { value: ModelType; label: string; description: string }[] = [
  {
    value: 'auto',
    label: 'Auto (Recommended)',
    description: 'Automatically select the best model',
  },
  {
    value: 'gemini',
    label: 'Google Gemini',
    description: 'Google Gemini 1.5 Pro - Advanced reasoning',
  },
  {
    value: 'llama4_maverick',
    label: 'Llama 4 Maverick',
    description: 'Meta Llama 4 - Complex analysis',
  },
  {
    value: 'gemma3_4b',
    label: 'Gemma 3 4B',
    description: 'Google Gemma 3 - Fast & efficient',
  },
];

export const ModelSelector: React.FC<ModelSelectorProps> = ({
  value,
  onChange,
  className = '',
}) => {
  return (
    <div className={`flex items-center gap-2 ${className}`}>
      <Brain className="h-4 w-4 text-muted-foreground" />
      <Select value={value} onValueChange={onChange}>
        <SelectTrigger className="w-[200px]">
          <SelectValue placeholder="Select model" />
        </SelectTrigger>
        <SelectContent>
          {MODEL_OPTIONS.map((option) => (
            <SelectItem key={option.value} value={option.value}>
              <div className="flex flex-col">
                <span className="font-medium">{option.label}</span>
                <span className="text-xs text-muted-foreground">
                  {option.description}
                </span>
              </div>
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  );
};

