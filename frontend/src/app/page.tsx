import { LabLayout } from '@/components/templates/LabLayout';
import { ChatInterface } from '@/components/organisms/ChatInterface';
import { AnalyticsDashboard } from '@/components/organisms/AnalyticsDashboard';

export default function HomePage() {
  return (
    <LabLayout>
      <section className="grid grid-cols-1 lg:grid-cols-3 gap-6 flex-1">
        {/* Chat Interface - Takes 2/3 of the width on large screens */}
        <div className="lg:col-span-2">
          <ChatInterface />
        </div>
        
        {/* Analytics Dashboard - Takes 1/3 of the width on large screens */}
        <aside className="lg:col-span-1 h-full">
          <AnalyticsDashboard />
        </aside>
      </section>
    </LabLayout>
  );
}
