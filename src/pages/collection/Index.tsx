import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { 
  FileUpload, 
  FormInput, 
  Settings, 
  BarChart3,
  Clock,
  CheckCircle,
  AlertCircle
} from 'lucide-react';

/**
 * Collection workflow index page
 * Provides overview and entry points for all collection workflows
 */
const CollectionIndex: React.FC = () => {
  const navigate = useNavigate();

  const workflowOptions = [
    {
      id: 'adaptive-forms',
      title: 'Adaptive Data Collection',
      description: 'Dynamic forms that adapt based on application attributes and user responses',
      icon: <FormInput className="h-6 w-6" />,
      path: '/collection/adaptive-forms',
      status: 'available',
      completionRate: 0,
      estimatedTime: '15-30 min per application'
    },
    {
      id: 'bulk-upload',
      title: 'Bulk Data Upload',
      description: 'Upload and process multiple applications data via CSV/Excel templates',
      icon: <FileUpload className="h-6 w-6" />,
      path: '/collection/bulk-upload',
      status: 'available',
      completionRate: 0,
      estimatedTime: '5-10 min for 100+ applications'
    },
    {
      id: 'data-integration',
      title: 'Data Integration & Validation',
      description: 'Resolve conflicts and validate data from multiple collection sources',
      icon: <Settings className="h-6 w-6" />,
      path: '/collection/data-integration',
      status: 'available',
      completionRate: 0,
      estimatedTime: '10-20 min'
    },
    {
      id: 'progress-monitoring',
      title: 'Collection Progress Monitor',
      description: 'Monitor collection workflows and track completion status',
      icon: <BarChart3 className="h-6 w-6" />,
      path: '/collection/progress',
      status: 'available',
      completionRate: 0,
      estimatedTime: 'Real-time monitoring'
    }
  ];

  const getStatusBadge = (status: string, completionRate: number) => {
    if (completionRate > 0) {
      return <Badge variant="secondary"><CheckCircle className="h-3 w-3 mr-1" />{completionRate}% Complete</Badge>;
    }
    switch (status) {
      case 'available':
        return <Badge variant="outline">Ready to Start</Badge>;
      case 'in-progress':
        return <Badge variant="default"><Clock className="h-3 w-3 mr-1" />In Progress</Badge>;
      case 'requires-attention':
        return <Badge variant="destructive"><AlertCircle className="h-3 w-3 mr-1" />Needs Attention</Badge>;
      default:
        return <Badge variant="outline">Available</Badge>;
    }
  };

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="space-y-2">
        <h1 className="text-3xl font-bold">Data Collection Workflows</h1>
        <p className="text-muted-foreground">
          Choose the best data collection approach for your applications and infrastructure
        </p>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center space-x-2">
              <div className="p-2 bg-blue-100 rounded-lg">
                <FormInput className="h-4 w-4 text-blue-600" />
              </div>
              <div>
                <p className="text-sm font-medium">Active Forms</p>
                <p className="text-2xl font-bold">0</p>
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center space-x-2">
              <div className="p-2 bg-green-100 rounded-lg">
                <FileUpload className="h-4 w-4 text-green-600" />
              </div>
              <div>
                <p className="text-sm font-medium">Bulk Uploads</p>
                <p className="text-2xl font-bold">0</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center space-x-2">
              <div className="p-2 bg-orange-100 rounded-lg">
                <Settings className="h-4 w-4 text-orange-600" />
              </div>
              <div>
                <p className="text-sm font-medium">Pending Conflicts</p>
                <p className="text-2xl font-bold">0</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center space-x-2">
              <div className="p-2 bg-purple-100 rounded-lg">
                <CheckCircle className="h-4 w-4 text-purple-600" />
              </div>
              <div>
                <p className="text-sm font-medium">Completion Rate</p>
                <p className="text-2xl font-bold">0%</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Workflow Options */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {workflowOptions.map((workflow) => (
          <Card key={workflow.id} className="hover:shadow-lg transition-shadow cursor-pointer">
            <CardHeader>
              <div className="flex items-start justify-between">
                <div className="flex items-center space-x-3">
                  <div className="p-2 bg-primary/10 rounded-lg">
                    {workflow.icon}
                  </div>
                  <div>
                    <CardTitle className="text-lg">{workflow.title}</CardTitle>
                    <div className="mt-1">
                      {getStatusBadge(workflow.status, workflow.completionRate)}
                    </div>
                  </div>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <p className="text-muted-foreground mb-4">{workflow.description}</p>
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-1 text-sm text-muted-foreground">
                  <Clock className="h-3 w-3" />
                  <span>{workflow.estimatedTime}</span>
                </div>
                <Button 
                  onClick={() => navigate(workflow.path)}
                  variant="outline"
                  size="sm"
                >
                  Start Workflow
                </Button>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Getting Started Tips */}
      <Card>
        <CardHeader>
          <CardTitle>Getting Started with Data Collection</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <h4 className="font-medium mb-2">For Small to Medium Portfolios (1-50 apps)</h4>
              <p className="text-sm text-muted-foreground mb-2">
                Start with Adaptive Data Collection for detailed, application-specific insights
              </p>
              <Button 
                variant="outline" 
                size="sm"
                onClick={() => navigate('/collection/adaptive-forms')}
              >
                Start Adaptive Collection
              </Button>
            </div>
            <div>
              <h4 className="font-medium mb-2">For Large Portfolios (50+ apps)</h4>
              <p className="text-sm text-muted-foreground mb-2">
                Begin with Bulk Data Upload to efficiently process large application inventories
              </p>
              <Button 
                variant="outline" 
                size="sm"
                onClick={() => navigate('/collection/bulk-upload')}
              >
                Start Bulk Upload
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default CollectionIndex;