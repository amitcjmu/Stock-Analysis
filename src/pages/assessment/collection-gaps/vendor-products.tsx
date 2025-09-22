/**
 * Vendor Product Management UI
 *
 * Search/create/edit vendor products and map them to assets
 * Location: src/pages/assessment/collection-gaps/vendor-products.tsx
 */

import React, { useState, useCallback } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

// Layout components
import Sidebar from '@/components/Sidebar';
import ContextBreadcrumbs from '@/components/context/ContextBreadcrumbs';

// UI components
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '@/components/ui/dropdown-menu';

// Icons
import {
  Database,
  Search,
  Plus,
  Edit,
  Trash2,
  MoreHorizontal,
  ArrowLeft,
  CheckCircle,
  AlertTriangle,
  Info,
  Link,
  Calendar
} from 'lucide-react';

// Services and hooks
import { useToast } from '@/components/ui/use-toast';
import { cn } from '@/lib/utils';

// Types
import type { VendorProduct, TechnologySelectionOption } from '@/components/collection/types';

interface VendorProductExtended extends VendorProduct {
  created_at?: string;
  updated_at?: string;
  linked_assets_count?: number;
  lifecycle_dates?: {
    support_end_date?: string;
    extended_support_end_date?: string;
    latest_version?: string;
  };
}

interface VendorProductFormData {
  vendor_name: string;
  product_name: string;
  product_version?: string;
  category?: string;
  description?: string;
}

