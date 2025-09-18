// Analytics API service
import { httpClient } from '../shared/httpClient';
import type {
  AnalyticsSummaryResponse,
  ReportGenerationRequest,
  ReportGenerationResponse,
} from '@/types/api/analyticsTypes';

export const analyticsApi = {
  // Get analytics summary
  async getAnalyticsSummary(
    userId?: string,
    conversationId?: string,
    days: number = 30,
    includeGlobal: boolean = false
  ): Promise<AnalyticsSummaryResponse> {
    const params = new URLSearchParams();
    if (userId) params.append('user_id', userId);
    if (conversationId) params.append('conversation_id', conversationId);
    params.append('days', days.toString());
    params.append('include_global', includeGlobal.toString());

    return httpClient.get<AnalyticsSummaryResponse>(`/analytics/summary?${params.toString()}`);
  },

  // Get user analytics
  async getUserAnalytics(
    userId: string,
    days: number = 30
  ): Promise<{
    user_id: string;
    period_days: number;
    summary: any;
  }> {
    return httpClient.get(`/analytics/user/${userId}?days=${days}`);
  },

  // Get conversation analytics
  async getConversationAnalytics(conversationId: string): Promise<{
    conversation_id: string;
    analytics: any;
  }> {
    return httpClient.get(`/analytics/conversation/${conversationId}`);
  },

  // Get global analytics
  async getGlobalAnalytics(days: number = 30): Promise<{
    period_days: number;
    global_summary: any;
  }> {
    return httpClient.get(`/analytics/global?days=${days}`);
  },

  // Generate report
  async generateReport(request: ReportGenerationRequest): Promise<ReportGenerationResponse> {
    return httpClient.post<ReportGenerationResponse>('/analytics/report', request);
  },

  // Export user data
  async exportUserData(
    userId: string,
    days: number = 30,
    format: string = 'json'
  ): Promise<any> {
    return httpClient.get(`/analytics/export/${userId}?days=${days}&format=${format}`);
  },
};
