import { DashboardContext } from '../../hooks/useDashboardContext';
import { Card, CardHeader, CardTitle, CardContent } from '../ui/card';
import { Button } from '../ui/button';
import { Settings, FileText, Key, Users as UsersIcon, BookOpen, BarChart3 } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

interface QuickActionsCardProps {
  context: DashboardContext;
}

/**
 * QuickActionsCard - Role-based quick action shortcuts
 *
 * Displays: Different actions based on user's roles
 * Always shown with role-appropriate actions
 */
export function QuickActionsCard({ context }: QuickActionsCardProps) {
  const navigate = useNavigate();

  return (
    <Card className="col-span-1 shadow-lg">
      <CardHeader>
        <div className="flex items-center gap-2">
          <Settings className="h-5 w-5 text-gray-600" />
          <CardTitle>Quick Actions</CardTitle>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          {/* Admin actions */}
          {context.isAdmin && (
            <>
              <Button
                variant="outline"
                className="w-full justify-start"
                onClick={() => navigate('/users')}
              >
                <UsersIcon className="mr-2 h-4 w-4" />
                Manage Users
              </Button>
              <Button
                variant="outline"
                className="w-full justify-start"
                onClick={() => navigate('/permissions')}
              >
                <Key className="mr-2 h-4 w-4" />
                Set Permissions
              </Button>
            </>
          )}

          {/* Instructor actions */}
          {context.instructorClasses.length > 0 && (
            <>
              <Button
                variant="outline"
                className="w-full justify-start"
                onClick={() => navigate('/quizzes/create')}
              >
                <FileText className="mr-2 h-4 w-4" />
                Create Quiz
              </Button>
              <Button
                variant="outline"
                className="w-full justify-start"
                onClick={() => navigate('/classes')}
              >
                <BarChart3 className="mr-2 h-4 w-4" />
                Manage Classes
              </Button>
            </>
          )}

          {/* TA actions */}
          {context.taClasses.length > 0 && (
            <Button
              variant="outline"
              className="w-full justify-start"
              onClick={() => navigate('/classes')}
            >
              <UsersIcon className="mr-2 h-4 w-4" />
              View Classes
            </Button>
          )}

          {/* Student actions */}
          {context.studentClasses.length > 0 && (
            <>
              <Button
                variant="outline"
                className="w-full justify-start"
                onClick={() => navigate('/student-center')}
              >
                <BookOpen className="mr-2 h-4 w-4" />
                My Courses
              </Button>
              <Button
                variant="outline"
                className="w-full justify-start"
                onClick={() => navigate('/resources')}
              >
                <FileText className="mr-2 h-4 w-4" />
                Resources
              </Button>
            </>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
