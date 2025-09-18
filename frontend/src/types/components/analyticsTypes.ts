// Analytics component types
export interface MetricCardProps {
  title: string;
  value: string | number;
  change?: {
    value: number;
    type: 'increase' | 'decrease' | 'neutral';
  };
  icon?: React.ReactNode;
  className?: string;
}

export interface AnalyticsChartProps {
  data: Array<{
    name: string;
    value: number;
    [key: string]: any;
  }>;
  type: 'line' | 'bar' | 'pie' | 'area';
  title?: string;
  className?: string;
}

export interface SentimentChartProps {
  data: {
    positive: number;
    negative: number;
    neutral: number;
  };
  className?: string;
}

export interface ProviderUsageChartProps {
  data: Record<string, number>;
  className?: string;
}

export interface CostAnalysisChartProps {
  data: Array<{
    date: string;
    cost: number;
  }>;
  className?: string;
}

export interface AnalyticsDashboardProps {
  userId?: string;
  conversationId?: string;
  className?: string;
}

export interface MetricsOverviewProps {
  userMetrics?: {
    total_conversations: number;
    total_messages: number;
    total_tokens_used: number;
    total_cost_usd: number;
    avg_response_time_ms: number;
    most_used_provider?: string;
  };
  className?: string;
}
