import { apiClient } from './api';
import type {
  Resource,
  ResourceFormData,
  ResourceFilter,
  ResourceStats,
  ResourcesResponse,
  SeedResourcesResponse,
  ApiResponse,
} from '../types';

export const resourcesService = {
  // ========== PUBLIC/STUDENT ENDPOINTS ==========

  // Get all accessible resources (general + course-specific for user's enrollments)
  getResources: async (filters?: ResourceFilter): Promise<ResourcesResponse> => {
    const response = await apiClient.get<ResourcesResponse>('/api/resources', {
      params: filters,
    });
    return response as ResourcesResponse;
  },

  // Get single resource by ID
  getResource: async (resourceId: string): Promise<Resource> => {
    const response = await apiClient.get<Resource>(`/api/resources/${resourceId}`);
    return response as any as Resource;
  },

  // ========== ADMIN ENDPOINTS ==========

  // Get all general resources (admin only)
  getAdminResources: async (): Promise<ResourcesResponse> => {
    const response = await apiClient.get<ResourcesResponse>('/api/resources/admin');
    return response as ResourcesResponse;
  },

  // Create general resource (admin only)
  createAdminResource: async (resourceData: ResourceFormData): Promise<ApiResponse<Resource>> => {
    const response = await apiClient.post<ApiResponse<Resource>>('/api/resources/admin', resourceData);
    return response as unknown as ApiResponse<Resource>;
  },

  // Update general resource (admin only)
  updateAdminResource: async (resourceId: string, resourceData: Partial<ResourceFormData>): Promise<ApiResponse<Resource>> => {
    const response = await apiClient.put<ApiResponse<Resource>>(`/api/resources/admin/${resourceId}`, resourceData);
    return response as unknown as ApiResponse<Resource>;
  },

  // Delete general resource (admin only)
  deleteAdminResource: async (resourceId: string): Promise<ApiResponse<void>> => {
    const response = await apiClient.delete<ApiResponse<void>>(`/api/resources/admin/${resourceId}`);
    return response as ApiResponse<void>;
  },

  // Get all categories (admin only)
  getCategories: async (): Promise<string[]> => {
    const response = await apiClient.get<string[]>('/api/resources/admin/categories');
    return response as any as string[];
  },

  // Seed default resources (admin only)
  seedResources: async (): Promise<SeedResourcesResponse> => {
    const response = await apiClient.post<SeedResourcesResponse>('/api/resources/seed');
    return response as SeedResourcesResponse;
  },

  // ========== COURSE-SPECIFIC ENDPOINTS ==========

  // Get resources for specific course (instructor/TA/admin)
  getCourseResources: async (courseId: string): Promise<ResourcesResponse> => {
    const response = await apiClient.get<ResourcesResponse>(`/api/resources/course/${courseId}`);
    return response as ResourcesResponse;
  },

  // Create course-specific resource (instructor/TA/admin)
  createCourseResource: async (courseId: string, resourceData: ResourceFormData): Promise<ApiResponse<Resource>> => {
    const response = await apiClient.post<ApiResponse<Resource>>(`/api/resources/course/${courseId}`, resourceData);
    return response as unknown as ApiResponse<Resource>;
  },

  // Update course-specific resource (instructor/TA/admin)
  updateCourseResource: async (courseId: string, resourceId: string, resourceData: Partial<ResourceFormData>): Promise<ApiResponse<Resource>> => {
    const response = await apiClient.put<ApiResponse<Resource>>(`/api/resources/course/${courseId}/${resourceId}`, resourceData);
    return response as unknown as ApiResponse<Resource>;
  },

  // Delete course-specific resource (instructor/TA/admin)
  deleteCourseResource: async (courseId: string, resourceId: string): Promise<ApiResponse<void>> => {
    const response = await apiClient.delete<ApiResponse<void>>(`/api/resources/course/${courseId}/${resourceId}`);
    return response as ApiResponse<void>;
  },

  // Get statistics for course resources (instructor/TA/admin)
  getCourseResourceStats: async (courseId: string): Promise<ResourceStats> => {
    const response = await apiClient.get<ApiResponse<{ stats: ResourceStats }>>(`/api/resources/course/${courseId}/stats`);
    return (response as any).stats as ResourceStats;
  },
};
