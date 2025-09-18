import React from 'react';
import { cn, formatRelativeTime, getSentimentColor } from '@/utils/helpers';
import { Typography } from '@/components/atoms/Typography';
import { User, Bot } from 'lucide-react';
import type { ChatMessageProps } from '@/types/components/chatTypes';

export function ChatMessage({ message, className }: ChatMessageProps) {
  const isUser = message.role === 'user';
  const isAssistant = message.role === 'assistant';
  
  // Get sentiment analysis if available
  const sentimentAnalysis = message.metadata?.sentiment_analysis;
  const provider = message.metadata?.provider;
  const responseTime = message.metadata?.response_time_ms;
  const tokensUsed = message.metadata?.tokens_used;

  return (
    <div className={cn(
      'flex space-x-3',
      isUser ? 'justify-end' : 'justify-start',
      className
    )}>
      {!isUser && (
        <div className="flex-shrink-0">
          <div className="w-8 h-8 bg-primary-100 rounded-full flex items-center justify-center">
            <Bot className="w-4 h-4 text-primary-600" />
          </div>
        </div>
      )}
      
      <div className={cn(
        'max-w-xs lg:max-w-md xl:max-w-lg',
        isUser ? 'order-first' : 'order-last'
      )}>
        <div className={cn(
          'rounded-lg px-4 py-2',
          isUser 
            ? 'bg-primary-600 text-white' 
            : 'bg-white border border-gray-200'
        )}>
          <Typography 
            variant="p" 
            className={cn(
              'text-sm whitespace-pre-wrap',
              isUser ? 'text-white' : 'text-gray-900'
            )}
          >
            {message.content}
          </Typography>
        </div>
        
        {/* Message metadata */}
        <div className={cn(
          'mt-1 flex items-center space-x-2 text-xs text-gray-500',
          isUser ? 'justify-end' : 'justify-start'
        )}>
          <span>{formatRelativeTime(message.timestamp)}</span>
          
          {isAssistant && (
            <>
              {provider && (
                <>
                  <span>•</span>
                  <span className={cn(
                    'px-1.5 py-0.5 rounded text-xs font-medium',
                    provider === 'gemini' ? 'bg-blue-100 text-blue-800' :
                    provider === 'openai' ? 'bg-green-100 text-green-800' :
                    'bg-gray-100 text-gray-800'
                  )}>
                    {provider.toUpperCase()}
                  </span>
                </>
              )}
              
              {responseTime && (
                <>
                  <span>•</span>
                  <span>{responseTime.toFixed(0)}ms</span>
                </>
              )}
              
              {tokensUsed && (
                <>
                  <span>•</span>
                  <span>{tokensUsed} tokens</span>
                </>
              )}
            </>
          )}
        </div>
        
        {/* Sentiment analysis */}
        {sentimentAnalysis && (
          <div className={cn(
            'mt-1 flex items-center space-x-1',
            isUser ? 'justify-end' : 'justify-start'
          )}>
            <span className={cn(
              'px-2 py-0.5 rounded-full text-xs font-medium',
              getSentimentColor(sentimentAnalysis.sentiment)
            )}>
              {sentimentAnalysis.sentiment === 'positive' ? '😊' :
               sentimentAnalysis.sentiment === 'negative' ? '😞' : '😐'} 
              {sentimentAnalysis.sentiment}
            </span>
            <span className="text-xs text-gray-500">
              ({Math.round(sentimentAnalysis.confidence * 100)}%)
            </span>
          </div>
        )}
      </div>
      
      {isUser && (
        <div className="flex-shrink-0">
          <div className="w-8 h-8 bg-gray-100 rounded-full flex items-center justify-center">
            <User className="w-4 h-4 text-gray-600" />
          </div>
        </div>
      )}
    </div>
  );
}
