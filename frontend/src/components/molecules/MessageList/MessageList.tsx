import React from 'react';
import { cn } from '@/utils/helpers';
import { ChatMessage } from '@/components/molecules/ChatMessage';
import type { MessageListProps } from '@/types/components/chatTypes';

export function MessageList({ messages, isLoading, className }: MessageListProps) {
  return (
    <div className={cn('space-y-4', className)}>
      {messages.map((message) => (
        <ChatMessage key={message.id} message={message} />
      ))}
      
      {isLoading && (
        <div className="flex items-center space-x-2 text-gray-500">
          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-primary-600"></div>
          <span className="text-sm">Generando respuesta...</span>
        </div>
      )}
    </div>
  );
}
