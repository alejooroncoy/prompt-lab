// Chat API types
export interface ChatMessageRequest {
  user_id: string;
  message: string;
  conversation_id?: string;
  preferred_provider?: string;
  template_id?: string;
  template_variables?: Record<string, any>;
  metadata?: Record<string, any>;
}

export interface ChatMessageResponse {
  conversation_id: string;
  user_message: {
    id: string;
    role: 'user' | 'assistant' | 'system';
    content: string;
    timestamp: string;
    metadata: Record<string, any>;
  };
  assistant_message: {
    id: string;
    role: 'user' | 'assistant' | 'system';
    content: string;
    timestamp: string;
    metadata: Record<string, any>;
  };
  provider_used: string;
  response_time_ms: number;
  tokens_used: number;
  cost_usd: number;
  sentiment_analysis?: {
    sentiment: 'positive' | 'negative' | 'neutral';
    polarity: number;
    subjectivity: number;
    confidence: number;
  };
  metadata?: Record<string, any>;
}

export interface Conversation {
  id: string;
  user_id: string;
  title: string;
  created_at: string;
  updated_at: string;
  message_count: number;
  total_tokens: number;
  avg_response_time: number;
}

export interface ConversationDetail {
  id: string;
  user_id: string;
  title: string;
  created_at: string;
  updated_at: string;
  messages: Array<{
    id: string;
    role: 'user' | 'assistant' | 'system';
    content: string;
    timestamp: string;
    metadata: Record<string, any>;
  }>;
  metadata: Record<string, any>;
}

export interface ConversationListResponse {
  conversations: Conversation[];
  total: number;
  limit: number;
  offset: number;
}

export interface LLMProvider {
  provider: string;
  info: {
    provider: string;
    model_name: string;
    capabilities: string[];
    max_tokens: number;
    supported_languages: string[];
    pricing: {
      input: number;
      output: number;
    };
    rate_limits: {
      requests_per_minute: number;
      tokens_per_minute: number;
    };
  };
}

export interface ProvidersResponse {
  providers: LLMProvider[];
}
