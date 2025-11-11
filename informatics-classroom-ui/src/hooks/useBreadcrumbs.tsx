import { Home } from 'lucide-react';
import { BreadcrumbItem } from '../components/common/Breadcrumbs';

/**
 * Hook providing common breadcrumb patterns and utilities
 */
export function useBreadcrumbs() {
  /**
   * Standard home/dashboard breadcrumb
   */
  const homeBreadcrumb: BreadcrumbItem = {
    label: 'Dashboard',
    path: '/',
    icon: <Home className="h-4 w-4" />
  };

  /**
   * Helper to capitalize first letter of a string (for tab names, etc.)
   */
  const capitalize = (str: string): string => {
    if (!str) return '';
    return str.charAt(0).toUpperCase() + str.slice(1).toLowerCase();
  };

  /**
   * Helper to build breadcrumbs for class-related pages
   */
  const buildClassBreadcrumbs = (
    classId: string,
    additionalItems?: BreadcrumbItem[]
  ): BreadcrumbItem[] => {
    const items: BreadcrumbItem[] = [
      homeBreadcrumb,
      { label: 'Classes', path: '/classes' },
      { label: classId, path: `/classes/${classId}/manage` }
    ];

    if (additionalItems) {
      items.push(...additionalItems);
    }

    return items;
  };

  /**
   * Helper to build breadcrumbs for quiz-related pages
   */
  const buildQuizBreadcrumbs = (
    mode: 'create' | 'edit',
    quizName?: string
  ): BreadcrumbItem[] => {
    const items: BreadcrumbItem[] = [
      homeBreadcrumb,
      { label: 'Quiz Builder', path: '/quiz/create' }
    ];

    if (mode === 'create') {
      items.push({ label: 'Create' });
    } else if (mode === 'edit') {
      items.push({ label: quizName ? `Edit: ${quizName}` : 'Edit' });
    }

    return items;
  };

  return {
    homeBreadcrumb,
    capitalize,
    buildClassBreadcrumbs,
    buildQuizBreadcrumbs
  };
}
