/**
 * AgentSelector component extracted from AgentComparison
 * Handles agent selection for comparison
 */

import React from 'react'
import { useState } from 'react'
import { Search, X } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '../../ui/card';
import { Badge } from '../../ui/badge';
import { Button } from '../../ui/button';
import { Input } from '../../ui/input';

export interface AgentSelectorProps {
  availableAgents: string[];
  selectedAgents: string[];
  onSelectionChange: (agents: string[]) => void;
  maxAgents: number;
}

export const AgentSelector: React.FC<AgentSelectorProps> = ({
  availableAgents,
  selectedAgents,
  onSelectionChange,
  maxAgents
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  
  const filteredAgents = availableAgents.filter(agent =>
    agent.toLowerCase().includes(searchTerm.toLowerCase()) &&
    !selectedAgents.includes(agent)
  );

  const handleAddAgent = (agent: string) => {
    if (selectedAgents.length < maxAgents) {
      onSelectionChange([...selectedAgents, agent]);
    }
  };

  const handleRemoveAgent = (agent: string) => {
    onSelectionChange(selectedAgents.filter(a => a !== agent));
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">Select Agents to Compare</CardTitle>
        <p className="text-sm text-gray-600">
          Select up to {maxAgents} agents for performance comparison
        </p>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {/* Selected agents */}
          {selectedAgents.length > 0 && (
            <div className="space-y-2">
              <h4 className="text-sm font-medium text-gray-700">
                Selected Agents ({selectedAgents.length}/{maxAgents})
              </h4>
              <div className="flex flex-wrap gap-2">
                {selectedAgents.map(agent => (
                  <Badge key={agent} variant="default" className="flex items-center gap-1">
                    {agent.replace('Agent', '')}
                    <X 
                      className="w-3 h-3 cursor-pointer hover:text-red-500" 
                      onClick={() => handleRemoveAgent(agent)}
                    />
                  </Badge>
                ))}
              </div>
            </div>
          )}

          {/* Agent search and selection */}
          {selectedAgents.length < maxAgents && (
            <div className="space-y-2">
              <h4 className="text-sm font-medium text-gray-700">Available Agents</h4>
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                <Input
                  placeholder="Search agents..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-9"
                />
              </div>
              <div className="max-h-40 overflow-y-auto space-y-1">
                {filteredAgents.map(agent => (
                  <div
                    key={agent}
                    className="flex items-center justify-between p-2 rounded-md hover:bg-gray-50 cursor-pointer"
                    onClick={() => handleAddAgent(agent)}
                  >
                    <span className="text-sm">{agent}</span>
                    <Button variant="ghost" size="sm">
                      Add
                    </Button>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
};