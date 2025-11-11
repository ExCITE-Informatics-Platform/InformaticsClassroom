import { DashboardContext } from '../../hooks/useDashboardContext';
import { Card, CardHeader, CardTitle, CardContent } from '../ui/card';
import { GraduationCap, Users, BarChart3 } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '../../services/api';
import { useNavigate } from 'react-router-dom';

interface TeachingCardProps {
  context: DashboardContext;
}

interface InstructorClass {
  id: string;
  name?: string;
  students: string[];
  created_at: string;
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

/**
 * TeachingCard - Shows instructor's classes taught with analytics
 *
 * Displays when: user is an instructor in one or more classes
 * Data source: /api/instructor/classes and /api/classes/:class_id/grades
 */
export function TeachingCard({ context }: TeachingCardProps) {
  const navigate = useNavigate();

  // Fetch instructor's classes - hook must be called unconditionally
  const classesQuery = useQuery({
    queryKey: ['instructor-classes'],
    queryFn: async () => {
      // apiClient.get() already unwraps response.data
      const data = await apiClient.get<{ data: { classes: InstructorClass[] } }>(
        '/api/instructor/classes'
      );
      return data.data.classes;
    },
    enabled: context.instructorClasses.length > 0,
    staleTime: 5 * 60 * 1000, // 5 minutes
    retry: false,
    refetchOnWindowFocus: false,
    refetchOnMount: false,
    refetchOnReconnect: false,
  });

  // Fetch student data for each class to calculate stats
  const classStatsQueries = useQuery({
    queryKey: ['instructor-class-stats', context.instructorClasses.map(c => c.class_id)],
    queryFn: async () => {
      const statsData = await Promise.all(
        context.instructorClasses.map(async (membership) => {
          try {
            // apiClient.get() already unwraps response.data
            // Correct endpoint: /api/classes/:class_id/grades
            const data = await apiClient.get<GradesResponse>(
              `/api/classes/${membership.class_id}/grades`
            );

            // Calculate stats from the grades matrix
            const studentCount = data.students.length;
            const grades = data.grades;
            const quizzes = data.quizzes;

            if (studentCount === 0 || quizzes.length === 0) {
              return {
                classId: membership.class_id,
                studentCount: 0,
                avgCompletion: 0,
                avgScore: 0,
              };
            }

            // Calculate average completion and score across all students
            let totalCompletion = 0;
            let totalScore = 0;
            let studentsWithSubmissions = 0;

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
                studentsWithSubmissions++;
                totalCompletion += (submittedQuizzes / quizzes.length) * 100;
                totalScore += totalPercentage / submittedQuizzes;
              }
            });

            return {
              classId: membership.class_id,
              studentCount,
              avgCompletion: studentsWithSubmissions > 0
                ? totalCompletion / studentsWithSubmissions
                : 0,
              avgScore: studentsWithSubmissions > 0
                ? totalScore / studentsWithSubmissions
                : 0,
            };
          } catch {
            return {
              classId: membership.class_id,
              studentCount: 0,
              avgCompletion: 0,
              avgScore: 0,
            };
          }
        })
      );
      return statsData;
    },
    enabled: context.instructorClasses.length > 0,
    staleTime: 5 * 60 * 1000,
    retry: false,
    refetchOnWindowFocus: false,
    refetchOnMount: false,
    refetchOnReconnect: false,
  });

  // Don't render if user is not an instructor in any class
  if (context.instructorClasses.length === 0) return null;

  const handleClassClick = (classId: string) => {
    navigate(`/classes/${classId}/manage`);
  };

  return (
    <Card className="col-span-1 md:col-span-2 shadow-lg hover:shadow-xl transition-shadow">
      <CardHeader>
        <div className="flex items-center gap-2">
          <GraduationCap className="h-5 w-5 text-blue-600" />
          <CardTitle>Teaching ({context.instructorClasses.length})</CardTitle>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {context.instructorClasses.map((membership) => {
            const classInfo = classesQuery.data?.find(c => c.id === membership.class_id);
            const stats = classStatsQueries.data?.find(s => s.classId === membership.class_id);

            return (
              <div
                key={membership.class_id}
                onClick={() => handleClassClick(membership.class_id)}
                className="p-4 border rounded-lg hover:bg-gray-50 hover:border-blue-500 transition-all cursor-pointer"
              >
                <div className="flex items-start justify-between mb-3">
                  <div>
                    <h3 className="font-semibold text-gray-900 text-lg">
                      {membership.class_id.toUpperCase()}
                    </h3>
                    <p className="text-sm text-gray-500">Instructor</p>
                  </div>
                  <div className="text-right">
                    <div className="flex items-center gap-1 text-sm font-medium text-blue-600">
                      Manage Class
                      <span className="text-lg">→</span>
                    </div>
                  </div>
                </div>

                {classesQuery.isLoading || classStatsQueries.isLoading ? (
                  <div className="h-2 bg-gray-200 rounded-full animate-pulse" />
                ) : stats ? (
                  <div className="flex gap-6">
                    <div className="flex items-center gap-2">
                      <Users className="h-4 w-4 text-blue-600" />
                      <div>
                        <p className="text-xs text-gray-600">Students</p>
                        <p className="font-semibold text-gray-900">{stats.studentCount}</p>
                      </div>
                    </div>

                    {stats.avgCompletion > 0 && (
                      <div className="flex items-center gap-2">
                        <BarChart3 className="h-4 w-4 text-green-600" />
                        <div>
                          <p className="text-xs text-gray-600">Avg Completion</p>
                          <p className="font-semibold text-gray-900">
                            {Math.round(stats.avgCompletion)}%
                          </p>
                        </div>
                      </div>
                    )}

                    {stats.avgScore > 0 && (
                      <div className="flex items-center gap-2">
                        <BarChart3 className="h-4 w-4 text-amber-600" />
                        <div>
                          <p className="text-xs text-gray-600">Avg Score</p>
                          <p className="font-semibold text-gray-900">
                            {Math.round(stats.avgScore)}%
                          </p>
                        </div>
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="text-sm text-gray-500">
                    {classInfo ? `${classInfo.students?.length || 0} students` : 'Loading...'}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}
