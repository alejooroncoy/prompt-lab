import React from 'react';
import { cn, formatRelativeTime, truncateText } from '@/utils/helpers';
import { Typography } from '@/components/atoms/Typography';
import { MessageSquare, Clock } from 'lucide-react';
import type { ConversationListProps } from '@/types/components/chatTypes';

export function ConversationList({ 
  conversations, 
  onConversationSelect, 
  selectedConversationId, 
  className 
}: ConversationListProps) {
  return (
    <div className={cn('space-y-2', className)}>
      {conversations.length === 0 ? (
        <div className="text-center py-8">
          <MessageSquare className="w-8 h-8 text-gray-400 mx-auto mb-2" />
          <Typography variant="muted" className="text-sm">
            No hay conversaciones aún
          </Typography>
        </div>
      ) : (
        conversations.map((conversation) => (
          <button
            key={conversation.id}
            onClick={() => onConversationSelect(conversation.id)}
            className={cn(
              'w-full text-left p-3 rounded-lg border transition-colors',
              selectedConversationId === conversation.id
                ? 'border-primary-200 bg-primary-50'
                : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
            )}
          >
            <div className="space-y-1">
              <Typography 
                variant="small" 
                className="font-medium text-gray-900 line-clamp-1"
              >
                {truncateText(conversation.title, 30)}
              </Typography>
              
              <div className="flex items-center space-x-2 text-xs text-gray-500">
                <div className="flex items-center space-x-1">
                  <MessageSquare className="w-3 h-3" />
                  <span>{conversation.message_count}</span>
                </div>
                
                <div className="flex items-center space-x-1">
                  <Clock className="w-3 h-3" />
                  <span>{formatRelativeTime(conversation.updated_at)}</span>
                </div>
              </div>
              
              {conversation.total_tokens > 0 && (
                <div className="text-xs text-gray-500">
                  {conversation.total_tokens.toLocaleString()} tokens
                </div>
              )}
            </div>
          </button>
        ))
      )}
    </div>
  );
}
