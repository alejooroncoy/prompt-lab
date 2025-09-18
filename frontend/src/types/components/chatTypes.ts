// Chat component types
export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
  metadata: Record<string, any>;
}

export interface ChatInterfaceProps {
  className?: string;
  userId?: string;
  conversationId?: string;
}

export interface ChatMessageProps {
  message: ChatMessage;
  className?: string;
}

export interface ChatInputProps {
  onSendMessage: (message: string) => void;
  disabled?: boolean;
  placeholder?: string;
  className?: string;
}

export interface MessageListProps {
  messages: ChatMessage[];
  isLoading?: boolean;
  className?: string;
}

export interface ProviderSelectorProps {
  providers: Array<{
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
  }>;
  selectedProvider?: string;
  onProviderChange: (provider: string) => void;
  className?: string;
}

export interface ConversationListProps {
  conversations: Array<{
    id: string;
    title: string;
    created_at: string;
    updated_at: string;
    message_count: number;
    total_tokens: number;
    avg_response_time: number;
  }>;
  onConversationSelect: (conversationId: string) => void;
  selectedConversationId?: string;
  className?: string;
}
