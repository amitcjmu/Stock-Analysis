import React from 'react'
import { useState } from 'react'
import { useMutation } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { apiCall } from '@/config/api';
import { ArrowLeft, Save, AlertCircle, Building2, Mail, MapPin } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Checkbox } from '@/components/ui/checkbox';
import { Separator } from '@/components/ui/separator';
import { useToast } from '@/components/ui/use-toast';

interface CreateClientData {
  account_name: string;
  industry: string;
  company_size: string;
  headquarters_location: string;
  primary_contact_name: string;
  primary_contact_email: string;
  primary_contact_phone: string;
  business_objectives: string[];
  target_cloud_providers: string[];
  business_priorities: string[];
  compliance_requirements: string[];
}

const CloudProviders = [
  { value: 'aws', label: 'Amazon Web Services (AWS)' },
  { value: 'azure', label: 'Microsoft Azure' },
  { value: 'gcp', label: 'Google Cloud Platform (GCP)' },
  { value: 'multi_cloud', label: 'Multi-Cloud Strategy' },
  { value: 'hybrid', label: 'Hybrid Cloud' },
  { value: 'private_cloud', label: 'Private Cloud' }
];

const BusinessPriorities = [
  { value: 'cost_reduction', label: 'Cost Reduction' },
  { value: 'agility_speed', label: 'Agility & Speed' },
  { value: 'security_compliance', label: 'Security & Compliance' },
  { value: 'innovation', label: 'Innovation' },
  { value: 'scalability', label: 'Scalability' },
  { value: 'reliability', label: 'Reliability' }
];

const Industries = [
  'Technology', 'Healthcare', 'Finance', 'Manufacturing', 'Retail',
  'Education', 'Government', 'Energy', 'Transportation', 'Other'
];

const CompanySizes = [
  'Small (1-100)', 'Medium (101-1000)', 'Large (1001-5000)', 'Enterprise (5000+)'
];

