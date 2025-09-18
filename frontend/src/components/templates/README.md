# Templates - Componentes Reutilizables

Esta carpeta contiene componentes de template reutilizables que siguen el patrón de Atomic Design.

## Componentes Disponibles

### Header
Componente de cabecera reutilizable con las siguientes características:

```tsx
import { Header } from '@/components/templates';

<Header 
  title="Mi Aplicación"
  version="v2.0.0"
  status={{
    isActive: true,
    label: "Sistema Activo"
  }}
  actions={<button>Acción</button>}
/>
```

**Props:**
- `title?: string` - Título de la aplicación
- `version?: string` - Versión a mostrar
- `status?: { isActive: boolean; label: string }` - Estado del sistema
- `actions?: React.ReactNode` - Elementos de acción adicionales
- `className?: string` - Clases CSS adicionales

### Footer
Componente de pie de página reutilizable:

```tsx
import { Footer } from '@/components/templates';

<Footer 
  copyright="© 2025 Mi Empresa"
  description="Descripción adicional"
  features={["Feature 1", "Feature 2"]}
  links={[
    { label: "Privacidad", href: "/privacy" },
    { label: "Términos", href: "/terms" }
  ]}
/>
```

**Props:**
- `copyright?: string` - Texto de copyright
- `description?: string` - Descripción adicional
- `features?: string[]` - Lista de características
- `links?: Array<{ label: string; href: string }>` - Enlaces del footer
- `className?: string` - Clases CSS adicionales

### LabLayout
Layout principal que combina Header y Footer:

```tsx
import { LabLayout } from '@/components/templates';

<LabLayout>
  <div>Contenido principal</div>
</LabLayout>
```

## Uso en Otras Páginas

Los componentes Header y Footer pueden ser utilizados independientemente en cualquier página:

```tsx
// Página personalizada
import { Header, Footer } from '@/components/templates';

export default function CustomPage() {
  return (
    <div className="min-h-screen flex flex-col">
      <Header 
        title="Página Personalizada"
        status={{ isActive: false, label: "Mantenimiento" }}
      />
      
      <main className="flex-1">
        {/* Contenido personalizado */}
      </main>
      
      <Footer 
        copyright="© 2025 Mi Empresa"
        features={["Feature A", "Feature B"]}
      />
    </div>
  );
}
```

## Beneficios

- **Reutilización**: Componentes que se pueden usar en múltiples páginas
- **Consistencia**: Mantiene el diseño uniforme en toda la aplicación
- **Flexibilidad**: Props configurables para diferentes casos de uso
- **Mantenibilidad**: Cambios centralizados en un solo lugar
- **Atomic Design**: Sigue las mejores prácticas de arquitectura de componentes
