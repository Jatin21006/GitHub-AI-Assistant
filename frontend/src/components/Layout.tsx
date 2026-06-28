import type { ReactNode } from 'react';
import { Sidebar } from './Sidebar';

interface LayoutProps {
  children: ReactNode;
  rightPanel?: ReactNode;
}

export const Layout = ({ children, rightPanel }: LayoutProps) => {
  return (
    <div className="flex h-screen w-full overflow-hidden bg-background text-foreground">
      <Sidebar />
      <main className="flex-1 flex flex-col min-w-0 relative">
        {children}
      </main>
      {rightPanel}
    </div>
  );
};