const CreateClient: React.FC = () => {
  const navigate = useNavigate();
  const { toast } = useToast();
  // Server state: useMutation for API interaction
  const createClientMutation = useMutation({
    mutationFn: async (payload: CreateClientData) => {
      return await apiCall('/admin/clients/', {
        method: 'POST',
        body: payload
      });
    },
    onSuccess: (data) => {
      toast({
        title: "Client Created Successfully",
        description: `Client ${formData.account_name} has been created and is now active.`,
      });
      navigate('/admin/clients');
    },
    onError: (error: Error & { response?: { data?: { detail?: string | object } }; message?: string }) => {
      console.error('Create client error:', error);
      let errorMessage = "Failed to create client. Please try again.";

      // Safely extract error message
      if (error?.response?.data?.detail) {
        errorMessage = typeof error.response.data.detail === 'string'
          ? error.response.data.detail
          : JSON.stringify(error.response.data.detail);
      } else if (error?.message) {
        errorMessage = typeof error.message === 'string'
          ? error.message
          : JSON.stringify(error.message);
      }

      toast({
        title: "Error",
        description: errorMessage,
        variant: "destructive"
      });
    }
  });

  const [formData, setFormData] = useState<CreateClientData>({
    account_name: '',
    industry: '',
    company_size: '',
    headquarters_location: '',
    primary_contact_name: '',
    primary_contact_email: '',
    primary_contact_phone: '',
    business_objectives: [],
    target_cloud_providers: [],
    business_priorities: [],
    compliance_requirements: []
  });

  const [errors, setErrors] = useState<Record<string, string>>({});

  // Simple form handler - no useCallback to prevent re-renders
  const handleFormChange = (field: keyof CreateClientData, value: CreateClientData[keyof CreateClientData]): void => {
    // Debug logging
    console.log(`handleFormChange: field=${field}, value=`, value, `type=${typeof value}`);

    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: '' }));
    }
  };

  const validateForm = (): JSX.Element => {
    const newErrors: Record<string, string> = {};

    if (!formData.account_name) newErrors.account_name = 'Account name is required';
    if (!formData.industry) newErrors.industry = 'Industry is required';
    if (!formData.company_size) newErrors.company_size = 'Company size is required';
    if (!formData.headquarters_location) newErrors.headquarters_location = 'Headquarters location is required';
    if (!formData.primary_contact_name) newErrors.primary_contact_name = 'Primary contact name is required';
    if (!formData.primary_contact_email) {
      newErrors.primary_contact_email = 'Primary contact email is required';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.primary_contact_email)) {
      newErrors.primary_contact_email = 'Invalid email format';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (e: React.FormEvent): void => {
    e.preventDefault();
    if (!validateForm()) {
      toast({
        title: "Validation Error",
        description: "Please fix the errors in the form",
        variant: "destructive"
      });
      return;
    }
    createClientMutation.mutate(formData);
  };

  return (
    <div className="container mx-auto p-6 space-y-6">
      <div className="flex items-center gap-4">
        <Button variant="outline" onClick={() => navigate('/admin/clients')}>
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back to Client Management
        </Button>
        <div>
          <h1 className="text-3xl font-bold">Create New Client</h1>
          <p className="text-muted-foreground">
            Add a new client account with business context and migration preferences
          </p>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Basic Information</CardTitle>
                <CardDescription>Client account and company details</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="account_name">Account Name *</Label>
                    <Input
                      id="account_name"
                      value={formData.account_name}
                      onChange={(e) => handleFormChange('account_name', e.target.value)}
                      placeholder="Enter company name"
                      required
                    />
                    {errors.account_name && (
                      <p className="text-sm text-red-600 flex items-center gap-1">
                        <AlertCircle className="w-3 h-3" />
                        {errors.account_name}
                      </p>
                    )}
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="industry">Industry *</Label>
                    <Select value={formData.industry} onValueChange={(value) => handleFormChange('industry', value)}>
                      <SelectTrigger>
                        <SelectValue placeholder="Select industry" />
                      </SelectTrigger>
                      <SelectContent>
                        {Industries.map(industry => (
                          <SelectItem key={industry} value={industry}>{industry}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    {errors.industry && (
                      <p className="text-sm text-red-600 flex items-center gap-1">
                        <AlertCircle className="w-3 h-3" />
                        {errors.industry}
                      </p>
                    )}
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="company_size">Company Size *</Label>
                    <Select value={formData.company_size} onValueChange={(value) => handleFormChange('company_size', value)}>
                      <SelectTrigger>
                        <SelectValue placeholder="Select company size" />
                      </SelectTrigger>
                      <SelectContent>
                        {CompanySizes.map(size => (
                          <SelectItem key={size} value={size}>{size}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    {errors.company_size && (
                      <p className="text-sm text-red-600 flex items-center gap-1">
                        <AlertCircle className="w-3 h-3" />
                        {errors.company_size}
                      </p>
                    )}
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="headquarters_location">Headquarters Location *</Label>
                    <Input
                      id="headquarters_location"
                      value={formData.headquarters_location}
                      onChange={(e) => handleFormChange('headquarters_location', e.target.value)}
                      placeholder="City, State/Country"
                      required
                    />
                    {errors.headquarters_location && (
                      <p className="text-sm text-red-600 flex items-center gap-1">
                        <AlertCircle className="w-3 h-3" />
                        {errors.headquarters_location}
                      </p>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Primary Contact</CardTitle>
                <CardDescription>Main point of contact for this client</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="primary_contact_name">Primary Contact Name *</Label>
                    <Input
                      id="primary_contact_name"
                      value={formData.primary_contact_name}
                      onChange={(e) => handleFormChange('primary_contact_name', e.target.value)}
                      placeholder="Full name"
                      required
                    />
                    {errors.primary_contact_name && (
                      <p className="text-sm text-red-600 flex items-center gap-1">
                        <AlertCircle className="w-3 h-3" />
                        {errors.primary_contact_name}
                      </p>
                    )}
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="primary_contact_email">Primary Contact Email *</Label>
                    <Input
                      id="primary_contact_email"
                      type="email"
                      value={formData.primary_contact_email}
                      onChange={(e) => handleFormChange('primary_contact_email', e.target.value)}
                      placeholder="email@company.com"
                      required
                    />
                    {errors.primary_contact_email && (
                      <p className="text-sm text-red-600 flex items-center gap-1">
                        <AlertCircle className="w-3 h-3" />
                        {errors.primary_contact_email}
                      </p>
                    )}
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="primary_contact_phone">Primary Contact Phone</Label>
                    <Input
                      id="primary_contact_phone"
                      value={formData.primary_contact_phone}
                      onChange={(e) => handleFormChange('primary_contact_phone', e.target.value)}
                      placeholder="+1-555-0123"
                    />
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Business Context</CardTitle>
                <CardDescription>Migration preferences and business priorities</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label>Target Cloud Providers</Label>
                  <div className="grid grid-cols-2 gap-2">
                    {CloudProviders.map(provider => (
                      <div key={provider.value} className="flex items-center space-x-2">
                        <Checkbox
                          id={`cloud-${provider.value}`}
                          checked={formData.target_cloud_providers.includes(provider.value)}
                          onCheckedChange={(checked) => {
                            console.log('Checkbox onCheckedChange:', checked, 'type:', typeof checked);
                            const currentArray = formData.target_cloud_providers;
                            if (checked) {
                              handleFormChange('target_cloud_providers', [...currentArray, provider.value]);
                            } else {
                              handleFormChange('target_cloud_providers', currentArray.filter(item => item !== provider.value));
                            }
                          }}
                        />
                        <label htmlFor={`cloud-${provider.value}`} className="text-sm cursor-pointer">
                          {provider.label}
                        </label>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="space-y-2">
                  <Label>Business Priorities</Label>
                  <div className="grid grid-cols-2 gap-2">
                    {BusinessPriorities.map(priority => (
                      <div key={priority.value} className="flex items-center space-x-2">
                        <Checkbox
                          id={`priority-${priority.value}`}
                          checked={formData.business_priorities.includes(priority.value)}
                          onCheckedChange={(checked) => {
                            const currentArray = formData.business_priorities;
                            if (checked) {
                              handleFormChange('business_priorities', [...currentArray, priority.value]);
                            } else {
                              handleFormChange('business_priorities', currentArray.filter(item => item !== priority.value));
                            }
                          }}
                        />
                        <label htmlFor={`priority-${priority.value}`} className="text-sm cursor-pointer">
                          {priority.label}
                        </label>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="business_objectives">Business Objectives</Label>
                  <Textarea
                    id="business_objectives"
                    placeholder="Enter business objectives (one per line)"
                    value={formData.business_objectives.join('\n')}
                    onChange={(e) => {
                      const newArray = e.target.value.split('\n').filter(item => item.trim());
                      handleFormChange('business_objectives', newArray);
                    }}
                    rows={3}
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="compliance_requirements">Compliance Requirements</Label>
                  <Textarea
                    id="compliance_requirements"
                    placeholder="Enter compliance requirements (one per line)"
                    value={formData.compliance_requirements.join('\n')}
                    onChange={(e) => {
                      const newArray = e.target.value.split('\n').filter(item => item.trim());
                      handleFormChange('compliance_requirements', newArray);
                    }}
                    rows={3}
                  />
                </div>
              </CardContent>
            </Card>
          </div>

          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Client Summary</CardTitle>
                <CardDescription>Review client information</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <div className="flex items-center gap-2">
                    <Building2 className="w-4 h-4 text-muted-foreground" />
                    <span className="font-medium">{formData.account_name || 'Company Name'}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Mail className="w-4 h-4 text-muted-foreground" />
                    <span className="text-sm">{formData.primary_contact_email || 'email@company.com'}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <MapPin className="w-4 h-4 text-muted-foreground" />
                    <span className="text-sm">{formData.headquarters_location || 'Location'}</span>
                  </div>
                </div>

                <Separator />

                <div className="space-y-2">
                  <h4 className="font-medium">Industry</h4>
                  <p className="text-sm text-muted-foreground">{formData.industry || 'Not selected'}</p>
                </div>

                <div className="space-y-2">
                  <h4 className="font-medium">Company Size</h4>
                  <p className="text-sm text-muted-foreground">{formData.company_size || 'Not selected'}</p>
                </div>

                <div className="space-y-2">
                  <h4 className="font-medium">Cloud Providers</h4>
                  <p className="text-sm text-muted-foreground">
                    {formData.target_cloud_providers.length > 0
                      ? `${formData.target_cloud_providers.length} selected`
                      : 'None selected'
                    }
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
                    onClick={() => navigate('/admin/clients')}
                    className="flex-1"
                  >
                    Cancel
                  </Button>
                  <Button
                    type="submit"
                    disabled={createClientMutation.isLoading}
                    className="flex-1"
                  >
                    {createClientMutation.isLoading ? (
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                    ) : (
                      <>
                        <Save className="w-4 h-4 mr-2" />
                        Create Client
                      </>
                    )}
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </form>
    </div>
  );
};

export default CreateClient;
