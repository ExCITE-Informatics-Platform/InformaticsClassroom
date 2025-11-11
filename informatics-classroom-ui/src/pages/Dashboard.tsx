import { DashboardGrid } from '../components/dashboard/DashboardGrid';

/**
 * Dashboard - Role-adaptive dashboard page
 *
 * This page uses the DashboardGrid component which:
 * - Analyzes user's roles and class_memberships
 * - Displays relevant dashboard components based on role context
 * - Shows different content for admin, instructor, TA, and student roles
 * - Handles users with multiple roles gracefully
 *
 * Components are self-determining and only render when applicable to the user's role.
 * No tabs or role switching needed - all relevant content is visible at once.
 */
export function Dashboard() {
  return <DashboardGrid />;
}
