import React from 'react';
import { cn } from '@/utils/helpers';

interface HeaderProps {
  title?: string;
  version?: string;
  status?: {
    isActive: boolean;
    label: string;
  };
  actions?: React.ReactNode;
  className?: string;
}

export function Header({ 
  title = "MVP Prompt Lab",
  version = "v1.0.0",
  status = {
    isActive: true,
    label: "Sistema Activo"
  },
  actions,
  className 
}: HeaderProps) {
  return (
    <header className={cn('bg-white border-b border-gray-200', className)}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          <div className="flex items-center">
            <h1 className="text-xl font-semibold text-gray-900">
              {title}
            </h1>
            {version && (
              <span className="ml-2 px-2 py-1 text-xs font-medium bg-primary-100 text-primary-800 rounded-full">
                {version}
              </span>
            )}
          </div>
          
          <div className="flex items-center space-x-4">
            {status && (
              <div className="flex items-center space-x-2">
                <div className={cn(
                  "w-2 h-2 rounded-full",
                  status.isActive ? "bg-green-500" : "bg-red-500"
                )}></div>
                <span className="text-sm text-gray-600">{status.label}</span>
              </div>
            )}
            {actions}
          </div>
        </div>
      </div>
    </header>
  );
}
