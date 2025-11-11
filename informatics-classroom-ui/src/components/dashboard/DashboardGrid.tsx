import { useAuth } from '../../hooks/useAuth';
import { useDashboardContext } from '../../hooks/useDashboardContext';
import { WelcomeCard } from './WelcomeCard';
import { SystemStatsCard } from './SystemStatsCard';
import { MyCoursesCard } from './MyCoursesCard';
import { TeachingCard } from './TeachingCard';
import { TAAssignmentsCard } from './TAAssignmentsCard';
import { QuickActionsCard } from './QuickActionsCard';
import { RecentActivityCard } from './RecentActivityCard';
import { ClassStatsCard } from './ClassStatsCard';

/**
 * DashboardGrid - Main dashboard layout with role-adaptive components
 *
 * This component:
 * 1. Gets user context and role information
 * 2. Renders a welcome card for all users
 * 3. Shows role-specific dashboard components based on user's class_memberships
 * 4. Arranges components in a flex grid that wraps naturally
 *
 * Components are self-determining:
 * - Each card checks the context and renders only if applicable
 * - No tabs or role switchers needed
 * - All relevant content visible at once
 *
 * Layout:
 * - Welcome card: Full width
 * - System stats (admin): Full width
 * - Role cards: Flex grid (wraps based on screen size)
 */
export function DashboardGrid() {
  const { user } = useAuth();
  const context = useDashboardContext(user);

  if (!user) {
    return (
      <div className="p-6 max-w-7xl mx-auto">
        <div className="text-center py-12">
          <p className="text-gray-500">Loading...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      {/* Welcome Card - Always shown, full width */}
      <WelcomeCard user={user} primaryRole={context.primaryRole} />

      {/* System Stats Card - Admin only, full width */}
      <SystemStatsCard context={context} />

      {/* Role-based component grid - Flex grid, wraps naturally */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {/* Student view - Shows if student in any class */}
        <MyCoursesCard context={context} />

        {/* Instructor view - Shows if instructor in any class */}
        <TeachingCard context={context} />

        {/* TA view - Shows if TA in any class */}
        <TAAssignmentsCard context={context} />

        {/* Student activity - Shows recent quiz attempts */}
        <RecentActivityCard context={context} />

        {/* Instructor stats - Shows aggregated class performance */}
        <ClassStatsCard context={context} />

        {/* Quick Actions - Always shown, actions vary by role */}
        <QuickActionsCard context={context} />
      </div>

      {/* Empty state if no roles */}
      {!context.isAdmin &&
       context.studentClasses.length === 0 &&
       context.instructorClasses.length === 0 &&
       context.taClasses.length === 0 && (
        <div className="text-center py-12 bg-gray-50 rounded-lg border-2 border-dashed border-gray-300">
          <p className="text-gray-600 mb-2">No class memberships found</p>
          <p className="text-sm text-gray-500">
            Contact your administrator to be added to classes
          </p>
        </div>
      )}
    </div>
  );
}
