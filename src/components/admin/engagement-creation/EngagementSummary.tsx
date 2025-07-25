import React from 'react';
import { Calendar, DollarSign, Target, Save } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Separator } from '@/components/ui/separator';
import type { CreateEngagementData , ClientAccount} from './types'
import { CloudProviders } from './types'

interface EngagementSummaryProps {
  formData: CreateEngagementData;
  clientAccounts: ClientAccount[];
  loading: boolean;
  onCancel: () => void;
  onSubmit: () => void;
}

export const EngagementSummary: React.FC<EngagementSummaryProps> = ({
  formData,
  clientAccounts,
  loading,
  onCancel,
  onSubmit
}) => {
  const selectedClient = clientAccounts.find(client => client.id === formData.client_account_id);

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Engagement Summary</CardTitle>
          <CardDescription>Review engagement information</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <Target className="w-4 h-4 text-muted-foreground" />
              <span className="font-medium">{formData.engagement_name || 'Engagement Name'}</span>
            </div>
            <div className="flex items-center gap-2">
              <Calendar className="w-4 h-4 text-muted-foreground" />
              <span className="text-sm">
                {formData.estimated_start_date ? formData.estimated_start_date : 'Start Date'} - {formData.estimated_end_date ? formData.estimated_end_date : 'End Date'}
              </span>
            </div>
            <div className="flex items-center gap-2">
              <DollarSign className="w-4 h-4 text-muted-foreground" />
              <span className="text-sm">
                {formData.budget ? `${formData.budget} ${formData.budget_currency}` : 'No budget set'}
              </span>
            </div>
          </div>

          <Separator />

          <div className="space-y-2">
            <h4 className="font-medium">Client</h4>
            <p className="text-sm text-muted-foreground">
              {selectedClient ? `${selectedClient.account_name} (${selectedClient.industry})` : 'Not selected'}
            </p>
          </div>

          <div className="space-y-2">
            <h4 className="font-medium">Project Manager</h4>
            <p className="text-sm text-muted-foreground">{formData.project_manager || 'Not assigned'}</p>
          </div>

          <div className="space-y-2">
            <h4 className="font-medium">Cloud Provider</h4>
            <p className="text-sm text-muted-foreground">
              {formData.target_cloud_provider
                ? CloudProviders.find(p => p.value === formData.target_cloud_provider)?.label
                : 'Not selected'
              }
            </p>
          </div>

          <div className="space-y-2">
            <h4 className="font-medium">Scope Items</h4>
            <p className="text-sm text-muted-foreground">
              {[
                formData.scope_applications && 'Applications',
                formData.scope_databases && 'Databases',
                formData.scope_infrastructure && 'Infrastructure',
                formData.scope_data_migration && 'Data Migration'
              ].filter(Boolean).join(', ') || 'None selected'}
            </p>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="pt-6">
          <div className="flex gap-3">
            <Button
              type="button"
              variant="outline"
              onClick={onCancel}
              className="flex-1"
            >
              Cancel
            </Button>
            <Button
              type="button"
              disabled={loading}
              onClick={onSubmit}
              className="flex-1"
            >
              {loading ? (
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
              ) : (
                <>
                  <Save className="w-4 h-4 mr-2" />
                  Create Engagement
                </>
              )}
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};
