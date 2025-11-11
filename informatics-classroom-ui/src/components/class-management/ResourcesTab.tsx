import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { resourcesService } from '../../services/resources';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Alert, AlertDescription } from '../ui/alert';
import { Input } from '../ui/input';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '../ui/table';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '../ui/alert-dialog';
import {
  Plus,
  Edit,
  Trash2,
  Search,
  AlertCircle,
  CheckCircle,
  BarChart3,
} from 'lucide-react';
import type { Resource, ResourceFormData } from '../../types';
import ResourceForm from '../resources/ResourceForm';

interface ResourcesTabProps {
  classId: string;
}

export default function ResourcesTab({ classId }: ResourcesTabProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const [showForm, setShowForm] = useState(false);
  const [editingResource, setEditingResource] = useState<Resource | null>(null);
  const [deleteConfirm, setDeleteConfirm] = useState<Resource | null>(null);
  const queryClient = useQueryClient();

  // Fetch course resources
  const { data: resourcesData, isLoading, error } = useQuery({
    queryKey: ['course', 'resources', classId],
    queryFn: async () => {
      const response = await resourcesService.getCourseResources(classId);
      return response;
    },
  });

  // Fetch resource stats
  const { data: statsData } = useQuery({
    queryKey: ['course', 'resources', classId, 'stats'],
    queryFn: async () => {
      return await resourcesService.getCourseResourceStats(classId);
    },
  });

  // Create resource mutation
  const createMutation = useMutation({
    mutationFn: (data: ResourceFormData) =>
      resourcesService.createCourseResource(classId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['course', 'resources', classId] });
      setShowForm(false);
      setEditingResource(null);
    },
  });

  // Update resource mutation
  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<ResourceFormData> }) =>
      resourcesService.updateCourseResource(classId, id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['course', 'resources', classId] });
      setShowForm(false);
      setEditingResource(null);
    },
  });

  // Delete resource mutation
  const deleteMutation = useMutation({
    mutationFn: (id: string) => resourcesService.deleteCourseResource(classId, id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['course', 'resources', classId] });
      setDeleteConfirm(null);
    },
  });

  // Extract resources from API response
  // Course endpoint returns { success, resources } not { general, course_specific }
  const courseResources = resourcesData?.resources || [];
  const filteredResources = courseResources.filter((resource: Resource) => {
    const matchesSearch =
      searchQuery === '' ||
      resource.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      resource.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
      resource.category.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesSearch;
  });

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

  if (error) {
    return (
      <Alert variant="destructive">
        <AlertCircle className="h-4 w-4" />
        <AlertDescription>
          Failed to load resources. Please try again later.
        </AlertDescription>
      </Alert>
    );
  }

  return (
    <div className="space-y-6">
      {/* Stats Cards */}
      {statsData && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card className="shadow-lg">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                Total Resources
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{statsData.total}</div>
            </CardContent>
          </Card>
          <Card className="shadow-lg">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                Active
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-green-600">{statsData.active}</div>
            </CardContent>
          </Card>
          <Card className="shadow-lg">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                Inactive
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-muted-foreground">
                {statsData.inactive}
              </div>
            </CardContent>
          </Card>
          <Card className="shadow-lg">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                Resource Types
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {statsData.by_type ? Object.keys(statsData.by_type).length : 0}
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Header and Actions */}
      <div className="flex items-center justify-between">
        <div className="relative max-w-md">
          <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search course resources..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10"
          />
        </div>
        <Button onClick={handleCreate}>
          <Plus className="h-4 w-4 mr-2" />
          Add Resource
        </Button>
      </div>

      {/* Resources Table */}
      {isLoading ? (
        <div className="text-center py-12">
          <p className="text-muted-foreground">Loading resources...</p>
        </div>
      ) : (
        <Card className="shadow-lg">
          <CardHeader>
            <CardTitle>Course Resources ({filteredResources.length})</CardTitle>
            <CardDescription>
              Manage resources specific to this course
            </CardDescription>
          </CardHeader>
          <CardContent>
            {filteredResources.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                No course-specific resources yet. Click "Add Resource" to create one.
              </div>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Name</TableHead>
                    <TableHead>Type</TableHead>
                    <TableHead>Category</TableHead>
                    <TableHead>URL</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Order</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredResources
                    .sort((a, b) => (a.order || 999) - (b.order || 999))
                    .map((resource: Resource) => (
                      <TableRow key={resource.id}>
                        <TableCell className="font-medium">{resource.name}</TableCell>
                        <TableCell className="capitalize">{resource.resource_type}</TableCell>
                        <TableCell className="capitalize">
                          {resource.category.replace('_', ' ')}
                        </TableCell>
                        <TableCell className="max-w-xs truncate">
                          <a
                            href={resource.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-primary hover:underline"
                          >
                            {resource.url}
                          </a>
                        </TableCell>
                        <TableCell>
                          {resource.is_active ? (
                            <span className="flex items-center gap-1 text-green-600">
                              <CheckCircle className="h-4 w-4" />
                              Active
                            </span>
                          ) : (
                            <span className="flex items-center gap-1 text-muted-foreground">
                              Inactive
                            </span>
                          )}
                        </TableCell>
                        <TableCell>{resource.order}</TableCell>
                        <TableCell className="text-right">
                          <div className="flex justify-end gap-2">
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handleEdit(resource)}
                            >
                              <Edit className="h-4 w-4" />
                            </Button>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handleDelete(resource)}
                            >
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          </div>
                        </TableCell>
                      </TableRow>
                    ))}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>
      )}

      {/* Resource Form Dialog */}
      {showForm && (
        <ResourceForm
          resource={editingResource}
          courseSpecific={classId}
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
