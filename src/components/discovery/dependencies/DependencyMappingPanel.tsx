import React, { useState } from 'react';
import { Card } from '../../ui/card';
import { Button } from '../../ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../ui/select';
import { Input } from '../../ui/input';
import { DependencyData } from '../../../types/dependency';
import { Plus } from 'lucide-react';

interface DependencyMappingPanelProps {
  data: DependencyData | null;
  activeView: 'app-server' | 'app-app';
  onCreateDependency: (dependency: any) => void;
}

const DependencyMappingPanel: React.FC<DependencyMappingPanelProps> = ({
  data,
  activeView,
  onCreateDependency
}) => {
  const [sourceApp, setSourceApp] = useState('');
  const [targetApp, setTargetApp] = useState('');
  const [server, setServer] = useState('');
  const [dependencyType, setDependencyType] = useState('');

  if (!data) return null;

  const getApplications = () => {
    if (activeView === 'app-server') {
      const hostingRelationships = data?.app_server_mapping?.hosting_relationships || [];
      return Array.from(new Set(
        hostingRelationships.map(r => r?.application_name).filter(Boolean)
      ));
    } else {
      const crossAppDependencies = data?.cross_application_mapping?.cross_app_dependencies || [];
      return Array.from(new Set([
        ...crossAppDependencies.map(d => d?.source_app).filter(Boolean),
        ...crossAppDependencies.map(d => d?.target_app).filter(Boolean)
      ]));
    }
  };

  const getServers = () => {
    const hostingRelationships = data?.app_server_mapping?.hosting_relationships || [];
    return Array.from(new Set(
      hostingRelationships.map(r => r?.server_name).filter(Boolean)
    ));
  };

  const handleCreateDependency = () => {
    if (activeView === 'app-server') {
      if (!sourceApp || !server) return;
      onCreateDependency({
        application_name: sourceApp,
        server_name: server,
        status: 'pending',
        confidence: 1.0
      });
      setSourceApp('');
      setServer('');
    } else {
      if (!sourceApp || !targetApp || !dependencyType) return;
      onCreateDependency({
        source_app: sourceApp,
        target_app: targetApp,
        dependency_type: dependencyType,
        status: 'pending',
        confidence: 1.0
      });
      setSourceApp('');
      setTargetApp('');
      setDependencyType('');
    }
  };

  return (
    <Card className="p-4">
      <h2 className="text-lg font-semibold mb-4">Create New Dependency</h2>
      <div className="space-y-4">
        <div>
          <label className="text-sm font-medium">Source Application</label>
          <Select value={sourceApp} onValueChange={setSourceApp}>
            <SelectTrigger>
              <SelectValue placeholder="Select application" />
            </SelectTrigger>
            <SelectContent>
              {getApplications().map((app) => (
                <SelectItem key={app} value={app}>{app}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {activeView === 'app-server' ? (
          <div>
            <label className="text-sm font-medium">Target Server</label>
            <Select value={server} onValueChange={setServer}>
              <SelectTrigger>
                <SelectValue placeholder="Select server" />
              </SelectTrigger>
              <SelectContent>
                {getServers().map((s) => (
                  <SelectItem key={s} value={s}>{s}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        ) : (
          <>
            <div>
              <label className="text-sm font-medium">Target Application</label>
              <Select value={targetApp} onValueChange={setTargetApp}>
                <SelectTrigger>
                  <SelectValue placeholder="Select application" />
                </SelectTrigger>
                <SelectContent>
                  {getApplications()
                    .filter(app => app !== sourceApp)
                    .map((app) => (
                      <SelectItem key={app} value={app}>{app}</SelectItem>
                    ))}
                </SelectContent>
              </Select>
            </div>

            <div>
              <label className="text-sm font-medium">Dependency Type</label>
              <Select value={dependencyType} onValueChange={setDependencyType}>
                <SelectTrigger>
                  <SelectValue placeholder="Select type" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="api">API</SelectItem>
                  <SelectItem value="database">Database</SelectItem>
                  <SelectItem value="file">File</SelectItem>
                  <SelectItem value="message">Message Queue</SelectItem>
                  <SelectItem value="other">Other</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </>
        )}

        <Button
          className="w-full"
          onClick={handleCreateDependency}
          disabled={
            activeView === 'app-server'
              ? !sourceApp || !server
              : !sourceApp || !targetApp || !dependencyType
          }
        >
          <Plus className="h-4 w-4 mr-2" />
          Create Dependency
        </Button>
      </div>
    </Card>
  );
};

export default DependencyMappingPanel; 