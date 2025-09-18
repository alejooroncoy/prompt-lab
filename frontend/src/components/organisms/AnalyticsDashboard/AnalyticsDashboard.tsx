'use client';

import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { cn } from '@/utils/helpers';
import { analyticsApi } from '@/services/api/analytics';
import { Typography } from '@/components/atoms/Typography';
import { MetricCard } from '@/components/molecules/MetricCard';
import { SentimentChart } from '@/components/molecules/SentimentChart';
import { ProviderUsageChart } from '@/components/molecules/ProviderUsageChart';
import { CostAnalysisChart } from '@/components/molecules/CostAnalysisChart';
import { BarChart3, TrendingUp, DollarSign, MessageSquare } from 'lucide-react';

interface AnalyticsDashboardProps {
  className?: string;
  userId?: string;
  conversationId?: string;
}

export function AnalyticsDashboard({ 
  className, 
  userId = 'demo-user',
  conversationId 
}: AnalyticsDashboardProps) {
  // Get analytics summary
  const { data: analyticsData, isLoading, error } = useQuery({
    queryKey: ['analytics-summary', userId, conversationId],
    queryFn: () => analyticsApi.getAnalyticsSummary(
      userId, 
      conversationId, 
      30, 
      !conversationId // Include global metrics if not viewing specific conversation
    ),
    refetchInterval: 30000, // Refetch every 30 seconds
  });

  if (isLoading) {
    return (
      <div className={cn('p-6 justify-center align-center flex flex-col h-full', className)}>
        <div className="animate-pulse">
          <div className="h-6 bg-gray-200 rounded w-1/3 mb-4"></div>
          <div className="space-y-3">
            <div className="h-20 bg-gray-200 rounded"></div>
            <div className="h-20 bg-gray-200 rounded"></div>
            <div className="h-20 bg-gray-200 rounded"></div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={cn('p-6 justify-center align-center flex flex-col h-full', className)}>
        <div className="text-center">
          <Typography variant="h4" className="text-lg font-medium text-gray-900 mb-2">
            Error al cargar analytics
          </Typography>
          <Typography variant="muted" className="text-gray-600">
            No se pudieron cargar los datos de analytics. Inténtalo de nuevo.
          </Typography>
        </div>
      </div>
    );
  }

  const userMetrics = analyticsData?.user_metrics;
  const conversationMetrics = analyticsData?.conversation_metrics;
  const globalMetrics = analyticsData?.global_metrics;
  const providerBreakdown = analyticsData?.provider_breakdown;
  const sentimentTrends = analyticsData?.sentiment_trends;
  const costAnalysis = analyticsData?.cost_analysis;

  return (
    <div className={cn('p-6 pt-0 space-y-6 flex-1 h-full overflow-y-auto', className)}>
      {/* Header */}
      <header className="flex items-center space-x-2 mb-6">
        <BarChart3 className="w-5 h-5 text-primary-600" />
        <Typography variant="h3" className="text-lg font-semibold text-gray-900">
          Analytics Dashboard
        </Typography>
      </header>

      {/* Metrics Overview */}
      <div className="grid grid-cols-1 gap-4 mb-6">
        {userMetrics && (
          <>
            <MetricCard
              title="Conversaciones"
              value={userMetrics.total_conversations}
              icon={<MessageSquare className="w-5 h-5" />}
            />
            <MetricCard
              title="Mensajes Totales"
              value={userMetrics.total_messages}
              icon={<MessageSquare className="w-5 h-5" />}
            />
            <MetricCard
              title="Tokens Usados"
              value={userMetrics.total_tokens_used.toLocaleString()}
              icon={<TrendingUp className="w-5 h-5" />}
            />
            <MetricCard
              title="Costo Total"
              value={`$${userMetrics.total_cost_usd.toFixed(4)}`}
              icon={<DollarSign className="w-5 h-5" />}
            />
          </>
        )}

        {conversationMetrics && (
          <>
            <MetricCard
              title="Tiempo Promedio de Respuesta"
              value={`${conversationMetrics.avg_response_time_ms.toFixed(0)}ms`}
              icon={<TrendingUp className="w-5 h-5" />}
            />
            <MetricCard
              title="Costo por Mensaje"
              value={`$${conversationMetrics.cost_per_message.toFixed(4)}`}
              icon={<DollarSign className="w-5 h-5" />}
            />
          </>
        )}
      </div>

      {/* Charts */}
      <div className="space-y-6">
        {/* Sentiment Analysis */}
        {sentimentTrends && (
          <article className="card">
            <header className="card-header">
              <Typography variant="h4" className="text-base font-semibold text-gray-900">
                Análisis de Sentimiento
              </Typography>
              <Typography variant="muted" className="text-sm text-gray-600">
                Distribución del sentimiento en las conversaciones
              </Typography>
            </header>
            <div className="card-content pb-20">
              <SentimentChart 
                data={{
                  positive: sentimentTrends.sentiment_distribution.positive || 0,
                  negative: sentimentTrends.sentiment_distribution.negative || 0,
                  neutral: sentimentTrends.sentiment_distribution.neutral || 0,
                }} 
              />
            </div>
          </article>
        )}

        {/* Provider Usage */}
        {providerBreakdown && (
          <article className="card">
            <header className="card-header">
              <Typography variant="h4" className="text-base font-semibold text-gray-900">
                Uso de Proveedores
              </Typography>
              <Typography variant="muted" className="text-sm text-gray-600">
                Distribución del uso entre diferentes LLM providers
              </Typography>
            </header>
            <div className="card-content pb-12 md:pb-18">
              <ProviderUsageChart data={providerBreakdown.provider_distribution} />
            </div>
          </article>
        )}

        {/* Cost Analysis */}
        {costAnalysis && costAnalysis.daily_cost_trend && costAnalysis.daily_cost_trend.length > 0 && (
          <article className="card">
            <header className="card-header">
              <Typography variant="h4" className="text-base font-semibold text-gray-900">
                Análisis de Costos
              </Typography>
              <Typography variant="muted" className="text-sm text-gray-600">
                Tendencias de costos diarios
              </Typography>
            </header>
            <div className="card-content pb-5">
              <CostAnalysisChart data={costAnalysis.daily_cost_trend} />
            </div>
          </article>
        )}
      </div>

      {/* Global Metrics (if available) */}
      {globalMetrics && (
        <article className="card">
          <header className="card-header">
            <Typography variant="h4" className="text-base font-semibold text-gray-900">
              Métricas Globales
            </Typography>
            <Typography variant="muted" className="text-sm text-gray-600">
              Estadísticas generales de la plataforma
            </Typography>
          </header>
          <div className="card-content pb-5">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
              <div className="text-center p-4 bg-gray-50 rounded-lg">
                <Typography variant="small" className="text-gray-600 mb-2 font-medium">
                  Usuarios Totales
                </Typography>
                <Typography variant="large" className="text-3xl font-bold text-primary-600">
                  {globalMetrics.total_users}
                </Typography>
              </div>
              <div className="text-center p-4 bg-gray-50 rounded-lg">
                <Typography variant="small" className="text-gray-600 mb-2 font-medium">
                  Conversaciones Totales
                </Typography>
                <Typography variant="large" className="text-3xl font-bold text-primary-600">
                  {globalMetrics.total_conversations}
                </Typography>
              </div>
            </div>
          </div>
        </article>
      )}
    </div>
  );
}
