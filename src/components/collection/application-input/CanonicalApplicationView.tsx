import React, { useState } from 'react';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import {
  Layers,
  Clock,
  MoreHorizontal,
  Edit3,
  Trash2,
  Merge,
  History,
  Search,
  Filter,
  ChevronDown,
  ChevronRight,
  Users,
  Calendar,
  MapPin,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import type {
  CanonicalApplication,
  ApplicationVariant,
  CollectionHistoryEntry,
  CanonicalApplicationSelection,
} from '@/types/collection/canonical-applications';

interface CanonicalApplicationViewProps {
  applications: CanonicalApplicationSelection[];
  canonicalApplications: CanonicalApplication[];
  onRemoveApplication: (canonicalApplicationId: string) => void;
  onEditApplication?: (application: CanonicalApplication) => void;
  onViewHistory?: (application: CanonicalApplication) => void;
  onMergeApplications?: (primary: CanonicalApplication, secondary: CanonicalApplication) => void;
  className?: string;
  showVariantDetails?: boolean;
  showCollectionHistory?: boolean;
}

/**
 * CanonicalApplicationView Component
 *
 * Provides a consolidated view of all canonical applications selected for collection.
 * Shows variants, collection history, and provides management actions like editing,
 * merging, and removing applications from the collection.
 */
export const CanonicalApplicationView: React.FC<CanonicalApplicationViewProps> = ({
  applications,
  canonicalApplications,
  onRemoveApplication,
  onEditApplication,
  onViewHistory,
  onMergeApplications,
  className,
  showVariantDetails = true,
  showCollectionHistory = false,
}) => {
  const [expandedApplications, setExpandedApplications] = useState<Set<string>>(new Set());
  const [searchTerm, setSearchTerm] = useState('');
  const [sortBy, setSortBy] = useState<'name' | 'variants' | 'lastCollected'>('name');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('asc');
  const [applicationToRemove, setApplicationToRemove] = useState<string | null>(null);

  // Toggle expansion of application details
  const toggleExpansion = (applicationId: string) => {
    const newExpanded = new Set(expandedApplications);
    if (newExpanded.has(applicationId)) {
      newExpanded.delete(applicationId);
    } else {
      newExpanded.add(applicationId);
    }
    setExpandedApplications(newExpanded);
  };

  // Get canonical application data
  const getCanonicalApplicationData = (canonicalAppId: string) => {
    return canonicalApplications.find(app => app.id === canonicalAppId);
  };

  // Filter and sort applications
  const filteredApplications = applications
    .filter(app => {
      if (!searchTerm.trim()) return true;
      const canonicalApp = getCanonicalApplicationData(app.canonical_application_id);
      if (!canonicalApp) return false;

      const searchLower = searchTerm.toLowerCase();
      return (
        canonicalApp.canonical_name.toLowerCase().includes(searchLower) ||
        app.variant_name.toLowerCase().includes(searchLower) ||
        canonicalApp.variants.some(variant =>
          variant.variant_name.toLowerCase().includes(searchLower)
        )
      );
    })
    .sort((a, b) => {
      const canonicalAppA = getCanonicalApplicationData(a.canonical_application_id);
      const canonicalAppB = getCanonicalApplicationData(b.canonical_application_id);

      if (!canonicalAppA || !canonicalAppB) return 0;

      let comparison = 0;
      switch (sortBy) {
        case 'name':
          comparison = canonicalAppA.canonical_name.localeCompare(canonicalAppB.canonical_name);
          break;
        case 'variants':
          comparison = canonicalAppA.variants.length - canonicalAppB.variants.length;
          break;
        case 'lastCollected':
          const dateA = canonicalAppA.metadata.last_collected_at ? new Date(canonicalAppA.metadata.last_collected_at) : new Date(0);
          const dateB = canonicalAppB.metadata.last_collected_at ? new Date(canonicalAppB.metadata.last_collected_at) : new Date(0);
          comparison = dateA.getTime() - dateB.getTime();
          break;
      }

      return sortOrder === 'asc' ? comparison : -comparison;
    });

  // Format last collected date
  const formatLastCollected = (dateString?: string) => {
    if (!dateString) return 'Never collected';
    const date = new Date(dateString);
    const now = new Date();
    const diffDays = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60 * 24));

    if (diffDays === 0) return 'Today';
    if (diffDays === 1) return 'Yesterday';
    if (diffDays < 7) return `${diffDays} days ago`;
    return date.toLocaleDateString();
  };

  // Get variant source badge
  const getVariantSourceBadge = (variant: ApplicationVariant) => {
    const sourceMap = {
      discovery: { label: 'Discovery', className: 'bg-blue-100 text-blue-800' },
      collection_manual: { label: 'Collection', className: 'bg-green-100 text-green-800' },
      collection_import: { label: 'Import', className: 'bg-purple-100 text-purple-800' },
      admin_created: { label: 'Admin', className: 'bg-gray-100 text-gray-800' },
    };

    const source = sourceMap[variant.source] || { label: 'Unknown', className: 'bg-gray-100 text-gray-800' };

    return (
      <Badge variant="outline" className={cn('text-xs', source.className)}>
        {source.label}
      </Badge>
    );
  };

  // Handle remove confirmation
  const handleRemoveConfirm = () => {
    if (applicationToRemove) {
      onRemoveApplication(applicationToRemove);
      setApplicationToRemove(null);
    }
  };

  if (applications.length === 0) {
    return (
      <Card className={className}>
        <CardContent className="flex flex-col items-center justify-center py-12">
          <Layers className="h-12 w-12 text-gray-300 mb-4" />
          <p className="text-gray-500 text-center">
            No applications selected yet.
          </p>
          <p className="text-gray-400 text-sm text-center mt-1">
            Start typing application names to add them to your collection.
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <>
      <Card className={className}>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <Layers className="h-5 w-5" />
                Selected Applications ({applications.length})
              </CardTitle>
              <CardDescription>
                Applications that will be included in this collection flow
              </CardDescription>
            </div>
          </div>

          {/* Search and Filter Controls */}
          {applications.length > 3 && (
            <div className="flex flex-col sm:flex-row gap-4 pt-4 border-t">
              <div className="flex-1 relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                <Input
                  type="text"
                  placeholder="Search applications..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10"
                />
              </div>

              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="outline" size="sm">
                    <Filter className="h-4 w-4 mr-2" />
                    Sort by {sortBy}
                    <ChevronDown className="h-4 w-4 ml-2" />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end">
                  <DropdownMenuItem onClick={() => { setSortBy('name'); setSortOrder('asc'); }}>
                    Name (A-Z)
                  </DropdownMenuItem>
                  <DropdownMenuItem onClick={() => { setSortBy('name'); setSortOrder('desc'); }}>
                    Name (Z-A)
                  </DropdownMenuItem>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem onClick={() => { setSortBy('variants'); setSortOrder('desc'); }}>
                    Most variants
                  </DropdownMenuItem>
                  <DropdownMenuItem onClick={() => { setSortBy('variants'); setSortOrder('asc'); }}>
                    Fewest variants
                  </DropdownMenuItem>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem onClick={() => { setSortBy('lastCollected'); setSortOrder('desc'); }}>
                    Recently collected
                  </DropdownMenuItem>
                  <DropdownMenuItem onClick={() => { setSortBy('lastCollected'); setSortOrder('asc'); }}>
                    Least recently collected
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </div>
          )}
        </CardHeader>

        <CardContent className="space-y-4">
          {filteredApplications.map((application) => {
            const canonicalApp = getCanonicalApplicationData(application.canonical_application_id);
            if (!canonicalApp) return null;

            const isExpanded = expandedApplications.has(application.canonical_application_id);

            return (
              <div
                key={application.canonical_application_id}
                className="border border-gray-200 rounded-lg"
              >
                {/* Application Header */}
                <div className="p-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3 flex-1 min-w-0">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => toggleExpansion(application.canonical_application_id)}
                        className="p-0 h-auto"
                      >
                        {isExpanded ? (
                          <ChevronDown className="h-4 w-4" />
                        ) : (
                          <ChevronRight className="h-4 w-4" />
                        )}
                      </Button>

                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          <h3 className="font-semibold text-gray-900 truncate">
                            {canonicalApp.canonical_name}
                          </h3>
                          <Badge variant="outline" className="text-xs">
                            {application.selection_method.replace('_', ' ')}
                          </Badge>
                        </div>

                        <div className="flex items-center gap-4 text-sm text-gray-500">
                          <span className="flex items-center gap-1">
                            <Layers className="h-3 w-3" />
                            {canonicalApp.variants.length} variant{canonicalApp.variants.length !== 1 ? 's' : ''}
                          </span>
                          <span className="flex items-center gap-1">
                            <Clock className="h-3 w-3" />
                            {formatLastCollected(canonicalApp.metadata.last_collected_at)}
                          </span>
                          {canonicalApp.metadata.collection_count > 0 && (
                            <span className="flex items-center gap-1">
                              <Users className="h-3 w-3" />
                              {canonicalApp.metadata.collection_count} collection{canonicalApp.metadata.collection_count !== 1 ? 's' : ''}
                            </span>
                          )}
                        </div>

                        {canonicalApp.description && (
                          <p className="text-sm text-gray-600 mt-2 line-clamp-2">
                            {canonicalApp.description}
                          </p>
                        )}
                      </div>
                    </div>

                    {/* Actions Menu */}
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button variant="ghost" size="sm">
                          <MoreHorizontal className="h-4 w-4" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        {onEditApplication && (
                          <DropdownMenuItem onClick={() => onEditApplication(canonicalApp)}>
                            <Edit3 className="h-4 w-4 mr-2" />
                            Edit Application
                          </DropdownMenuItem>
                        )}
                        {onViewHistory && (
                          <DropdownMenuItem onClick={() => onViewHistory(canonicalApp)}>
                            <History className="h-4 w-4 mr-2" />
                            View History
                          </DropdownMenuItem>
                        )}
                        {onMergeApplications && (
                          <DropdownMenuItem onClick={() => console.log('Merge functionality would be implemented here')}>
                            <Merge className="h-4 w-4 mr-2" />
                            Merge Applications
                          </DropdownMenuItem>
                        )}
                        <DropdownMenuSeparator />
                        <DropdownMenuItem
                          className="text-red-600"
                          onClick={() => setApplicationToRemove(application.canonical_application_id)}
                        >
                          <Trash2 className="h-4 w-4 mr-2" />
                          Remove from Collection
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </div>

                  {/* Selected Variant Badge */}
                  <div className="mt-3 pl-7">
                    <div className="inline-flex items-center gap-2 px-2 py-1 bg-blue-50 border border-blue-200 rounded text-sm">
                      <MapPin className="h-3 w-3 text-blue-600" />
                      <span className="text-blue-800">
                        Selected variant: <span className="font-medium">"{application.variant_name}"</span>
                      </span>
                    </div>
                  </div>
                </div>

                {/* Expanded Details */}
                {isExpanded && showVariantDetails && (
                  <div className="border-t border-gray-200 p-4 bg-gray-50">
                    <h4 className="font-medium text-gray-900 mb-3">All Variants ({canonicalApp.variants.length})</h4>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                      {canonicalApp.variants.map((variant) => (
                        <div
                          key={variant.id}
                          className={cn(
                            "flex items-center justify-between p-3 rounded border",
                            variant.variant_name === application.variant_name
                              ? "border-blue-200 bg-blue-50"
                              : "border-gray-200 bg-white"
                          )}
                        >
                          <div className="flex-1 min-w-0">
                            <div className="font-medium text-sm truncate">
                              {variant.variant_name}
                            </div>
                            <div className="text-xs text-gray-500 mt-1">
                              Added {new Date(variant.created_at).toLocaleDateString()}
                            </div>
                          </div>
                          <div className="flex items-center gap-2 ml-3">
                            {variant.variant_name === application.variant_name && (
                              <Badge variant="outline" className="text-xs bg-blue-100 text-blue-800">
                                Selected
                              </Badge>
                            )}
                            {getVariantSourceBadge(variant)}
                          </div>
                        </div>
                      ))}
                    </div>

                    {/* Collection History */}
                    {showCollectionHistory && canonicalApp.collection_history.length > 0 && (
                      <div className="mt-6">
                        <h4 className="font-medium text-gray-900 mb-3">Recent Collections</h4>
                        <div className="space-y-2">
                          {canonicalApp.collection_history.slice(0, 3).map((entry) => (
                            <div
                              key={entry.id}
                              className="flex items-center justify-between p-2 border border-gray-200 rounded bg-white"
                            >
                              <div className="flex-1">
                                <div className="text-sm font-medium">
                                  {entry.flow_name || `Collection ${entry.collection_flow_id.slice(-8)}`}
                                </div>
                                <div className="text-xs text-gray-500">
                                  Variant: "{entry.variant_name}" • {new Date(entry.collected_at).toLocaleDateString()}
                                </div>
                              </div>
                              <Badge
                                variant={entry.status === 'completed' ? 'default' :
                                        entry.status === 'in_progress' ? 'secondary' : 'destructive'}
                              >
                                {entry.status}
                              </Badge>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })}

          {/* No results message */}
          {filteredApplications.length === 0 && searchTerm && (
            <div className="text-center py-8 text-gray-500">
              <Search className="h-8 w-8 mx-auto mb-2" />
              <p>No applications match "{searchTerm}"</p>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setSearchTerm('')}
                className="mt-2"
              >
                Clear search
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Remove Confirmation Dialog */}
      <AlertDialog open={!!applicationToRemove} onOpenChange={() => setApplicationToRemove(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Remove Application</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to remove this application from the collection?
              This will not delete the application from your inventory, only remove it from this collection flow.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={handleRemoveConfirm}>
              Remove
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
};
