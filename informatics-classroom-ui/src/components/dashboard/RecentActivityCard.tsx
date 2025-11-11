import { DashboardContext } from '../../hooks/useDashboardContext';
import { Card, CardHeader, CardTitle, CardContent } from '../ui/card';
import { BookOpen, CheckCircle, XCircle, Clock } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '../../services/api';

interface RecentActivityCardProps {
  context: DashboardContext;
}

interface StudentDashboardData {
  success: true;
  user: {
    id: string;
    email: string;
    display_name: string;
    team: string;
  };
  courses: string[];
  course_summaries: {
    course: string;
    total_modules: number;
    total_questions: number;
    answered_questions: number;
    correct_questions: number;
    completion_percentage: number;
  }[];
}

interface CoursePerformance {
  course: string;
  completion_percentage: number;
  accuracy: number;
}

/**
 * RecentActivityCard - Shows student's course performance across all enrolled classes
 *
 * Displays when: user is a student in one or more classes
 * Data source: /api/student/dashboard
 */
export function RecentActivityCard({ context }: RecentActivityCardProps) {
  // Fetch dashboard data - hook must be called unconditionally
  const dashboardQuery = useQuery({
    queryKey: ['student-dashboard-performance'],
    queryFn: async () => {
      // apiClient.get() already unwraps response.data
      const data = await apiClient.get<StudentDashboardData>('/api/student/dashboard');

      // Transform to course performance (case-insensitive comparison)
      const coursePerformance: CoursePerformance[] = (data.course_summaries || [])
        .filter(summary => context.studentClasses.some(c => c.class_id.toLowerCase() === summary.course.toLowerCase()))
        .map(summary => ({
          course: summary.course,
          completion_percentage: summary.completion_percentage,
          accuracy: summary.total_questions > 0
            ? (summary.correct_questions / summary.total_questions) * 100
            : 0,
        }));

      return coursePerformance;
    },
    enabled: context.studentClasses.length > 0,
    staleTime: 5 * 60 * 1000, // 5 minutes
    retry: false,
    refetchOnWindowFocus: false,
    refetchOnMount: false,
    refetchOnReconnect: false,
  });

  // Don't render if user is not a student in any class
  if (context.studentClasses.length === 0) return null;

  const getProgressColor = (completion: number) => {
    if (completion >= 80) return 'bg-green-600';
    if (completion >= 50) return 'bg-yellow-600';
    return 'bg-red-600';
  };

  const getAccuracyIcon = (accuracy: number) => {
    if (accuracy >= 80) return <CheckCircle className="h-5 w-5 text-green-600" />;
    if (accuracy >= 60) return <Clock className="h-5 w-5 text-yellow-600" />;
    return <XCircle className="h-5 w-5 text-red-600" />;
  };

  return (
    <Card className="col-span-1 shadow-lg">
      <CardHeader>
        <div className="flex items-center gap-2">
          <BookOpen className="h-5 w-5 text-purple-600" />
          <CardTitle>Course Performance</CardTitle>
        </div>
      </CardHeader>
      <CardContent>
        {dashboardQuery.isLoading ? (
          <div className="space-y-3">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-20 bg-gray-100 rounded-lg animate-pulse" />
            ))}
          </div>
        ) : dashboardQuery.data && dashboardQuery.data.length > 0 ? (
          <div className="space-y-3">
            {dashboardQuery.data.map((course) => (
              <div
                key={course.course}
                className="p-3 border rounded-lg hover:bg-gray-50 transition-colors"
              >
                <div className="flex items-start justify-between mb-2">
                  <div className="flex items-center gap-2">
                    {getAccuracyIcon(course.accuracy)}
                    <div>
                      <p className="text-sm font-semibold text-gray-900">
                        {course.course.toUpperCase()}
                      </p>
                      <p className="text-xs text-gray-600">
                        {Math.round(course.accuracy)}% accuracy
                      </p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-lg font-bold text-gray-900">
                      {Math.round(course.completion_percentage)}%
                    </p>
                    <p className="text-xs text-gray-500">Complete</p>
                  </div>
                </div>
                {/* Progress bar */}
                <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                  <div
                    className={`h-full rounded-full transition-all ${getProgressColor(course.completion_percentage)}`}
                    style={{ width: `${course.completion_percentage}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-8">
            <BookOpen className="h-12 w-12 text-gray-300 mx-auto mb-3" />
            <p className="text-sm text-gray-500">No course data available</p>
            <p className="text-xs text-gray-400 mt-1">
              Start taking quizzes to see your performance
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
