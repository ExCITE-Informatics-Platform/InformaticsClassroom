import { DashboardContext } from '../../hooks/useDashboardContext';
import { Card, CardHeader, CardTitle, CardContent } from '../ui/card';
import { BarChart3, Users, TrendingUp, Award } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '../../services/api';

interface ClassStatsCardProps {
  context: DashboardContext;
}

interface GradesResponse {
  success: boolean;
  students: string[];  // Array of student IDs
  quizzes: {
    id: string;
    module: number;
    title: string;
    question_count: number;
  }[];
  grades: {
    [studentId: string]: {
      [quizId: string]: {
        score: number;
        total: number;
        percentage: number;
        submitted: boolean;
      };
    };
  };
}

interface ClassStats {
  totalStudents: number;
  avgCompletion: number;
  avgScore: number;
  activeStudents: number; // Students with any progress
}

/**
 * ClassStatsCard - Shows aggregated statistics across all instructor's classes
 *
 * Displays when: user is an instructor in one or more classes
 * Data source: Aggregates data from /api/classes/:class_id/grades
 */
export function ClassStatsCard({ context }: ClassStatsCardProps) {
  // Fetch and aggregate stats across all classes - hook must be called unconditionally
  const statsQuery = useQuery({
    queryKey: ['instructor-aggregate-stats', context.instructorClasses.map(c => c.class_id)],
    queryFn: async () => {
      let totalStudents = 0;
      let totalCompletion = 0;
      let totalScore = 0;
      let activeStudents = 0;

      await Promise.all(
        context.instructorClasses.map(async (membership) => {
          try {
            // apiClient.get() already unwraps response.data
            // Correct endpoint: /api/classes/:class_id/grades
            const data = await apiClient.get<GradesResponse>(
              `/api/classes/${membership.class_id}/grades`
            );

            const studentCount = data.students.length;
            const grades = data.grades;
            const quizzes = data.quizzes;

            totalStudents += studentCount;

            if (studentCount === 0 || quizzes.length === 0) {
              return; // Skip this class
            }

            // Calculate stats for this class
            data.students.forEach(studentId => {
              const studentGrades = grades[studentId] || {};
              let submittedQuizzes = 0;
              let totalPercentage = 0;

              quizzes.forEach(quiz => {
                const quizGrade = studentGrades[quiz.id];
                if (quizGrade?.submitted) {
                  submittedQuizzes++;
                  totalPercentage += quizGrade.percentage;
                }
              });

              if (submittedQuizzes > 0) {
                activeStudents++;
                totalCompletion += (submittedQuizzes / quizzes.length) * 100;
                totalScore += totalPercentage / submittedQuizzes;
              }
            });
          } catch {
            // Skip if class data unavailable
          }
        })
      );

      const stats: ClassStats = {
        totalStudents,
        avgCompletion: activeStudents > 0
          ? totalCompletion / activeStudents
          : 0,
        avgScore: activeStudents > 0
          ? totalScore / activeStudents
          : 0,
        activeStudents,
      };

      return stats;
    },
    enabled: context.instructorClasses.length > 0,
    staleTime: 5 * 60 * 1000, // 5 minutes
    retry: false,
    refetchOnWindowFocus: false,
    refetchOnMount: false,
    refetchOnReconnect: false,
  });

  // Don't render if user is not an instructor in any class
  if (context.instructorClasses.length === 0) return null;

  const stats = statsQuery.data;

  return (
    <Card className="col-span-1 shadow-lg">
      <CardHeader>
        <div className="flex items-center gap-2">
          <BarChart3 className="h-5 w-5 text-indigo-600" />
          <CardTitle>Class Overview</CardTitle>
        </div>
      </CardHeader>
      <CardContent>
        {statsQuery.isLoading ? (
          <div className="space-y-4">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="h-16 bg-gray-100 rounded-lg animate-pulse" />
            ))}
          </div>
        ) : stats ? (
          <div className="space-y-4">
            {/* Total Students */}
            <div className="p-3 bg-blue-50 rounded-lg border border-blue-200">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-blue-100 rounded-lg">
                  <Users className="h-5 w-5 text-blue-600" />
                </div>
                <div className="flex-1">
                  <p className="text-xs text-blue-600 font-medium">Total Students</p>
                  <p className="text-2xl font-bold text-blue-900">{stats.totalStudents}</p>
                </div>
              </div>
              {stats.activeStudents > 0 && (
                <p className="text-xs text-blue-600 mt-2">
                  {stats.activeStudents} active ({Math.round((stats.activeStudents / stats.totalStudents) * 100)}%)
                </p>
              )}
            </div>

            {/* Average Completion */}
            {stats.avgCompletion > 0 && (
              <div className="p-3 bg-green-50 rounded-lg border border-green-200">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-green-100 rounded-lg">
                    <TrendingUp className="h-5 w-5 text-green-600" />
                  </div>
                  <div className="flex-1">
                    <p className="text-xs text-green-600 font-medium">Avg Completion</p>
                    <p className="text-2xl font-bold text-green-900">
                      {Math.round(stats.avgCompletion)}%
                    </p>
                  </div>
                </div>
                <div className="mt-2 h-2 bg-green-100 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-green-600 rounded-full transition-all"
                    style={{ width: `${stats.avgCompletion}%` }}
                  />
                </div>
              </div>
            )}

            {/* Average Score */}
            {stats.avgScore > 0 && (
              <div className="p-3 bg-amber-50 rounded-lg border border-amber-200">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-amber-100 rounded-lg">
                    <Award className="h-5 w-5 text-amber-600" />
                  </div>
                  <div className="flex-1">
                    <p className="text-xs text-amber-600 font-medium">Avg Score</p>
                    <p className="text-2xl font-bold text-amber-900">
                      {Math.round(stats.avgScore)}%
                    </p>
                  </div>
                </div>
                <div className="mt-2 h-2 bg-amber-100 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-amber-600 rounded-full transition-all"
                    style={{ width: `${stats.avgScore}%` }}
                  />
                </div>
              </div>
            )}

            {/* Classes Count */}
            <div className="pt-3 border-t">
              <div className="flex items-center justify-between text-sm">
                <span className="text-gray-600">Teaching</span>
                <span className="font-semibold text-gray-900">
                  {context.instructorClasses.length} {context.instructorClasses.length === 1 ? 'class' : 'classes'}
                </span>
              </div>
            </div>
          </div>
        ) : (
          <div className="text-center py-8">
            <BarChart3 className="h-12 w-12 text-gray-300 mx-auto mb-3" />
            <p className="text-sm text-gray-500">No class data available</p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
