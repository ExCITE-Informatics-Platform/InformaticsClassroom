import { User, Role } from '../../types';
import { Card, CardContent } from '../ui/card';
import { Badge } from '../ui/badge';
import { Clock } from 'lucide-react';

interface WelcomeCardProps {
  user: User;
  primaryRole: Role;
}

/**
 * Get display-friendly role name with color scheme
 */
function getRoleDisplay(role: Role): { label: string; variant: 'default' | 'secondary' | 'destructive' | 'outline' } {
  switch (role) {
    case Role.ADMIN:
      return { label: 'Administrator', variant: 'destructive' };
    case Role.INSTRUCTOR:
      return { label: 'Instructor', variant: 'default' };
    case Role.TA:
      return { label: 'Teaching Assistant', variant: 'secondary' };
    case Role.STUDENT:
      return { label: 'Student', variant: 'outline' };
    default:
      return { label: 'User', variant: 'outline' };
  }
}

/**
 * Get time-appropriate greeting
 */
function getGreeting(): string {
  const hour = new Date().getHours();
  if (hour < 12) return 'Good morning';
  if (hour < 18) return 'Good afternoon';
  return 'Good evening';
}

/**
 * WelcomeCard component - Personalized welcome message shown to all users
 *
 * Displays:
 * - Time-appropriate greeting
 * - User's display name
 * - Role badge
 * - Current date/time
 */
export function WelcomeCard({ user, primaryRole }: WelcomeCardProps) {
  const roleDisplay = getRoleDisplay(primaryRole);
  const greeting = getGreeting();
  const currentDate = new Date().toLocaleDateString('en-US', {
    weekday: 'long',
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  });

  return (
    <Card className="shadow-lg border-l-4 border-l-amber-500">
      <CardContent className="pt-6">
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 mb-2">
              {greeting}, {user.displayName}!
            </h1>
            <div className="flex items-center gap-3 text-gray-600">
              <Badge variant={roleDisplay.variant} className="font-medium">
                {roleDisplay.label}
              </Badge>
              <span className="flex items-center gap-1 text-sm">
                <Clock className="h-4 w-4" />
                {currentDate}
              </span>
            </div>
          </div>
          {user.roles && user.roles.length > 0 && (
            <div className="text-right">
              <p className="text-sm text-gray-500 mb-1">User ID</p>
              <p className="text-sm font-mono text-gray-700">{user.id || user.username}</p>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
