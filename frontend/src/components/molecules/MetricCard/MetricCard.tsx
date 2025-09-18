import React from 'react';
import { cn } from '@/utils/helpers';
import { Typography } from '@/components/atoms/Typography';
import { TrendingUp, TrendingDown } from 'lucide-react';
import type { MetricCardProps } from '@/types/components/analyticsTypes';

export function MetricCard({ 
  title, 
  value, 
  change, 
  icon, 
  className 
}: MetricCardProps) {
  return (
    <div className={cn('card hover:shadow-md transition-shadow duration-200', className)}>
      <div className="card-content py-4">
        <div className="flex items-start justify-between">
          <div className="flex-1 min-w-0 w-full">
            <Typography variant="small" className="text-gray-600 mb-2 font-medium">
              {title}
            </Typography>
            <Typography variant="h3" className="text-2xl font-bold text-gray-900 mb-1">
              {value}
            </Typography>
            
            {change && (
              <div className="flex items-center">
                {change.type === 'increase' ? (
                  <TrendingUp className="w-3 h-3 text-success-600 mr-1" />
                ) : change.type === 'decrease' ? (
                  <TrendingDown className="w-3 h-3 text-error-600 mr-1" />
                ) : null}
                
                <Typography 
                  variant="small" 
                  className={cn(
                    'text-xs font-medium',
                    change.type === 'increase' ? 'text-success-600' :
                    change.type === 'decrease' ? 'text-error-600' :
                    'text-gray-600'
                  )}
                >
                  {change.type === 'increase' ? '+' : change.type === 'decrease' ? '-' : ''}
                  {Math.abs(change.value)}%
                </Typography>
              </div>
            )}
          </div>
          
          {icon && (
            <div className="flex-shrink-0 ml-4">
              <div className="w-10 h-10 bg-primary-50 rounded-lg flex items-center justify-center border border-primary-100">
                <div className="text-primary-600">
                  {icon}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
