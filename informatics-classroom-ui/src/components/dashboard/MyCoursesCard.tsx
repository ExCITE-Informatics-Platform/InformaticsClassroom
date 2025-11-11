import { DashboardContext } from '../../hooks/useDashboardContext';
import { Card, CardHeader, CardTitle, CardContent } from '../ui/card';
import { BookOpen, TrendingUp, Award } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '../../services/api';
import { useNavigate } from 'react-router-dom';

interface MyCoursesCardProps {
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

/**
 * MyCoursesCard - Shows student's enrolled courses with progress
 *
 * Displays when: user is a student in one or more classes
 * Data source: /api/student/dashboard/:class
 */
export function MyCoursesCard({ context }: MyCoursesCardProps) {
  const navigate = useNavigate();

  // Fetch dashboard data (includes all courses) - hook must be called unconditionally
  const dashboardQuery = useQuery({
    queryKey: ['student-dashboard'],
    queryFn: async () => {
      // apiClient.get() already unwraps response.data, so we get the data directly
      const data = await apiClient.get<StudentDashboardData>('/api/student/dashboard');
      return data;
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

  const handleCourseClick = (classId: string) => {
    navigate(`/student?class=${classId}`);
  };

  return (
    <Card className="col-span-1 md:col-span-2 shadow-lg hover:shadow-xl transition-shadow">
      <CardHeader>
        <div className="flex items-center gap-2">
          <BookOpen className="h-5 w-5 text-green-600" />
          <CardTitle>My Courses ({context.studentClasses.length})</CardTitle>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {context.studentClasses.map((membership) => {
            // Find course summary data (case-insensitive comparison)
            const courseSummary = dashboardQuery.data?.course_summaries?.find(
              summary => summary.course.toLowerCase() === membership.class_id.toLowerCase()
            );

            const completion = courseSummary?.completion_percentage || 0;
            const moduleCount = courseSummary?.total_modules || 0;
            const answeredQuestions = courseSummary?.answered_questions || 0;
            const correctQuestions = courseSummary?.correct_questions || 0;
            const totalQuestions = courseSummary?.total_questions || 0;

            // Calculate average score
            const avgScore = totalQuestions > 0
              ? (correctQuestions / totalQuestions) * 100
              : 0;

            return (
              <div
                key={membership.class_id}
                onClick={() => handleCourseClick(membership.class_id)}
                className="p-4 border rounded-lg hover:bg-gray-50 hover:border-green-500 transition-all cursor-pointer"
              >
                <div className="flex items-start justify-between mb-3">
                  <div>
                    <h3 className="font-semibold text-gray-900 text-lg">
                      {membership.class_id.toUpperCase()}
                    </h3>
                    <p className="text-sm text-gray-500">
                      {moduleCount > 0 ? `${moduleCount} modules` : 'Loading...'}
                    </p>
                  </div>
                  <div className="text-right">
                    <div className="flex items-center gap-1 text-sm font-medium text-green-600">
                      View Progress
                      <span className="text-lg">→</span>
                    </div>
                  </div>
                </div>

                {dashboardQuery.isLoading ? (
                  <div className="h-2 bg-gray-200 rounded-full animate-pulse" />
                ) : courseSummary ? (
                  <>
                    {/* Progress bar */}
                    <div className="mb-2">
                      <div className="flex justify-between items-center mb-1">
                        <span className="text-xs text-gray-600">Completion</span>
                        <span className="text-xs font-semibold text-gray-900">
                          {Math.round(completion)}%
                        </span>
                      </div>
                      <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-green-600 rounded-full transition-all"
                          style={{ width: `${completion}%` }}
                        />
                      </div>
                    </div>

                    {/* Stats */}
                    <div className="flex gap-4 mt-3">
                      {avgScore > 0 && (
                        <div className="flex items-center gap-1 text-sm">
                          <Award className="h-4 w-4 text-amber-600" />
                          <span className="text-gray-600">Accuracy:</span>
                          <span className="font-semibold text-gray-900">
                            {Math.round(avgScore)}%
                          </span>
                        </div>
                      )}
                      <div className="flex items-center gap-1 text-sm">
                        <TrendingUp className="h-4 w-4 text-blue-600" />
                        <span className="text-gray-600">Modules:</span>
                        <span className="font-semibold text-gray-900">
                          {moduleCount}
                        </span>
                      </div>
                    </div>
                  </>
                ) : (
                  <div className="text-sm text-gray-500">No progress data</div>
                )}
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}
