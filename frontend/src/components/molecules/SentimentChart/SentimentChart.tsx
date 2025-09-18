import React from 'react';
import { cn } from '@/utils/helpers';
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts';
import type { SentimentChartProps } from '@/types/components/analyticsTypes';

const COLORS = {
  positive: '#22c55e',
  negative: '#ef4444',
  neutral: '#6b7280',
};

export function SentimentChart({ data, className }: SentimentChartProps) {
  const chartData = [
    { name: 'Positivo', value: data.positive, color: COLORS.positive },
    { name: 'Negativo', value: data.negative, color: COLORS.negative },
    { name: 'Neutral', value: data.neutral, color: COLORS.neutral },
  ].filter(item => item.value > 0);

  const total = data.positive + data.negative + data.neutral;

  if (total === 0) {
    return (
      <div className={cn('flex items-center justify-center h-48 text-gray-500', className)}>
        <div className="text-center">
          <div className="text-sm">No hay datos de sentimiento disponibles</div>
        </div>
      </div>
    );
  }

  return (
    <div className={cn('h-48', className)}>
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie
            data={chartData}
            cx="50%"
            cy="50%"
            innerRadius={40}
            outerRadius={80}
            paddingAngle={2}
            dataKey="value"
          >
            {chartData.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.color} />
            ))}
          </Pie>
          <Tooltip 
            formatter={(value: number) => [
              `${value} (${((value / total) * 100).toFixed(1)}%)`,
              'Análisis'
            ]}
          />
          <Legend />
        </PieChart>
      </ResponsiveContainer>
      
      {/* Summary */}
      <div className="mt-4 grid grid-cols-3 gap-2 text-center">
        {chartData.map((item) => (
          <div key={item.name} className="space-y-1">
            <div 
              className="w-3 h-3 rounded-full mx-auto"
              style={{ backgroundColor: item.color }}
            ></div>
            <div className="text-xs font-medium text-gray-900">{item.name}</div>
            <div className="text-xs text-gray-600">
              {item.value} ({((item.value / total) * 100).toFixed(1)}%)
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
