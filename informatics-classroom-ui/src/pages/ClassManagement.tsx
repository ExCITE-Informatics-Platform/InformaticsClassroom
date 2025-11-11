import { useState } from 'react';
import { useParams, useSearchParams } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Alert, AlertDescription } from '../components/ui/alert';
import { AlertCircle } from 'lucide-react';
import StudentsTab from '../components/class-management/StudentsTab';
import AssignmentsTab from '../components/class-management/AssignmentsTab';
import GradesTab from '../components/class-management/GradesTab';
import ResourcesTab from '../components/class-management/ResourcesTab';
import { Breadcrumbs } from '../components/common/Breadcrumbs';
import { useBreadcrumbs } from '../hooks/useBreadcrumbs';

export default function ClassManagement() {
  const { classId } = useParams<{ classId: string }>();
  const [searchParams, setSearchParams] = useSearchParams();
  const activeTab = searchParams.get('tab') || 'assignments';
  const { buildClassBreadcrumbs, capitalize } = useBreadcrumbs();

  const handleTabChange = (tab: string) => {
    setSearchParams({ tab });
  };

  if (!classId) {
    return (
      <div className="container mx-auto p-6">
        <Alert variant="destructive" className="border-l-4 border-red-500 shadow-md animate-fade-in">
          <AlertCircle className="h-5 w-5" />
          <AlertDescription className="text-base">
            No class selected. Please select a class to manage.
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  // Build breadcrumbs with class and active tab
  const breadcrumbItems = buildClassBreadcrumbs(classId, [
    { label: capitalize(activeTab) }
  ]);

  return (
    <div className="container mx-auto p-6 space-y-6 animate-fade-in">
      {/* Breadcrumbs */}
      <Breadcrumbs items={breadcrumbItems} />

      {/* Header */}
      <div className="bg-white rounded-2xl p-8 shadow-xl border-l-4 border-amber-500">
        <h1 className="text-3xl font-display font-bold text-gray-900">Class Management</h1>
        <p className="text-lg text-gray-600 mt-2">
          Manage assignments, students, and grades for <span className="font-semibold text-gray-900">{classId}</span>
        </p>
      </div>

      {/* Tabs */}
      <Card className="shadow-lg border-0 bg-white overflow-hidden">
        <Tabs value={activeTab} onValueChange={handleTabChange} className="w-full">
          <div className="bg-gradient-to-b from-gray-50 to-white border-b-2 border-gray-200 px-6 pt-6 pb-4">
            <TabsList className="grid w-full grid-cols-4 bg-white p-1 rounded-lg shadow-sm border-2 border-gray-300">
              <TabsTrigger
                value="assignments"
                className="relative data-[state=active]:bg-amber-500 data-[state=active]:text-white data-[state=active]:shadow-lg data-[state=active]:font-semibold data-[state=inactive]:text-gray-600 data-[state=inactive]:hover:bg-gray-100 transition-all duration-200 rounded-md"
              >
                Assignments
              </TabsTrigger>
              <TabsTrigger
                value="students"
                className="relative data-[state=active]:bg-amber-500 data-[state=active]:text-white data-[state=active]:shadow-lg data-[state=active]:font-semibold data-[state=inactive]:text-gray-600 data-[state=inactive]:hover:bg-gray-100 transition-all duration-200 rounded-md"
              >
                Students
              </TabsTrigger>
              <TabsTrigger
                value="grades"
                className="relative data-[state=active]:bg-amber-500 data-[state=active]:text-white data-[state=active]:shadow-lg data-[state=active]:font-semibold data-[state=inactive]:text-gray-600 data-[state=inactive]:hover:bg-gray-100 transition-all duration-200 rounded-md"
              >
                Grades
              </TabsTrigger>
              <TabsTrigger
                value="resources"
                className="relative data-[state=active]:bg-amber-500 data-[state=active]:text-white data-[state=active]:shadow-lg data-[state=active]:font-semibold data-[state=inactive]:text-gray-600 data-[state=inactive]:hover:bg-gray-100 transition-all duration-200 rounded-md"
              >
                Resources
              </TabsTrigger>
            </TabsList>
          </div>

          <TabsContent value="assignments" className="space-y-4 mt-0 p-6 bg-slate-50/50 min-h-[400px]">
            <AssignmentsTab classId={classId} />
          </TabsContent>

          <TabsContent value="students" className="space-y-4 mt-0 p-6 bg-slate-50/50 min-h-[400px]">
            <StudentsTab classId={classId} />
          </TabsContent>

          <TabsContent value="grades" className="space-y-4 mt-0 p-6 bg-slate-50/50 min-h-[400px]">
            <GradesTab classId={classId} />
          </TabsContent>

          <TabsContent value="resources" className="space-y-4 mt-0 p-6 bg-slate-50/50 min-h-[400px]">
            <ResourcesTab classId={classId} />
          </TabsContent>
        </Tabs>
      </Card>
    </div>
  );
}
