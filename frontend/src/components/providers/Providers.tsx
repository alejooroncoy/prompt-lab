'use client';

import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

// Create a client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minutes
      retry: (failureCount, error: any) => {
        // Don't retry on 4xx errors
        if (error?.response?.status >= 400 && error?.response?.status < 500) {
          return false;
        }
        return failureCount < 3;
      },
    },
    mutations: {
      retry: false,
    },
  },
});

interface ProvidersProps {
  children: React.ReactNode;
}

export function Providers({ children }: ProvidersProps) {
  return (
    <QueryClientProvider client={queryClient}>
      {children}
      {process.env.NODE_ENV === 'development' && (
        <DynamicReactQueryDevtools />
      )}
    </QueryClientProvider>
  );
}

// Lazy load devtools only in development
const DynamicReactQueryDevtools = React.lazy(() =>
  import('@tanstack/react-query-devtools').then((module) => ({
    default: () => <module.ReactQueryDevtools initialIsOpen={false} />
  }))
);
