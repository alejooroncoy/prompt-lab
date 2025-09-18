'use client';

import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { cn } from '@/utils/helpers';
import { chatApi } from '@/services/api/chat';
import { Button } from '@/components/atoms/Button';
import { Input } from '@/components/atoms/Input';
import { Typography } from '@/components/atoms/Typography';
import { MessageList } from '@/components/molecules/MessageList';
import { ProviderSelector } from '@/components/molecules/ProviderSelector';
import { ConversationList } from '@/components/molecules/ConversationList';
import { Send, Bot, User, Loader2 } from 'lucide-react';

interface ChatInterfaceProps {
  className?: string;
  userId?: string;
  conversationId?: string;
}

export function ChatInterface({ 
  className, 
  userId = 'demo-user',
  conversationId 
}: ChatInterfaceProps) {
  const [message, setMessage] = useState('');
  const [selectedProvider, setSelectedProvider] = useState<string>('');
  const [currentConversationId, setCurrentConversationId] = useState<string | undefined>(conversationId);
  
  const queryClient = useQueryClient();

  // Get available providers
  const { data: providersData } = useQuery({
    queryKey: ['providers'],
    queryFn: () => chatApi.getAvailableProviders(),
  });

  // Get user conversations
  const { data: conversationsData } = useQuery({
    queryKey: ['conversations', userId],
    queryFn: () => chatApi.getUserConversations(userId),
    enabled: !!userId,
  });

  // Get conversation detail if conversationId is provided
  const { data: conversationData } = useQuery({
    queryKey: ['conversation', currentConversationId],
    queryFn: () => chatApi.getConversationDetail(currentConversationId!),
    enabled: !!currentConversationId,
  });

  // Send message mutation
  const sendMessageMutation = useMutation({
    mutationFn: (messageText: string) => 
      chatApi.sendMessage({
        user_id: userId,
        message: messageText,
        conversation_id: currentConversationId,
        preferred_provider: selectedProvider || undefined,
      }),
    onSuccess: (response) => {
      setMessage('');
      setCurrentConversationId(response.conversation_id);
      
      // Invalidate and refetch conversations
      queryClient.invalidateQueries({ queryKey: ['conversations', userId] });
      queryClient.invalidateQueries({ queryKey: ['conversation', response.conversation_id] });
    },
    onError: (error) => {
      console.error('Error sending message:', error);
    },
  });

  // Set default provider when providers are loaded
  useEffect(() => {
    if (providersData?.providers && !selectedProvider) {
      setSelectedProvider(providersData.providers[0]?.provider || '');
    }
  }, [providersData, selectedProvider]);

  const handleSendMessage = () => {
    if (message.trim() && !sendMessageMutation.isPending) {
      sendMessageMutation.mutate(message.trim());
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const handleConversationSelect = (conversationId: string) => {
    setCurrentConversationId(conversationId);
  };

  const messages = conversationData?.messages || [];

  return (
    <div className={cn('flex flex-col h-full', className)}>
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-gray-200 bg-white">
        <div>
          <Typography variant="h3" className="text-lg font-semibold">
            Chat Laboratory
          </Typography>
          <Typography variant="muted" className="text-sm">
            Experimenta con diferentes LLM providers
          </Typography>
        </div>
        
        {providersData && (
          <ProviderSelector
            providers={providersData.providers}
            selectedProvider={selectedProvider}
            onProviderChange={setSelectedProvider}
          />
        )}
      </div>

      <div className="flex flex-1 overflow-hidden">
        {/* Conversations Sidebar */}
        <div className="w-80 border-r border-gray-200 bg-white overflow-y-auto">
          <div className="p-4">
            <Typography variant="h4" className="text-base font-medium mb-3">
              Conversaciones
            </Typography>
            
            {conversationsData && (
              <ConversationList
                conversations={conversationsData.conversations}
                onConversationSelect={handleConversationSelect}
                selectedConversationId={currentConversationId}
              />
            )}
          </div>
        </div>

        {/* Chat Area */}
        <div className="flex-1 flex flex-col">
          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4">
            {messages.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-full text-center">
                <Bot className="w-12 h-12 text-gray-400 mb-4" />
                <Typography variant="h4" className="text-lg font-medium text-gray-900 mb-2">
                  ¡Bienvenido al Laboratorio de Prompts!
                </Typography>
                <Typography variant="muted" className="text-gray-600 max-w-md">
                  Comienza una conversación escribiendo un mensaje. Puedes experimentar con diferentes 
                  proveedores de LLM y analizar las respuestas en tiempo real.
                </Typography>
              </div>
            ) : (
              <MessageList messages={messages} />
            )}
          </div>

          {/* Input Area */}
          <div className="border-t border-gray-200 bg-white p-4">
            <div className="flex space-x-2">
              <Input
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Escribe tu mensaje aquí..."
                disabled={sendMessageMutation.isPending}
                className="flex-1"
              />
              <Button
                onClick={handleSendMessage}
                disabled={!message.trim() || sendMessageMutation.isPending}
                size="icon"
              >
                {sendMessageMutation.isPending ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Send className="w-4 h-4" />
                )}
              </Button>
            </div>
            
            {sendMessageMutation.isError && (
              <div className="mt-2 text-sm text-error-600">
                Error al enviar mensaje. Inténtalo de nuevo.
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
