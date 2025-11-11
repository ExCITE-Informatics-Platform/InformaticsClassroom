import { DashboardContext } from '../../hooks/useDashboardContext';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Users, FileText, Shield, ClipboardList, Activity } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '../../services/api';

interface SystemStatsCardProps {
  context: DashboardContext;
}

interface StatItemProps {
  title: string;
  value: string | number;
  icon: React.ComponentType<{ className?: string }>;
  iconColor: string;
  bgColor: string;
}

function StatItem({ title, value, icon: Icon, iconColor, bgColor }: StatItemProps) {
  return (
    <div className="flex items-center gap-3 p-3 rounded-lg border bg-white hover:shadow-md transition-shadow">
      <div className={`p-2 rounded-lg ${bgColor}`}>
        <Icon className={`h-5 w-5 ${iconColor}`} />
      </div>
      <div className="flex-1">
        <p className="text-sm text-gray-600">{title}</p>
        <p className="text-2xl font-bold text-gray-900">
          {typeof value === 'number' ? value.toLocaleString() : value}
        </p>
      </div>
    </div>
  );
}

/**
 * SystemStatsCard - Shows system-wide statistics
 *
 * Displays when: user is a global admin
 * Data source: /api/dashboard/stats
 */
export function SystemStatsCard({ context }: SystemStatsCardProps) {
  // Fetch system stats (hook must be called unconditionally)
  const { data: statsData, isLoading } = useQuery({
    queryKey: ['dashboard', 'stats'],
    queryFn: async () => {
      const response = await apiClient.get<{
        totalUsers: number;
        activeQuizzes: number;
        tokensGenerated: number;
        totalAnswers: number;
      }>('/api/dashboard/stats');
      return response.data;
    },
    staleTime: 60000, // Refetch after 1 minute
    enabled: context.isAdmin, // Only fetch if user is admin
    refetchOnWindowFocus: false,
    refetchOnMount: false,
    refetchOnReconnect: false,
  });

  // Don't render if user is not an admin
  if (!context.isAdmin) return null;

  if (isLoading) {
    return (
      <Card className="col-span-1 lg:col-span-3 shadow-lg">
        <CardHeader>
          <div className="flex items-center gap-2">
            <Activity className="h-5 w-5 text-purple-600 animate-pulse" />
            <CardTitle>System Statistics</CardTitle>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="h-20 bg-gray-100 animate-pulse rounded-lg"></div>
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="col-span-1 lg:col-span-3 shadow-lg border-l-4 border-l-purple-500">
      <CardHeader>
        <div className="flex items-center gap-2">
          <Activity className="h-5 w-5 text-purple-600" />
          <CardTitle>System Statistics</CardTitle>
        </div>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <StatItem
            title="Total Users"
            value={statsData?.totalUsers || 0}
            icon={Users}
            iconColor="text-blue-600"
            bgColor="bg-blue-100"
          />
          <StatItem
            title="Active Quizzes"
            value={statsData?.activeQuizzes || 0}
            icon={FileText}
            iconColor="text-green-600"
            bgColor="bg-green-100"
          />
          <StatItem
            title="Tokens Generated"
            value={statsData?.tokensGenerated || 0}
            icon={Shield}
            iconColor="text-amber-600"
            bgColor="bg-amber-100"
          />
          <StatItem
            title="Total Answers"
            value={statsData?.totalAnswers || 0}
            icon={ClipboardList}
            iconColor="text-purple-600"
            bgColor="bg-purple-100"
          />
        </div>
      </CardContent>
    </Card>
  );
}
