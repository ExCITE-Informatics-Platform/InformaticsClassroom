import { useState, useCallback } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '../services/api';
import { useAuth } from './useAuth';

interface User {
  id: string;
  email: string;
  displayName: string;
  roles: string[];
  classRoles?: Record<string, string>;
  class_memberships?: string[];
}

interface ImpersonationStatus {
  impersonating: boolean;
  original_user?: {
    id: string;
    email: string;
    displayName: string;
  };
  current_user?: User;
  started_at?: string;
}

export function useImpersonation() {
  const queryClient = useQueryClient();
  const { refetchSession, user, isAuthenticated } = useAuth();

  // Fetch available users for impersonation
  const { data: usersData, isLoading: usersLoading } = useQuery({
    queryKey: ['admin', 'users'],
    queryFn: async () => {
      const response = await apiClient.get<{ success: boolean; users: User[] }>(
        '/api/admin/users'
      );
      if (!response.success) {
        throw new Error(response.error || 'Failed to fetch users');
      }
      return response.users;
    },
    enabled: isAuthenticated && user?.roles?.includes('admin'), // Only fetch when authenticated and admin
    staleTime: 5 * 60 * 1000, // Cache for 5 minutes
    retry: 3, // Retry failed requests
  });

  // Fetch impersonation status
  const { data: statusData, refetch: refetchStatus } = useQuery({
    queryKey: ['admin', 'impersonation-status'],
    queryFn: async () => {
      const response = await apiClient.get<ImpersonationStatus>(
        '/api/admin/impersonation-status'
      );
      if (!response.success) {
        return { impersonating: false };
      }
      return response;
    },
    enabled: isAuthenticated, // Only fetch when authenticated
    refetchInterval: 30000, // Refetch every 30 seconds
    retry: 1,
  });

  // Start impersonation mutation
  const impersonateMutation = useMutation({
    mutationFn: async (userId: string) => {
      const response = await apiClient.post<{
        success: boolean;
        accessToken: string;
        current_user: User;
        original_user: User;
      }>('/api/admin/impersonate', { user_id: userId });

      if (!response.success) {
        throw new Error('Failed to start impersonation');
      }
      return response;
    },
    onSuccess: (data) => {
      // Update localStorage with new token
      if (data.accessToken) {
        localStorage.setItem('accessToken', data.accessToken);
      }

      // Invalidate and refetch relevant queries
      queryClient.invalidateQueries({ queryKey: ['admin', 'impersonation-status'] });
      refetchSession();
      refetchStatus();

      // Reload the page to apply impersonation context immediately
      // This ensures all components re-render with the new user context
      window.location.reload();
    },
  });

  // Stop impersonation mutation
  const stopImpersonationMutation = useMutation({
    mutationFn: async () => {
      const response = await apiClient.post<{
        success: boolean;
        accessToken: string;
        user: User;
      }>('/api/admin/stop-impersonate');

      if (!response.success) {
        throw new Error('Failed to stop impersonation');
      }
      return response;
    },
    onSuccess: (data) => {
      // Update localStorage with new token
      if (data.accessToken) {
        localStorage.setItem('accessToken', data.accessToken);
      }

      // Invalidate and refetch relevant queries
      queryClient.invalidateQueries({ queryKey: ['admin', 'impersonation-status'] });
      refetchSession();
      refetchStatus();

      // Reload the page to restore original user context
      // This ensures all components re-render with the admin's context
      window.location.reload();
    },
  });

  const startImpersonation = useCallback(
    (userId: string) => {
      return impersonateMutation.mutate(userId);
    },
    [impersonateMutation]
  );

  const stopImpersonation = useCallback(() => {
    return stopImpersonationMutation.mutate();
  }, [stopImpersonationMutation]);

  return {
    users: usersData || [],
    usersLoading,
    impersonating: statusData?.impersonating || false,
    originalUser: statusData?.original_user,
    currentUser: statusData?.current_user,
    startImpersonation,
    stopImpersonation,
    isImpersonating: impersonateMutation.isPending,
    isStoppingImpersonation: stopImpersonationMutation.isPending,
    impersonationError: impersonateMutation.error || stopImpersonationMutation.error,
  };
}
