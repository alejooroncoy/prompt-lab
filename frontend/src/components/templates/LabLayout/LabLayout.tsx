import React from 'react';
import { cn } from '@/utils/helpers';
import { Header } from '../Header';
import { Footer } from '../Footer';

interface LabLayoutProps {
  children: React.ReactNode;
  className?: string;
}

export function LabLayout({ children, className }: LabLayoutProps) {
  return (
    <div className={cn('min-h-dvh bg-gray-50 flex flex-col', className)}>
      <Header 
        title="Prompt Lab"
        version="v1.0.0"
        status={{
          isActive: true,
          label: "Sistema Activo"
        }}
      />

      {/* Main Content */}
      <main className="flex-1 flex flex-col max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {children}
      </main>

      <Footer 
        copyright="© 2025 Prompt Lab. Laboratorio de experimentación con LLMs."
        features={["Analytics en tiempo real"]}
      />
    </div>
  );
}
