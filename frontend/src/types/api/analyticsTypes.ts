// Analytics API types
export interface AnalyticsSummaryResponse {
  user_metrics?: {
    user_id: string;
    period_days: number;
    total_conversations: number;
    total_messages: number;
    avg_messages_per_conversation: number;
    total_tokens_used: number;
    total_cost_usd: number;
    avg_response_time_ms: number;
    most_used_provider?: string;
    sentiment_distribution: {
      positive: number;
      negative: number;
      neutral: number;
    };
    activity_trend: 'increasing' | 'decreasing' | 'stable';
  };
  conversation_metrics?: {
    conversation_id: string;
    user_id: string;
    title: string;
    created_at: string;
    updated_at: string;
    total_messages: number;
    total_tokens_used: number;
    total_cost_usd: number;
    avg_response_time_ms: number;
    avg_message_length: number;
    provider_usage: Record<string, number>;
    most_used_provider?: string;
    sentiment_trend: string;
    avg_sentiment?: {
      sentiment: 'positive' | 'negative' | 'neutral';
      polarity: number;
      confidence: number;
    };
    cost_per_message: number;
  };
  global_metrics?: {
    period_days: number;
    total_users: number;
    total_conversations: number;
    total_messages: number;
    total_tokens_used: number;
    total_cost_usd: number;
    avg_response_time_ms: number;
    provider_distribution: Record<string, number>;
    sentiment_distribution: {
      positive: number;
      negative: number;
      neutral: number;
    };
    daily_activity: Array<{
      date: string;
      conversations: number;
      messages: number;
      tokens: number;
    }>;
    avg_messages_per_user: number;
  };
  provider_breakdown: {
    provider_distribution: Record<string, number>;
    provider_percentages: Record<string, number>;
    total_requests: number;
    most_used_provider?: string;
  };
  sentiment_trends: {
    sentiment_distribution: Record<string, number>;
    sentiment_percentages: Record<string, number>;
    total_analyses: number;
    dominant_sentiment?: string;
    sentiment_trend: string;
  };
  cost_analysis: {
    total_cost_usd: number;
    avg_cost_per_message: number;
    avg_cost_per_token: number;
    total_messages: number;
    total_tokens: number;
    cost_by_provider: Record<string, number>;
    daily_cost_trend: Array<{
      date: string;
      cost: number;
    }>;
  };
}

export interface ReportGenerationRequest {
  user_id?: string;
  report_type: 'summary' | 'detailed' | 'export';
  days: number;
  include_conversations: boolean;
  include_analytics: boolean;
  include_recommendations: boolean;
  format: 'json' | 'csv' | 'pdf';
}

export interface ReportGenerationResponse {
  report_id: string;
  report_type: string;
  generated_at: string;
  period_days: number;
  summary: Record<string, any>;
  conversations?: Array<{
    id: string;
    title: string;
    created_at: string;
    updated_at: string;
    message_count: number;
    total_tokens: number;
    avg_response_time: number;
    analytics?: {
      total_cost: number;
      sentiment_trend: string;
      provider_usage: Record<string, number>;
    };
  }>;
  analytics?: Record<string, any>;
  recommendations?: string[];
  export_data?: Record<string, any>;
}
