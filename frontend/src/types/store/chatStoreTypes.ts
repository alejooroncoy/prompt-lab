// Chat store types
export interface ChatState {
  messages: Array<{
    id: string;
    role: 'user' | 'assistant' | 'system';
    content: string;
    timestamp: string;
    metadata: Record<string, any>;
  }>;
  currentConversationId?: string;
  selectedProvider?: string;
  isLoading: boolean;
  error?: string;
}

export interface ChatActions {
  sendMessage: (message: string, userId: string) => Promise<void>;
  loadConversation: (conversationId: string) => Promise<void>;
  clearMessages: () => void;
  setSelectedProvider: (provider: string) => void;
  setError: (error: string | undefined) => void;
}

export interface ChatStore extends ChatState, ChatActions {}