const VendorProductsPage: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { toast } = useToast();
  const queryClient = useQueryClient();

  const flowId = searchParams.get('flowId') || '';

  // State
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('');
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);
  const [isEditDialogOpen, setIsEditDialogOpen] = useState(false);
  const [editingProduct, setEditingProduct] = useState<VendorProductExtended | null>(null);
  const [formData, setFormData] = useState<VendorProductFormData>({
    vendor_name: '',
    product_name: '',
    product_version: '',
    category: '',
    description: ''
  });

  // Mock API calls (replace with actual API endpoints)
  const { data: vendorProducts, isLoading, error } = useQuery({
    queryKey: ['vendor-products', searchQuery, selectedCategory],
    queryFn: async (): Promise<VendorProductExtended[]> => {
      // This will be replaced with: apiCall('/api/v1/collection/vendor-products')
      await new Promise(resolve => setTimeout(resolve, 1000));

      const mockProducts: VendorProductExtended[] = [
        {
          id: '1',
          vendor_name: 'Microsoft',
          product_name: 'SQL Server',
          product_version: '2019',
          category: 'Database',
          normalized_vendor: 'Microsoft Corporation',
          normalized_product: 'Microsoft SQL Server',
          confidence_score: 0.95,
          created_at: '2024-01-15T10:00:00Z',
          linked_assets_count: 12,
          lifecycle_dates: {
            support_end_date: '2030-01-09',
            extended_support_end_date: '2035-01-09',
            latest_version: '2022'
          }
        },
        {
          id: '2',
          vendor_name: 'Oracle',
          product_name: 'Database',
          product_version: '19c',
          category: 'Database',
          normalized_vendor: 'Oracle Corporation',
          normalized_product: 'Oracle Database',
          confidence_score: 0.98,
          created_at: '2024-01-10T14:30:00Z',
          linked_assets_count: 8,
          lifecycle_dates: {
            support_end_date: '2027-04-30',
            extended_support_end_date: '2030-04-30',
            latest_version: '23c'
          }
        },
        {
          id: '3',
          vendor_name: 'VMware',
          product_name: 'vSphere',
          product_version: '7.0',
          category: 'Virtualization',
          normalized_vendor: 'VMware Inc.',
          normalized_product: 'VMware vSphere',
          confidence_score: 0.92,
          created_at: '2024-01-05T09:15:00Z',
          linked_assets_count: 25,
          lifecycle_dates: {
            support_end_date: '2025-04-02',
            extended_support_end_date: '2027-04-02',
            latest_version: '8.0'
          }
        }
      ];

      // Apply filters
      return mockProducts.filter(product => {
        const matchesSearch = !searchQuery ||
          product.vendor_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
          product.product_name.toLowerCase().includes(searchQuery.toLowerCase());
        const matchesCategory = !selectedCategory || product.category === selectedCategory;
        return matchesSearch && matchesCategory;
      });
    },
    refetchInterval: 30000,
    staleTime: 10000
  });

  // Categories for filtering
  const categories = ['Database', 'Virtualization', 'Operating System', 'Application Server', 'Middleware', 'Security'];

  // Create vendor product mutation
  const createProductMutation = useMutation({
    mutationFn: async (data: VendorProductFormData): Promise<VendorProductExtended> => {
      // This will be replaced with: apiCall('/api/v1/collection/vendor-products', { method: 'POST', body: data })
      await new Promise(resolve => setTimeout(resolve, 1000));
      return {
        id: Date.now().toString(),
        vendor_name: data.vendor_name,
        product_name: data.product_name,
        product_version: data.product_version,
        category: data.category,
        confidence_score: 0.85,
        created_at: new Date().toISOString(),
        linked_assets_count: 0
      };
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['vendor-products'] });
      setIsCreateDialogOpen(false);
      resetForm();
      toast({
        title: 'Vendor Product Created',
        description: 'The vendor product has been successfully created.'
      });
    },
    onError: (error) => {
      console.error('Failed to create vendor product:', error);
      toast({
        title: 'Creation Failed',
        description: 'Failed to create vendor product. Please try again.',
        variant: 'destructive'
      });
    }
  });

  // Update vendor product mutation
  const updateProductMutation = useMutation({
    mutationFn: async ({ id, data }: { id: string; data: VendorProductFormData }): Promise<VendorProductExtended> => {
      // This will be replaced with: apiCall(`/api/v1/collection/vendor-products/${id}`, { method: 'PUT', body: data })
      await new Promise(resolve => setTimeout(resolve, 1000));
      return {
        ...editingProduct,
        ...data,
        updated_at: new Date().toISOString()
      };
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['vendor-products'] });
      setIsEditDialogOpen(false);
      setEditingProduct(null);
      resetForm();
      toast({
        title: 'Vendor Product Updated',
        description: 'The vendor product has been successfully updated.'
      });
    },
    onError: (error) => {
      console.error('Failed to update vendor product:', error);
      toast({
        title: 'Update Failed',
        description: 'Failed to update vendor product. Please try again.',
        variant: 'destructive'
      });
    }
  });

  // Delete vendor product mutation
  const deleteProductMutation = useMutation({
    mutationFn: async (id: string): Promise<void> => {
      // This will be replaced with: apiCall(`/api/v1/collection/vendor-products/${id}`, { method: 'DELETE' })
      await new Promise(resolve => setTimeout(resolve, 1000));
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['vendor-products'] });
      toast({
        title: 'Vendor Product Deleted',
        description: 'The vendor product has been successfully deleted.'
      });
    },
    onError: (error) => {
      console.error('Failed to delete vendor product:', error);
      toast({
        title: 'Deletion Failed',
        description: 'Failed to delete vendor product. Please try again.',
        variant: 'destructive'
      });
    }
  });

  const resetForm = () => {
    setFormData({
      vendor_name: '',
      product_name: '',
      product_version: '',
      category: '',
      description: ''
    });
  };

  const handleCreateProduct = () => {
    if (!formData.vendor_name || !formData.product_name) {
      toast({
        title: 'Validation Error',
        description: 'Vendor name and product name are required.',
        variant: 'destructive'
      });
      return;
    }

    createProductMutation.mutate(formData);
  };

  const handleUpdateProduct = () => {
    if (!editingProduct?.id || !formData.vendor_name || !formData.product_name) {
      toast({
        title: 'Validation Error',
        description: 'Vendor name and product name are required.',
        variant: 'destructive'
      });
      return;
    }

    updateProductMutation.mutate({ id: editingProduct.id, data: formData });
  };

  const handleEditProduct = (product: VendorProductExtended) => {
    setEditingProduct(product);
    setFormData({
      vendor_name: product.vendor_name,
      product_name: product.product_name,
      product_version: product.product_version || '',
      category: product.category || '',
      description: ''
    });
    setIsEditDialogOpen(true);
  };

  const handleDeleteProduct = (id: string) => {
    if (confirm('Are you sure you want to delete this vendor product?')) {
      deleteProductMutation.mutate(id);
    }
  };

  const getLifecycleStatus = (product: VendorProductExtended) => {
    if (!product.lifecycle_dates?.support_end_date) return null;

    const supportEndDate = new Date(product.lifecycle_dates.support_end_date);
    const now = new Date();
    const monthsUntilEnd = Math.ceil((supportEndDate.getTime() - now.getTime()) / (1000 * 60 * 60 * 24 * 30));

    if (monthsUntilEnd < 0) {
      return { status: 'ended', color: 'bg-red-100 text-red-800', text: 'Support Ended' };
    } else if (monthsUntilEnd <= 12) {
      return { status: 'ending', color: 'bg-orange-100 text-orange-800', text: `${monthsUntilEnd}mo left` };
    } else {
      return { status: 'supported', color: 'bg-green-100 text-green-800', text: 'Supported' };
    }
  };

  if (!flowId) {
    return (
      <div className="flex min-h-screen bg-gray-50">
        <div className="hidden lg:block w-64 border-r bg-white">
          <Sidebar />
        </div>
        <div className="flex-1 overflow-y-auto">
          <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-4 sm:py-6 lg:py-8 max-w-7xl">
            <Alert>
              <Info className="h-4 w-4" />
              <AlertDescription>
                Flow ID is required to manage vendor products. Please navigate from an active collection flow.
              </AlertDescription>
            </Alert>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen bg-gray-50">
      <div className="hidden lg:block w-64 border-r bg-white">
        <Sidebar />
      </div>
      <div className="flex-1 overflow-y-auto">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-4 sm:py-6 lg:py-8 max-w-7xl">
          <div className="mb-6">
            <ContextBreadcrumbs />
          </div>

          <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => navigate(`/assessment/collection-gaps?flowId=${flowId}`)}
                  className="flex items-center gap-2"
                >
                  <ArrowLeft className="h-4 w-4" />
                  Back to Dashboard
                </Button>
                <div>
                  <h1 className="text-3xl font-bold">Vendor Product Management</h1>
                  <p className="text-muted-foreground">
                    Search, create, and manage vendor products for asset mapping
                  </p>
                </div>
              </div>
              <Dialog open={isCreateDialogOpen} onOpenChange={setIsCreateDialogOpen}>
                <DialogTrigger asChild>
                  <Button className="flex items-center gap-2">
                    <Plus className="h-4 w-4" />
                    Add Product
                  </Button>
                </DialogTrigger>
                <DialogContent>
                  <DialogHeader>
                    <DialogTitle>Create Vendor Product</DialogTitle>
                    <DialogDescription>
                      Add a new vendor product to the catalog
                    </DialogDescription>
                  </DialogHeader>
                  <div className="space-y-4">
                    <div className="grid grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <Label htmlFor="vendor_name">Vendor Name *</Label>
                        <Input
                          id="vendor_name"
                          value={formData.vendor_name}
                          onChange={(e) => setFormData({ ...formData, vendor_name: e.target.value })}
                          placeholder="e.g., Microsoft"
                        />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="product_name">Product Name *</Label>
                        <Input
                          id="product_name"
                          value={formData.product_name}
                          onChange={(e) => setFormData({ ...formData, product_name: e.target.value })}
                          placeholder="e.g., SQL Server"
                        />
                      </div>
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <Label htmlFor="product_version">Version</Label>
                        <Input
                          id="product_version"
                          value={formData.product_version}
                          onChange={(e) => setFormData({ ...formData, product_version: e.target.value })}
                          placeholder="e.g., 2019"
                        />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="category">Category</Label>
                        <Select value={formData.category} onValueChange={(value) => setFormData({ ...formData, category: value })}>
                          <SelectTrigger>
                            <SelectValue placeholder="Select category" />
                          </SelectTrigger>
                          <SelectContent>
                            {categories.map((cat) => (
                              <SelectItem key={cat} value={cat}>{cat}</SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>
                    </div>
                  </div>
                  <DialogFooter>
                    <Button variant="outline" onClick={() => setIsCreateDialogOpen(false)}>
                      Cancel
                    </Button>
                    <Button onClick={handleCreateProduct} disabled={createProductMutation.isPending}>
                      {createProductMutation.isPending ? 'Creating...' : 'Create Product'}
                    </Button>
                  </DialogFooter>
                </DialogContent>
              </Dialog>
            </div>

            {/* Filters */}
            <Card>
              <CardContent className="p-4">
                <div className="flex gap-4 items-end">
                  <div className="flex-1 space-y-2">
                    <Label htmlFor="search">Search Products</Label>
                    <div className="relative">
                      <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                      <Input
                        id="search"
                        placeholder="Search by vendor or product name..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        className="pl-10"
                      />
                    </div>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="category-filter">Category</Label>
                    <Select value={selectedCategory} onValueChange={setSelectedCategory}>
                      <SelectTrigger className="w-48">
                        <SelectValue placeholder="All categories" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="">All categories</SelectItem>
                        {categories.map((cat) => (
                          <SelectItem key={cat} value={cat}>{cat}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Error handling */}
            {error && (
              <Alert variant="destructive">
                <AlertTriangle className="h-4 w-4" />
                <AlertDescription>
                  Failed to load vendor products. Please try refreshing the page.
                </AlertDescription>
              </Alert>
            )}

            {/* Products Table */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Database className="h-5 w-5" />
                  Vendor Products ({vendorProducts?.length || 0})
                </CardTitle>
              </CardHeader>
              <CardContent className="p-0">
                {isLoading ? (
                  <div className="p-6">
                    <div className="space-y-3">
                      {[...Array(5)].map((_, i) => (
                        <div key={i} className="h-16 bg-gray-100 rounded animate-pulse" />
                      ))}
                    </div>
                  </div>
                ) : vendorProducts && vendorProducts.length > 0 ? (
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Vendor & Product</TableHead>
                        <TableHead>Version</TableHead>
                        <TableHead>Category</TableHead>
                        <TableHead>Lifecycle Status</TableHead>
                        <TableHead>Linked Assets</TableHead>
                        <TableHead>Confidence</TableHead>
                        <TableHead>Actions</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {vendorProducts.map((product) => {
                        const lifecycleStatus = getLifecycleStatus(product);
                        return (
                          <TableRow key={product.id}>
                            <TableCell>
                              <div className="space-y-1">
                                <div className="font-medium">{product.vendor_name}</div>
                                <div className="text-sm text-muted-foreground">{product.product_name}</div>
                                {product.normalized_vendor !== product.vendor_name && (
                                  <div className="text-xs text-blue-600">
                                    Normalized: {product.normalized_product}
                                  </div>
                                )}
                              </div>
                            </TableCell>
                            <TableCell>
                              <div className="space-y-1">
                                <div>{product.product_version || 'N/A'}</div>
                                {product.lifecycle_dates?.latest_version &&
                                 product.lifecycle_dates.latest_version !== product.product_version && (
                                  <div className="text-xs text-orange-600">
                                    Latest: {product.lifecycle_dates.latest_version}
                                  </div>
                                )}
                              </div>
                            </TableCell>
                            <TableCell>
                              {product.category && (
                                <Badge variant="outline">{product.category}</Badge>
                              )}
                            </TableCell>
                            <TableCell>
                              {lifecycleStatus ? (
                                <div className="space-y-1">
                                  <Badge className={lifecycleStatus.color}>
                                    {lifecycleStatus.text}
                                  </Badge>
                                  {product.lifecycle_dates?.support_end_date && (
                                    <div className="text-xs text-muted-foreground flex items-center gap-1">
                                      <Calendar className="h-3 w-3" />
                                      {new Date(product.lifecycle_dates.support_end_date).toLocaleDateString()}
                                    </div>
                                  )}
                                </div>
                              ) : (
                                <span className="text-muted-foreground">Unknown</span>
                              )}
                            </TableCell>
                            <TableCell>
                              <div className="flex items-center gap-2">
                                <Link className="h-4 w-4 text-muted-foreground" />
                                <span>{product.linked_assets_count || 0}</span>
                              </div>
                            </TableCell>
                            <TableCell>
                              <div className="flex items-center gap-2">
                                <div className="text-sm">
                                  {Math.round((product.confidence_score || 0) * 100)}%
                                </div>
                                {(product.confidence_score || 0) >= 0.9 ? (
                                  <CheckCircle className="h-4 w-4 text-green-600" />
                                ) : (product.confidence_score || 0) >= 0.7 ? (
                                  <AlertTriangle className="h-4 w-4 text-yellow-600" />
                                ) : (
                                  <AlertTriangle className="h-4 w-4 text-red-600" />
                                )}
                              </div>
                            </TableCell>
                            <TableCell>
                              <DropdownMenu>
                                <DropdownMenuTrigger asChild>
                                  <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
                                    <MoreHorizontal className="h-4 w-4" />
                                  </Button>
                                </DropdownMenuTrigger>
                                <DropdownMenuContent align="end">
                                  <DropdownMenuItem onClick={() => handleEditProduct(product)}>
                                    <Edit className="mr-2 h-4 w-4" />
                                    Edit
                                  </DropdownMenuItem>
                                  <DropdownMenuItem
                                    onClick={() => handleDeleteProduct(product.id)}
                                    className="text-red-600"
                                  >
                                    <Trash2 className="mr-2 h-4 w-4" />
                                    Delete
                                  </DropdownMenuItem>
                                </DropdownMenuContent>
                              </DropdownMenu>
                            </TableCell>
                          </TableRow>
                        );
                      })}
                    </TableBody>
                  </Table>
                ) : (
                  <div className="p-6 text-center">
                    <Database className="mx-auto h-12 w-12 text-gray-400" />
                    <h3 className="mt-2 text-sm font-medium text-gray-900">No vendor products found</h3>
                    <p className="mt-1 text-sm text-gray-500">
                      {searchQuery || selectedCategory ? 'Try adjusting your filters.' : 'Get started by adding your first vendor product.'}
                    </p>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Edit Dialog */}
          <Dialog open={isEditDialogOpen} onOpenChange={setIsEditDialogOpen}>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Edit Vendor Product</DialogTitle>
                <DialogDescription>
                  Update the vendor product information
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="edit_vendor_name">Vendor Name *</Label>
                    <Input
                      id="edit_vendor_name"
                      value={formData.vendor_name}
                      onChange={(e) => setFormData({ ...formData, vendor_name: e.target.value })}
                      placeholder="e.g., Microsoft"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="edit_product_name">Product Name *</Label>
                    <Input
                      id="edit_product_name"
                      value={formData.product_name}
                      onChange={(e) => setFormData({ ...formData, product_name: e.target.value })}
                      placeholder="e.g., SQL Server"
                    />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="edit_product_version">Version</Label>
                    <Input
                      id="edit_product_version"
                      value={formData.product_version}
                      onChange={(e) => setFormData({ ...formData, product_version: e.target.value })}
                      placeholder="e.g., 2019"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="edit_category">Category</Label>
                    <Select value={formData.category} onValueChange={(value) => setFormData({ ...formData, category: value })}>
                      <SelectTrigger>
                        <SelectValue placeholder="Select category" />
                      </SelectTrigger>
                      <SelectContent>
                        {categories.map((cat) => (
                          <SelectItem key={cat} value={cat}>{cat}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={() => setIsEditDialogOpen(false)}>
                  Cancel
                </Button>
                <Button onClick={handleUpdateProduct} disabled={updateProductMutation.isPending}>
                  {updateProductMutation.isPending ? 'Updating...' : 'Update Product'}
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </div>
      </div>
    </div>
  );
};

export default VendorProductsPage;
