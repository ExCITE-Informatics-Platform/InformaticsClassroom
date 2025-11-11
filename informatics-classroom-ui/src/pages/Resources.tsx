import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useAuth } from '../hooks/useAuth';
import { resourcesService } from '../services/resources';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Alert, AlertDescription } from '../components/ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Input } from '../components/ui/input';
import { Badge } from '../components/ui/badge';
import { Button } from '../components/ui/button';
import {
  Search,
  AlertCircle,
  GlobeIcon,
  BookOpenIcon,
  VideoIcon,
  FileTextIcon,
  LinkIcon,
  DatabaseIcon,
  FolderIcon,
  Settings
} from 'lucide-react';
import type { Resource, ResourceType } from '../types';
import ResourceCard from '../components/resources/ResourceCard';
import VideoResourceCard from '../components/resources/VideoResourceCard';
import DocumentResourceCard from '../components/resources/DocumentResourceCard';
import { Breadcrumbs } from '../components/common/Breadcrumbs';
import { useBreadcrumbs } from '../hooks/useBreadcrumbs';
import { hasRole } from '../utils/permissions';
import { Role } from '../types';

export default function Resources() {
  const { user } = useAuth();
  const [selectedCourse, setSelectedCourse] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [activeTab, setActiveTab] = useState('all');

  // Fetch all accessible resources
  const { data: resourcesData, isLoading, error } = useQuery({
    queryKey: ['resources', selectedCourse],
    queryFn: async () => {
      const response = await resourcesService.getResources({
        course: selectedCourse !== 'all' ? selectedCourse : undefined,
      });
      console.log('Resources response:', response);
      console.log('Course-specific resources:', response?.course_specific);

      // Check if response indicates an error
      if (!response.success) {
        console.error('API returned error');
        throw new Error('Failed to load resources');
      }

      return response;
    },
  });

  // Extract resources from general and course_specific
  const allResources = [
    ...(resourcesData?.general || []),
    ...(Object.values(resourcesData?.course_specific || {}).flat())
  ];

  const resources = allResources;
  const categories = Array.from(new Set(allResources.map(r => r.category).filter(c => c && c.trim() !== '')));

  // Filter resources based on search and category
  const filteredResources = resources.filter((resource) => {
    const matchesSearch =
      searchQuery === '' ||
      resource.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      resource.description.toLowerCase().includes(searchQuery.toLowerCase());

    const matchesCategory =
      selectedCategory === 'all' ||
      resource.category === selectedCategory;

    return matchesSearch && matchesCategory && resource.is_active;
  });

  // Separate general and course-specific resources
  const generalResources = filteredResources.filter(r => r.course_specific === null);
  const courseResources = filteredResources.filter(r => r.course_specific !== null);

  // Group general resources by category
  const groupedGeneralResources = generalResources.reduce((acc, resource) => {
    const category = resource.category;
    if (!acc[category]) {
      acc[category] = [];
    }
    acc[category].push(resource);
    return acc;
  }, {} as Record<string, Resource[]>);

  // Group course-specific resources by category
  const groupedCourseResources = courseResources.reduce((acc, resource) => {
    const category = resource.category;
    if (!acc[category]) {
      acc[category] = [];
    }
    acc[category].push(resource);
    return acc;
  }, {} as Record<string, Resource[]>);

  // Get icon for resource type
  const getTypeIcon = (type: ResourceType) => {
    switch (type) {
      case 'application':
        return <GlobeIcon className="h-5 w-5" />;
      case 'video':
        return <VideoIcon className="h-5 w-5" />;
      case 'document':
        return <FileTextIcon className="h-5 w-5" />;
      case 'wiki':
        return <BookOpenIcon className="h-5 w-5" />;
      case 'link':
        return <LinkIcon className="h-5 w-5" />;
      case 'dataset':
        return <DatabaseIcon className="h-5 w-5" />;
      default:
        return <FolderIcon className="h-5 w-5" />;
    }
  };

  // Get category display name
  const getCategoryName = (category: string): string => {
    const names: Record<string, string> = {
      'core_tools': 'Core Tools',
      'tutorials': 'Tutorials',
      'documentation': 'Documentation',
      'datasets': 'Datasets',
      'projects': 'Projects',
      'supplemental': 'Supplemental',
      'other': 'Other'
    };
    return names[category] || category;
  };

  // Render resource card based on type
  const renderResourceCard = (resource: Resource) => {
    switch (resource.resource_type) {
      case 'video':
        return <VideoResourceCard key={resource.id} resource={resource} />;
      case 'document':
        return <DocumentResourceCard key={resource.id} resource={resource} />;
      default:
        return <ResourceCard key={resource.id} resource={resource} />;
    }
  };

  if (error) {
    return (
      <div className="p-6">
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            Failed to load resources. Please try again later.
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  const { homeBreadcrumb } = useBreadcrumbs();
  const canManageResources = user && hasRole(user, Role.TA);

  // Build breadcrumbs with course filter if applicable
  const breadcrumbItems = [
    homeBreadcrumb,
    { label: 'Resources' }
  ];

  // Get unique courses from course_specific resources for the filter
  const userCourses = Array.from(
    new Set(
      Object.keys(resourcesData?.course_specific || {}).filter(
        course => (resourcesData?.course_specific?.[course] || []).length > 0
      )
    )
  );

  console.log('User courses for filter:', userCourses);
  console.log('All course_specific data:', resourcesData?.course_specific);

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6 animate-fade-in">
      {/* Breadcrumbs */}
      <Breadcrumbs items={breadcrumbItems} />

      <div className="bg-white rounded-2xl p-8 shadow-xl border-l-4 border-slate-500">
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-3xl font-display font-bold text-gray-900">ExCITE Resources</h1>
            <p className="text-lg text-gray-600 mt-2">
              Access tools, tutorials, documentation, and course materials
            </p>
          </div>
          {canManageResources && selectedCourse !== 'all' && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => window.location.href = `/classes/${selectedCourse}/manage?tab=resources`}
              className="flex items-center gap-2"
            >
              <Settings className="h-4 w-4" />
              Manage {selectedCourse} Resources
            </Button>
          )}
        </div>
      </div>

      {/* Filters */}
      <Card className="shadow-lg">
        <CardContent className="pt-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Search */}
            <div className="relative">
              <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search resources..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10"
              />
            </div>

            {/* Category Filter */}
            <Select value={selectedCategory} onValueChange={setSelectedCategory}>
              <SelectTrigger>
                <SelectValue placeholder="All Categories" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Categories</SelectItem>
                {categories.map((category) => (
                  <SelectItem key={category} value={category}>
                    {getCategoryName(category)}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>

            {/* Course Filter */}
            <Select value={selectedCourse} onValueChange={setSelectedCourse}>
              <SelectTrigger>
                <SelectValue>
                  {selectedCourse === 'all' ? 'All Resources' : selectedCourse}
                </SelectValue>
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Resources</SelectItem>
                {userCourses.length > 0 ? (
                  userCourses.map((course) => (
                    <SelectItem key={course} value={course}>
                      {course.toUpperCase()}
                    </SelectItem>
                  ))
                ) : (
                  <SelectItem value="no-courses" disabled>
                    No course-specific resources
                  </SelectItem>
                )}
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {isLoading ? (
        <div className="text-center py-12">
          <p className="text-muted-foreground">Loading resources...</p>
        </div>
      ) : (
        <Card className="shadow-lg">
          <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
            <TabsList className="grid w-full grid-cols-3 bg-gray-100 p-1 rounded-lg m-6">
              <TabsTrigger
                value="all"
                className="data-[state=active]:bg-white data-[state=active]:shadow-md data-[state=active]:text-slate-700 transition-all duration-200"
              >
                All Resources ({filteredResources.length})
              </TabsTrigger>
              <TabsTrigger
                value="general"
                className="data-[state=active]:bg-white data-[state=active]:shadow-md data-[state=active]:text-slate-700 transition-all duration-200"
              >
                General ({generalResources.length})
              </TabsTrigger>
              <TabsTrigger
                value="course"
                className="data-[state=active]:bg-white data-[state=active]:shadow-md data-[state=active]:text-slate-700 transition-all duration-200"
              >
                Course-Specific ({courseResources.length})
              </TabsTrigger>
            </TabsList>

          {/* All Resources */}
          <TabsContent value="all" className="space-y-6 p-6">
            {/* General Resources Section */}
            {Object.keys(groupedGeneralResources).length > 0 && (
              <>
                <div className="mb-6">
                  <h2 className="text-2xl font-bold text-gray-900 mb-4">General Resources</h2>
                </div>
                {Object.entries(groupedGeneralResources).map(([category, categoryResources]) => (
                  <div key={category}>
                    <div className="flex items-center gap-2 mb-4">
                      <h3 className="text-xl font-semibold">
                        {getCategoryName(category)}
                      </h3>
                      <Badge variant="secondary">{categoryResources.length}</Badge>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
                      {categoryResources
                        .sort((a, b) => (a.order || 999) - (b.order || 999))
                        .map(renderResourceCard)}
                    </div>
                  </div>
                ))}
              </>
            )}

            {/* Course-Specific Resources Section */}
            {Object.keys(groupedCourseResources).length > 0 && (
              <>
                {Object.keys(groupedGeneralResources).length > 0 && (
                  <div className="border-t border-gray-200 my-8"></div>
                )}
                <div className="mb-6">
                  <h2 className="text-2xl font-bold text-gray-900 mb-4">Course-Specific Resources</h2>
                </div>
                {Object.entries(groupedCourseResources).map(([category, categoryResources]) => (
                  <div key={category}>
                    <div className="flex items-center gap-2 mb-4">
                      <h3 className="text-xl font-semibold">
                        {getCategoryName(category)}
                      </h3>
                      <Badge variant="secondary">{categoryResources.length}</Badge>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
                      {categoryResources
                        .sort((a, b) => (a.order || 999) - (b.order || 999))
                        .map(renderResourceCard)}
                    </div>
                  </div>
                ))}
              </>
            )}

            {/* Empty State */}
            {filteredResources.length === 0 && (
              <Card className="shadow-md">
                <CardContent className="py-12 text-center">
                  <p className="text-muted-foreground">No resources found</p>
                </CardContent>
              </Card>
            )}
          </TabsContent>

          {/* General Resources */}
          <TabsContent value="general" className="space-y-6 p-6">
            {Object.entries(groupedGeneralResources).map(([category, categoryResources]) => (
              <div key={category}>
                <div className="flex items-center gap-2 mb-4">
                  <h2 className="text-xl font-semibold">
                    {getCategoryName(category)}
                  </h2>
                  <Badge variant="secondary">{categoryResources.length}</Badge>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {categoryResources
                    .sort((a, b) => (a.order || 999) - (b.order || 999))
                    .map(renderResourceCard)}
                </div>
              </div>
            ))}
            {generalResources.length === 0 && (
              <Card className="shadow-md">
                <CardContent className="py-12 text-center">
                  <p className="text-muted-foreground">No general resources available</p>
                </CardContent>
              </Card>
            )}
          </TabsContent>

          {/* Course-Specific Resources */}
          <TabsContent value="course" className="space-y-6 p-6">
            {Object.entries(groupedCourseResources).map(([category, categoryResources]) => (
              <div key={category}>
                <div className="flex items-center gap-2 mb-4">
                  <h2 className="text-xl font-semibold">
                    {getCategoryName(category)}
                  </h2>
                  <Badge variant="secondary">{categoryResources.length}</Badge>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {categoryResources
                    .sort((a, b) => (a.order || 999) - (b.order || 999))
                    .map(renderResourceCard)}
                </div>
              </div>
            ))}
            {courseResources.length === 0 && (
              <Card className="shadow-md">
                <CardContent className="py-12 text-center">
                  <p className="text-muted-foreground">
                    No course-specific resources available
                  </p>
                </CardContent>
              </Card>
            )}
          </TabsContent>
          </Tabs>
        </Card>
      )}
    </div>
  );
}
