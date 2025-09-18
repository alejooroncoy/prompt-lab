import React from 'react';
import { cn } from '@/utils/helpers';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import type { CostAnalysisChartProps } from '@/types/components/analyticsTypes';

export function CostAnalysisChart({ data, className }: CostAnalysisChartProps) {
  if (!data || data.length === 0) {
    return (
      <div className={cn('flex items-center justify-center h-48 text-gray-500', className)}>
        <div className="text-center">
          <div className="text-sm">No hay datos de costos disponibles</div>
        </div>
      </div>
    );
  }

  // Format data for chart
  const chartData = data.map(item => ({
    ...item,
    formattedDate: new Date(item.date).toLocaleDateString('es-ES', { 
      month: 'short', 
      day: 'numeric' 
    }),
  }));

  const totalCost = data.reduce((sum, item) => sum + item.cost, 0);

  return (
    <div className={cn('h-48', className)}>
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis 
            dataKey="formattedDate" 
            tick={{ fontSize: 12 }}
            axisLine={false}
            tickLine={false}
          />
          <YAxis 
            tick={{ fontSize: 12 }}
            axisLine={false}
            tickLine={false}
            tickFormatter={(value) => `$${value.toFixed(2)}`}
          />
          <Tooltip 
            formatter={(value: number) => [`$${value.toFixed(4)}`, 'Costo']}
            labelStyle={{ color: '#374151' }}
            contentStyle={{ 
              backgroundColor: '#fff',
              border: '1px solid #e5e7eb',
              borderRadius: '6px',
              boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
            }}
          />
          <Line 
            type="monotone" 
            dataKey="cost" 
            stroke="#3b82f6" 
            strokeWidth={2}
            dot={{ fill: '#3b82f6', strokeWidth: 2, r: 4 }}
            activeDot={{ r: 6, stroke: '#3b82f6', strokeWidth: 2 }}
          />
        </LineChart>
      </ResponsiveContainer>
      
      {/* Summary */}
      <div className="mt-4 text-center">
        <div className="text-sm text-gray-600">
          Costo total: <span className="font-medium text-gray-900">${totalCost.toFixed(4)}</span>
        </div>
        <div className="text-xs text-gray-500">
          Promedio diario: ${(totalCost / data.length).toFixed(4)}
        </div>
      </div>
    </div>
  );
}
