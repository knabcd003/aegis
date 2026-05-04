import { Sidebar } from './Sidebar';
import { Topbar } from './Topbar';

interface LayoutProps {
  children: React.ReactNode;
}

export function Layout({ children }: LayoutProps) {
  return (
    <div className="min-h-screen bg-surface text-on-surface font-body selection:bg-primary-container selection:text-on-primary-container">
      <Sidebar />
      <main className="ml-64 min-h-screen relative">
        <Topbar />
        <div className="p-8 max-w-[1600px] mx-auto">
          {children}
        </div>
        {/* Ambient background glow */}
        <div className="fixed bottom-0 right-0 w-1/3 h-1/3 bg-primary/[0.03] blur-[120px] rounded-full pointer-events-none -z-10" />
        <div className="fixed top-0 left-64 w-1/4 h-1/4 bg-secondary/[0.03] blur-[100px] rounded-full pointer-events-none -z-10" />
      </main>
    </div>
  );
}
