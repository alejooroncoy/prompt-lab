import React from 'react';
import { cn } from '@/utils/helpers';

interface FooterProps {
  copyright?: string;
  description?: string;
  features?: string[];
  links?: Array<{
    label: string;
    href: string;
  }>;
  className?: string;
}

export function Footer({ 
  copyright = "© 2025 Prompt Lab. Laboratorio de experimentación con LLMs.",
  description,
  features = ["Analytics en tiempo real"],
  links,
  className 
}: FooterProps) {
  return (
    <footer className={cn('bg-white border-t border-gray-200 mt-auto', className)}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center space-y-2 sm:space-y-0">
          <div className="flex flex-col space-y-1">
            <div className="text-sm text-gray-600">
              {copyright}
            </div>
            {description && (
              <div className="text-xs text-gray-500">
                {description}
              </div>
            )}
          </div>
          
          <div className="flex flex-col sm:flex-row items-start sm:items-center space-y-2 sm:space-y-0 sm:space-x-4">
            {features && features.length > 0 && (
              <div className="flex items-center space-x-2 text-sm text-gray-600">
                {features.map((feature, index) => (
                  <React.Fragment key={feature}>
                    <span>{feature}</span>
                    {index < features.length - 1 && <span>•</span>}
                  </React.Fragment>
                ))}
              </div>
            )}
            
            {links && links.length > 0 && (
              <div className="flex items-center space-x-4">
                {links.map((link) => (
                  <a
                    key={link.href}
                    href={link.href}
                    className="text-sm text-gray-600 hover:text-primary-600 transition-colors"
                  >
                    {link.label}
                  </a>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </footer>
  );
}
