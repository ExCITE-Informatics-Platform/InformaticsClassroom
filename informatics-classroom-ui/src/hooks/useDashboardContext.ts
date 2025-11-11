import { useMemo } from 'react';
import { User, Role } from '../types';
import { hasRole } from '../utils/permissions';

export interface ClassMembership {
  class_id: string;
  role: string;
  assigned_at?: string;
  assigned_by?: string;
}

export interface DashboardContext {
  isAdmin: boolean;
  studentClasses: ClassMembership[];
  instructorClasses: ClassMembership[];
  taClasses: ClassMembership[];
  primaryRole: Role;
  hasMultipleRoles: boolean;
}

/**
 * Determine the highest priority role for a user
 * Priority: admin > instructor > ta > student
 */
function determinePrimaryRole(user: User | null): Role {
  if (!user) return Role.STUDENT;

  // Check global roles first
  if (hasRole(user, Role.ADMIN)) return Role.ADMIN;

  // Check class memberships for highest role
  const membershipRoles = new Set<string>();
  const memberships = user.class_memberships || [];

  memberships.forEach(m => {
    if (m.role) membershipRoles.add(m.role);
  });

  // Return highest role based on hierarchy
  if (membershipRoles.has('instructor') || hasRole(user, Role.INSTRUCTOR)) {
    return Role.INSTRUCTOR;
  }
  if (membershipRoles.has('ta') || hasRole(user, Role.TA)) {
    return Role.TA;
  }

  return Role.STUDENT;
}

/**
 * Count the number of distinct roles a user has
 */
function getRoleCount(user: User | null): number {
  if (!user) return 1;

  const roles = new Set<string>();

  // Add global roles
  if (user.roles) {
    user.roles.forEach(r => roles.add(r));
  }

  // Add class-specific roles
  if (user.class_memberships) {
    user.class_memberships.forEach(m => {
      if (m.role) roles.add(m.role);
    });
  }

  return roles.size;
}

/**
 * Hook to provide dashboard context based on user's roles and class memberships
 *
 * This hook analyzes the user's permissions and returns:
 * - Which role dashboards to show (admin, instructor, TA, student)
 * - Which classes the user has for each role
 * - The user's primary role (highest in hierarchy)
 * - Whether the user has multiple roles
 *
 * @param user - The current authenticated user
 * @returns DashboardContext with role-based information
 */
export function useDashboardContext(user: User | null): DashboardContext {
  return useMemo(() => {
    if (!user) {
      return {
        isAdmin: false,
        studentClasses: [],
        instructorClasses: [],
        taClasses: [],
        primaryRole: Role.STUDENT,
        hasMultipleRoles: false,
      };
    }

    const isAdmin = hasRole(user, Role.ADMIN);
    const memberships = user.class_memberships || [];

    // Filter memberships by role
    const studentClasses = memberships.filter(m =>
      m.role === 'student' || m.role === Role.STUDENT
    );

    const instructorClasses = memberships.filter(m =>
      m.role === 'instructor' || m.role === Role.INSTRUCTOR
    );

    const taClasses = memberships.filter(m =>
      m.role === 'ta' || m.role === Role.TA
    );

    return {
      isAdmin,
      studentClasses,
      instructorClasses,
      taClasses,
      primaryRole: determinePrimaryRole(user),
      hasMultipleRoles: getRoleCount(user) > 1,
    };
  }, [user]);
}
