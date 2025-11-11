import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { resourcesService } from '../services/resources';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Alert, AlertDescription } from '../components/ui/alert';
import { Input } from '../components/ui/input';
import { Badge } from '../components/ui/badge';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '../components/ui/alert-dialog';
import {
  Plus,
  Edit,
  Trash2,
  Search,
  AlertCircle,
  Download,
  ExternalLink,
  GlobeIcon,
  BookOpenIcon,
  VideoIcon,
  FileTextIcon,
  LinkIcon,
  DatabaseIcon,
  FolderIcon,
  Code2Icon,
  Server,
  Cloud,
  Cpu,
  HardDrive,
  Network,
  Terminal,
  Box,
  Package,
  Layers,
  GitBranch,
  Github,
  FileCode,
  FileJson,
  FileCog,
  BookMarked,
  GraduationCap,
  Library,
  Microscope,
  FlaskConical,
  Activity,
  BarChart,
  LineChart,
  PieChart,
  TrendingUp,
  Calculator,
  Beaker,
} from 'lucide-react';
import type { Resource, ResourceFormData } from '../types';
import ResourceForm from '../components/resources/ResourceForm';

export default function ResourcesAdmin() {
  const [searchQuery, setSearchQuery] = useState('');
  const [showForm, setShowForm] = useState(false);
  const [editingResource, setEditingResource] = useState<Resource | null>(null);
  const [deleteConfirm, setDeleteConfirm] = useState<Resource | null>(null);
  const queryClient = useQueryClient();

  // Fetch admin resources
  const { data: resourcesData, isLoading, error } = useQuery({
    queryKey: ['admin', 'resources'],
    queryFn: async () => {
      const response = await resourcesService.getAdminResources();
      console.log('Admin resources response:', response);

      // Check if response indicates an error
      if (!response.success) {
        console.error('API returned error');
        throw new Error('Failed to load resources');
      }

      return response;
    },
  });

  // Create resource mutation
  const createMutation = useMutation({
    mutationFn: (data: ResourceFormData) => resourcesService.createAdminResource(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'resources'] });
      setShowForm(false);
      setEditingResource(null);
    },
  });

  // Update resource mutation
  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<ResourceFormData> }) =>
      resourcesService.updateAdminResource(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'resources'] });
      setShowForm(false);
      setEditingResource(null);
    },
  });

  // Delete resource mutation
  const deleteMutation = useMutation({
    mutationFn: (id: string) => resourcesService.deleteAdminResource(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'resources'] });
      setDeleteConfirm(null);
    },
  });

  // Seed default resources mutation
  const seedMutation = useMutation({
    mutationFn: () => resourcesService.seedResources(),
    onSuccess: (response) => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'resources'] });
      const { seeded, existing, errors } = response?.results || { seeded: [], existing: [], errors: [] };

      const messages = [];
      if (seeded.length > 0) {
        messages.push(`✓ Created ${seeded.length} resources: ${seeded.join(', ')}`);
      }
      if (existing.length > 0) {
        messages.push(`ℹ ${existing.length} resources already exist: ${existing.join(', ')}`);
      }
      if (errors.length > 0) {
        messages.push(`✗ ${errors.length} errors occurred`);
      }

      if (messages.length > 0) {
        alert(messages.join('\n\n'));
      }
    },
  });

  // Extract resources from API response
  // Admin endpoint returns { success, resources, stats }
  const resources = resourcesData?.resources || [];

  // Define the Big 3 core ExCITE apps
  const BIG_3_IDS = ['wintehr-default', 'broadsea-default', 'jupyterhub-default'];

  // Filter resources based on search
  const filteredResources = resources.filter((resource) => {
    const matchesSearch =
      searchQuery === '' ||
      resource.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      resource.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
      resource.category.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesSearch;
  });

  // Separate Big 3 from other resources
  const big3Resources = filteredResources.filter(r => BIG_3_IDS.includes(r.id));
  const otherResources = filteredResources.filter(r => !BIG_3_IDS.includes(r.id));

  // Get icon for resource - supports custom icons from metadata
  const getResourceIcon = (resource: Resource) => {
    const iconType = resource.metadata?.icon_type;
    const iconValue = resource.metadata?.icon_value;

    // Custom icon from metadata
    if (iconType && iconValue) {
      if (iconType === 'url') {
        return <img src={iconValue} alt={resource.name} className="h-full w-full object-contain" />;
      } else if (iconType === 'emoji') {
        return <span className="text-[80%] flex items-center justify-center h-full w-full">{iconValue}</span>;
      } else if (iconType === 'lucide') {
        // Map lucide icon names to components (comprehensive list)
        const iconMap: Record<string, any> = {
          GlobeIcon, BookOpenIcon, VideoIcon, FileTextIcon, LinkIcon,
          DatabaseIcon, FolderIcon, Code2Icon, Server, Cloud, Cpu,
          HardDrive, Network, Terminal, Box, Package, Layers,
          GitBranch, Github, FileCode, FileJson, FileCog, BookMarked,
          GraduationCap, Library, Microscope, FlaskConical, Activity,
          BarChart, LineChart, PieChart, TrendingUp, Calculator, Beaker,
        };
        const IconComponent = iconMap[iconValue];
        if (IconComponent) {
          return <IconComponent className="h-full w-full" />;
        }
      }
    }

    // Fallback to resource type default icons
    switch (resource.resource_type) {
      case 'application':
        return <GlobeIcon className="h-full w-full" />;
      case 'video':
        return <VideoIcon className="h-full w-full" />;
      case 'document':
        return <FileTextIcon className="h-full w-full" />;
      case 'wiki':
        return <BookOpenIcon className="h-full w-full" />;
      case 'link':
        return <LinkIcon className="h-full w-full" />;
      case 'dataset':
        return <DatabaseIcon className="h-full w-full" />;
      default:
        return <FolderIcon className="h-full w-full" />;
    }
  };

  const handleCreate = () => {
    setEditingResource(null);
    setShowForm(true);
  };

  const handleEdit = (resource: Resource) => {
    setEditingResource(resource);
    setShowForm(true);
  };

  const handleDelete = (resource: Resource) => {
    setDeleteConfirm(resource);
  };

  const handleFormSubmit = (data: ResourceFormData) => {
    if (editingResource) {
      updateMutation.mutate({ id: editingResource.id, data });
    } else {
      createMutation.mutate(data);
    }
  };

  const handleSeedDefaults = () => {
    if (confirm('Seed default ExCITE resources (WintEHR, Broadsea, JupyterHub)?')) {
      seedMutation.mutate();
    }
  };

  if (error) {
    console.error('React Query error object:', error);
    return (
      <div className="p-6">
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            Failed to load resources. Please try again later.
            <details className="mt-2">
              <summary className="cursor-pointer text-sm">Error details</summary>
              <pre className="mt-2 text-xs overflow-auto">{JSON.stringify(error, null, 2)}</pre>
            </details>
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  // Debug: Show what we received
  console.log('ResourcesAdmin - resourcesData:', resourcesData);
  console.log('ResourcesAdmin - isLoading:', isLoading);
  console.log('ResourcesAdmin - error:', error);

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-8 animate-fade-in">
      {/* Header */}
      <div className="bg-white rounded-2xl p-8 shadow-xl border-l-4 border-blue-500">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-display font-bold text-gray-900">Resource Management</h1>
            <p className="text-lg text-gray-600 mt-2">
              Manage ExCITE resources and learning materials
            </p>
          </div>
          <div className="flex gap-2">
          <Button onClick={handleSeedDefaults} variant="outline" disabled={seedMutation.isPending}>
            <Download className="h-4 w-4 mr-2" />
            {seedMutation.isPending ? 'Seeding...' : 'Seed Defaults'}
          </Button>
          <Button onClick={handleCreate}>
            <Plus className="h-4 w-4 mr-2" />
            Add Resource
          </Button>
        </div>
        </div>
      </div>

      {/* Search */}
      <div className="mb-6">
        <div className="relative max-w-md">
          <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search resources..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10"
          />
        </div>
      </div>

      {isLoading ? (
        <div className="text-center py-12">
          <p className="text-muted-foreground">Loading resources...</p>
        </div>
      ) : (
        <div className="space-y-8">
          {/* Big 3 ExCITE Apps */}
          {big3Resources.length > 0 && (
            <div>
              <h2 className="text-2xl font-bold mb-4">ExCITE Core Applications</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {big3Resources
                  .sort((a, b) => (a.order || 999) - (b.order || 999))
                  .map((resource) => (
                    <Card
                      key={resource.id}
                      className="relative group shadow-lg hover:shadow-xl transition-all duration-200 border-2 hover:border-primary/50"
                    >
                      <CardHeader className="pb-4">
                        <div className="flex items-center justify-between mb-4">
                          <div className="p-4 rounded-2xl bg-primary/10 text-primary">
                            <div className="h-16 w-16">
                              {getResourceIcon(resource)}
                            </div>
                          </div>
                          <div className="flex gap-1">
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handleEdit(resource)}
                              className="h-8 w-8 p-0"
                            >
                              <Edit className="h-4 w-4" />
                            </Button>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handleDelete(resource)}
                              className="h-8 w-8 p-0 text-destructive"
                            >
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          </div>
                        </div>
                        <CardTitle className="text-xl">{resource.name}</CardTitle>
                        <div className="flex gap-2 mt-2">
                          <Badge variant={resource.is_active ? "default" : "secondary"}>
                            {resource.is_active ? "Active" : "Inactive"}
                          </Badge>
                        </div>
                      </CardHeader>
                      <CardContent>
                        <CardDescription className="mb-4 min-h-[3rem]">
                          {resource.description}
                        </CardDescription>
                        <Button
                          className="w-full"
                          onClick={(e) => {
                            e.stopPropagation();
                            window.open(resource.url, '_blank');
                          }}
                        >
                          <ExternalLink className="h-4 w-4 mr-2" />
                          Open Application
                        </Button>
                      </CardContent>
                    </Card>
                  ))}
              </div>
            </div>
          )}

          {/* Resource Shop - Other Resources */}
          {otherResources.length > 0 && (
            <div>
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-2xl font-bold">Resource Library</h2>
                <span className="text-sm text-muted-foreground">
                  {otherResources.length} resource{otherResources.length !== 1 ? 's' : ''}
                </span>
              </div>
              <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-6 gap-4">
                {otherResources
                  .sort((a, b) => (a.order || 999) - (b.order || 999))
                  .map((resource) => (
                    <Card
                      key={resource.id}
                      className="group shadow-md hover:shadow-lg transition-all duration-200 hover:scale-105 relative"
                    >
                      <CardContent className="p-4">
                        {/* Action buttons */}
                        <div className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity flex gap-1 z-10">
                          <Button
                            variant="secondary"
                            size="sm"
                            onClick={(e) => {
                              e.stopPropagation();
                              handleEdit(resource);
                            }}
                            className="h-6 w-6 p-0"
                          >
                            <Edit className="h-3 w-3" />
                          </Button>
                          <Button
                            variant="secondary"
                            size="sm"
                            onClick={(e) => {
                              e.stopPropagation();
                              handleDelete(resource);
                            }}
                            className="h-6 w-6 p-0 text-destructive"
                          >
                            <Trash2 className="h-3 w-3" />
                          </Button>
                        </div>

                        {/* Clickable area for opening resource */}
                        <div
                          className="cursor-pointer"
                          onClick={() => window.open(resource.url, '_blank')}
                        >
                          {/* Icon */}
                          <div className="flex justify-center mb-3">
                            <div className="p-3 rounded-xl bg-primary/10 text-primary">
                              <div className="h-10 w-10">
                                {getResourceIcon(resource)}
                              </div>
                            </div>
                          </div>

                          {/* Resource name */}
                          <h3 className="text-sm font-semibold text-center mb-1 line-clamp-2 min-h-[2.5rem]">
                            {resource.name}
                          </h3>

                          {/* Type badge */}
                          <div className="flex justify-center">
                            <Badge variant="outline" className="text-xs">
                              {resource.resource_type}
                            </Badge>
                          </div>

                          {/* Course-specific indicator */}
                          {resource.course_specific && (
                            <div className="mt-2 flex justify-center">
                              <Badge variant="secondary" className="text-xs">
                                Class-Specific
                              </Badge>
                            </div>
                          )}

                          {/* Status indicator */}
                          {!resource.is_active && (
                            <div className="mt-2 text-center">
                              <span className="text-xs text-muted-foreground">Inactive</span>
                            </div>
                          )}
                        </div>
                      </CardContent>
                    </Card>
                  ))}
              </div>
            </div>
          )}

          {/* No resources message */}
          {filteredResources.length === 0 && (
            <Card className="shadow-lg">
              <CardContent className="py-12 text-center">
                <p className="text-muted-foreground">No resources found</p>
                {searchQuery && (
                  <p className="text-sm text-muted-foreground mt-2">
                    Try adjusting your search query
                  </p>
                )}
              </CardContent>
            </Card>
          )}
        </div>
      )}

      {/* Resource Form Dialog */}
      {showForm && (
        <ResourceForm
          resource={editingResource}
          onSubmit={handleFormSubmit}
          onCancel={() => {
            setShowForm(false);
            setEditingResource(null);
          }}
          isSubmitting={createMutation.isPending || updateMutation.isPending}
        />
      )}

      {/* Delete Confirmation Dialog */}
      <AlertDialog open={!!deleteConfirm} onOpenChange={() => setDeleteConfirm(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Resource?</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to delete "{deleteConfirm?.name}"? This action cannot be
              undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={() => deleteConfirm && deleteMutation.mutate(deleteConfirm.id)}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
