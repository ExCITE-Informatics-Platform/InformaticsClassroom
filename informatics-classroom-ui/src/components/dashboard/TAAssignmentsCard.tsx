import { DashboardContext } from '../../hooks/useDashboardContext';
import { Card, CardHeader, CardTitle, CardContent } from '../ui/card';
import { Users, GraduationCap } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

interface TAAssignmentsCardProps {
  context: DashboardContext;
}

/**
 * TAAssignmentsCard - Shows classes where user is a TA
 *
 * Displays when: user is a TA in one or more classes
 * Data source: class_memberships (filtered by TA role)
 */
export function TAAssignmentsCard({ context }: TAAssignmentsCardProps) {
  const navigate = useNavigate();

  // Don't render if user is not a TA in any class
  if (context.taClasses.length === 0) return null;

  const handleClassClick = (classId: string) => {
    navigate(`/classes/${classId}/manage`);
  };

  return (
    <Card className="col-span-1 shadow-lg hover:shadow-xl transition-shadow">
      <CardHeader>
        <div className="flex items-center gap-2">
          <Users className="h-5 w-5 text-amber-600" />
          <CardTitle>TA Assignments ({context.taClasses.length})</CardTitle>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {context.taClasses.map((membership) => (
            <div
              key={membership.class_id}
              onClick={() => handleClassClick(membership.class_id)}
              className="p-4 border rounded-lg hover:bg-gray-50 hover:border-amber-500 transition-all cursor-pointer"
            >
              <div className="flex items-start justify-between">
                <div>
                  <h3 className="font-semibold text-gray-900 text-lg">
                    {membership.class_id.toUpperCase()}
                  </h3>
                  <div className="flex items-center gap-1 mt-1">
                    <GraduationCap className="h-4 w-4 text-amber-600" />
                    <p className="text-sm text-gray-600">Teaching Assistant</p>
                  </div>
                </div>
                <div className="text-right">
                  <div className="flex items-center gap-1 text-sm font-medium text-amber-600">
                    View Class
                    <span className="text-lg">→</span>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
