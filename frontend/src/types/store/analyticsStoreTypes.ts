// Analytics store types
export interface AnalyticsState {
  userMetrics?: {
    total_conversations: number;
    total_messages: number;
    total_tokens_used: number;
    total_cost_usd: number;
    avg_response_time_ms: number;
    most_used_provider?: string;
  };
  conversationMetrics?: {
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
  globalMetrics?: {
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
  providerBreakdown: {
    provider_distribution: Record<string, number>;
    provider_percentages: Record<string, number>;
    total_requests: number;
    most_used_provider?: string;
  };
  sentimentTrends: {
    sentiment_distribution: Record<string, number>;
    sentiment_percentages: Record<string, number>;
    total_analyses: number;
    dominant_sentiment?: string;
    sentiment_trend: string;
  };
  costAnalysis: {
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
  isLoading: boolean;
  error?: string;
}

export interface AnalyticsActions {
  loadUserMetrics: (userId: string, days?: number) => Promise<void>;
  loadConversationMetrics: (conversationId: string) => Promise<void>;
  loadGlobalMetrics: (days?: number) => Promise<void>;
  loadAnalyticsSummary: (userId?: string, conversationId?: string, days?: number) => Promise<void>;
  clearError: () => void;
}

export interface AnalyticsStore extends AnalyticsState, AnalyticsActions {}
