import React from 'react';
import { Search, Download, Upload, Plus } from 'lucide-react';
import { Link } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import type { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import type { Client} from './types';
import { MigrationPhases } from './types';

interface EngagementFiltersProps {
  searchTerm: string;
  onSearchChange: (value: string) => void;
  filterClient: string;
  onClientFilterChange: (value: string) => void;
  filterPhase: string;
  onPhaseFilterChange: (value: string) => void;
  clients: Client[];
}

export const EngagementFilters: React.FC<EngagementFiltersProps> = ({
  searchTerm,
  onSearchChange,
  filterClient,
  onClientFilterChange,
  filterPhase,
  onPhaseFilterChange,
  clients
}) => {
  return (
    <>
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">Engagement Management</h1>
          <p className="text-muted-foreground">
            Manage client engagements and migration projects
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline">
            <Download className="w-4 h-4 mr-2" />
            Export
          </Button>
          <Button variant="outline">
            <Upload className="w-4 h-4 mr-2" />
            Import
          </Button>
          <Button asChild>
            <Link to="/admin/engagements/create">
              <Plus className="w-4 h-4 mr-2" />
              New Engagement
            </Link>
          </Button>
        </div>
      </div>

      {/* Search and Filters */}
      <div className="flex gap-4 items-center">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search engagements..."
            value={searchTerm}
            onChange={(e) => onSearchChange(e.target.value)}
            className="pl-8"
          />
        </div>
        <Select value={filterClient} onValueChange={onClientFilterChange}>
          <SelectTrigger className="w-40">
            <SelectValue placeholder="Client" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Clients</SelectItem>
            {clients.map(client => (
              <SelectItem key={client.id} value={client.id}>{client.account_name}</SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Select value={filterPhase} onValueChange={onPhaseFilterChange}>
          <SelectTrigger className="w-40">
            <SelectValue placeholder="Phase" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Phases</SelectItem>
            {MigrationPhases.map(phase => (
              <SelectItem key={phase.value} value={phase.value}>{phase.label}</SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>
    </>
  );
}; 