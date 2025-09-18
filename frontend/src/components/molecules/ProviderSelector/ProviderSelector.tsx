import React from 'react';
import { cn, getProviderColor } from '@/utils/helpers';
import { Typography } from '@/components/atoms/Typography';
import type { ProviderSelectorProps } from '@/types/components/chatTypes';

export function ProviderSelector({ 
  providers, 
  selectedProvider, 
  onProviderChange, 
  className 
}: ProviderSelectorProps) {
  return (
    <div className={cn('space-y-2', className)}>
      <Typography variant="small" className="text-gray-600">
        Proveedor LLM:
      </Typography>
      
      <div className="flex flex-wrap gap-2">
        {providers.map((provider) => (
          <button
            key={provider.provider}
            onClick={() => onProviderChange(provider.provider)}
            className={cn(
              'px-3 py-1.5 rounded-full text-xs font-medium transition-colors',
              selectedProvider === provider.provider
                ? 'bg-primary-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            )}
          >
            <span className={cn(
              'inline-block w-2 h-2 rounded-full mr-1.5',
              provider.provider === 'gemini' ? 'bg-blue-500' :
              provider.provider === 'openai' ? 'bg-green-500' :
              'bg-gray-500'
            )}></span>
            {provider.info.model_name}
          </button>
        ))}
      </div>
      
      {selectedProvider && (
        <div className="text-xs text-gray-500">
          {providers.find(p => p.provider === selectedProvider)?.info.capabilities.join(', ')}
        </div>
      )}
    </div>
  );
}
