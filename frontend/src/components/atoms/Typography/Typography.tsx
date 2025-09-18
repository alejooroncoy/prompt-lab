import React, { forwardRef } from 'react';
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '@/utils/helpers';

const typographyVariants = cva('', {
  variants: {
    variant: {
      h1: 'scroll-m-20 text-4xl font-extrabold tracking-tight lg:text-5xl',
      h2: 'scroll-m-20 border-b pb-2 text-3xl font-semibold tracking-tight first:mt-0',
      h3: 'scroll-m-20 text-2xl font-semibold tracking-tight',
      h4: 'scroll-m-20 text-xl font-semibold tracking-tight',
      h5: 'scroll-m-20 text-lg font-semibold tracking-tight',
      h6: 'scroll-m-20 text-base font-semibold tracking-tight',
      p: 'leading-7 [&:not(:first-child)]:mt-6',
      blockquote: 'mt-6 border-l-2 pl-6 italic',
      list: 'my-6 ml-6 list-disc [&>li]:mt-2',
      inlineCode: 'relative rounded bg-secondary-100 px-[0.3rem] py-[0.2rem] font-mono text-sm font-semibold',
      lead: 'text-xl text-secondary-600',
      large: 'text-lg font-semibold',
      small: 'text-sm font-medium leading-none',
      muted: 'text-sm text-secondary-600',
    },
  },
  defaultVariants: {
    variant: 'p',
  },
});

export interface TypographyProps
  extends React.HTMLAttributes<HTMLElement>,
    VariantProps<typeof typographyVariants> {
  as?: keyof JSX.IntrinsicElements;
}

const Typography = forwardRef<HTMLElement, TypographyProps>(
  ({ className, variant, as, ...props }, ref) => {
    // Map variants to appropriate HTML elements
    const getElementFromVariant = (variant: string | null | undefined): keyof JSX.IntrinsicElements => {
      switch (variant) {
        case 'h1':
        case 'h2':
        case 'h3':
        case 'h4':
        case 'h5':
        case 'h6':
          return variant as keyof JSX.IntrinsicElements;
        case 'blockquote':
          return 'blockquote';
        case 'list':
          return 'ul';
        case 'inlineCode':
          return 'code';
        case 'lead':
        case 'large':
        case 'small':
        case 'muted':
        case 'p':
        default:
          return 'p';
      }
    };
    
    const element = as || getElementFromVariant(variant);
    const classes = cn(typographyVariants({ variant, className }));
    
    // Use React.createElement to avoid TypeScript issues with dynamic components
    return React.createElement(
      element as string,
      {
        className: classes,
        ref,
        ...props,
      }
    );
  }
);

Typography.displayName = 'Typography';

export { Typography, typographyVariants };
