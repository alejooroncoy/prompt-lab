// Chat API service
import { httpClient } from '../shared/httpClient';
import type {
  ChatMessageRequest,
  ChatMessageResponse,
  ConversationListResponse,
  ConversationDetail,
  ProvidersResponse,
} from '@/types/api/chatTypes';

export const chatApi = {
  // Send a chat message
  async sendMessage(request: ChatMessageRequest): Promise<ChatMessageResponse> {
    return httpClient.post<ChatMessageResponse>('/chat/message', request);
  },

  // Get user conversations
  async getUserConversations(
    userId: string,
    limit: number = 50,
    offset: number = 0
  ): Promise<ConversationListResponse> {
    return httpClient.get<ConversationListResponse>(
      `/chat/conversations/${userId}?limit=${limit}&offset=${offset}`
    );
  },

  // Get conversation detail
  async getConversationDetail(conversationId: string): Promise<ConversationDetail> {
    return httpClient.get<ConversationDetail>(`/chat/conversations/${conversationId}/detail`);
  },

  // Delete conversation
  async deleteConversation(conversationId: string): Promise<{ message: string }> {
    return httpClient.delete<{ message: string }>(`/chat/conversations/${conversationId}`);
  },

  // Get available providers
  async getAvailableProviders(): Promise<ProvidersResponse> {
    return httpClient.get<ProvidersResponse>('/chat/providers');
  },

  // Search conversations
  async searchConversations(
    userId: string,
    query: string,
    limit: number = 20
  ): Promise<ConversationListResponse> {
    return httpClient.get<ConversationListResponse>(
      `/chat/conversations/${userId}/search?query=${encodeURIComponent(query)}&limit=${limit}`
    );
  },
};
