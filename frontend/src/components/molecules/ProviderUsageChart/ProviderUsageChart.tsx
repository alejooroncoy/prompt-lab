import React from 'react';
import { cn } from '@/utils/helpers';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import type { ProviderUsageChartProps } from '@/types/components/analyticsTypes';

const COLORS = {
  gemini: '#4285f4',
  openai: '#10a37f',
  claude: '#8b5cf6',
};

export function ProviderUsageChart({ data, className }: ProviderUsageChartProps) {
  const chartData = Object.entries(data).map(([provider, count]) => ({
    provider: provider.toUpperCase(),
    count,
    color: COLORS[provider.toLowerCase() as keyof typeof COLORS] || '#6b7280',
  }));

  const total = Object.values(data).reduce((sum, count) => sum + count, 0);

  if (total === 0) {
    return (
      <div className={cn('flex items-center justify-center h-48 text-gray-500', className)}>
        <div className="text-center">
          <div className="text-sm">No hay datos de uso de proveedores</div>
        </div>
      </div>
    );
  }

  return (
    <div className={cn('h-48', className)}>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis 
            dataKey="provider" 
            tick={{ fontSize: 12 }}
            axisLine={false}
            tickLine={false}
          />
          <YAxis 
            tick={{ fontSize: 12 }}
            axisLine={false}
            tickLine={false}
          />
          <Tooltip 
            formatter={(value: number) => [
              `${value} (${((value / total) * 100).toFixed(1)}%)`,
              'Uso'
            ]}
            labelStyle={{ color: '#374151' }}
            contentStyle={{ 
              backgroundColor: '#fff',
              border: '1px solid #e5e7eb',
              borderRadius: '6px',
              boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
            }}
          />
          <Bar 
            dataKey="count" 
            radius={[4, 4, 0, 0]}
            fill="#8884d8"
          />
        </BarChart>
      </ResponsiveContainer>
      
      {/* Summary */}
      <div className="mt-4 flex flex-wrap gap-2 justify-center">
        {chartData.map((item) => (
          <div key={item.provider} className="flex items-center space-x-1">
            <div 
              className="w-2 h-2 rounded-full"
              style={{ backgroundColor: item.color }}
            ></div>
            <span className="text-xs text-gray-600">
              {item.provider}: {item.count} ({((item.count / total) * 100).toFixed(1)}%)
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
