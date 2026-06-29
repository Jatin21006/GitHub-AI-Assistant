import { useState, type ReactNode } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Sidebar } from './Sidebar';
import { Menu, X } from 'lucide-react';
import { useWorkspace } from '../contexts/WorkspaceContext';

interface LayoutProps {
  children: ReactNode;
  rightPanel?: ReactNode;
}

export const Layout = ({ children, rightPanel }: LayoutProps) => {
  const { sidebarCollapsed } = useWorkspace();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  return (
    <div className="flex h-screen w-full overflow-hidden bg-[var(--rm-bg)] text-[var(--rm-text)]">
      {/* Desktop Sidebar */}
      <motion.div
        className="hidden md:flex flex-shrink-0"
        animate={{ width: sidebarCollapsed ? 68 : 260 }}
        transition={{ duration: 0.25, ease: 'easeInOut' }}
      >
        <Sidebar />
      </motion.div>

      {/* Mobile menu overlay */}
      <AnimatePresence>
        {mobileMenuOpen && (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 bg-black/60 z-40 md:hidden"
              onClick={() => setMobileMenuOpen(false)}
            />
            <motion.div
              initial={{ x: -280 }}
              animate={{ x: 0 }}
              exit={{ x: -280 }}
              transition={{ duration: 0.25, ease: 'easeInOut' }}
              className="fixed left-0 top-0 bottom-0 w-[260px] z-50 md:hidden"
            >
              <Sidebar />
            </motion.div>
          </>
        )}
      </AnimatePresence>

      {/* Mobile top bar */}
      <div className="flex flex-col flex-1 min-w-0">
        <div className="md:hidden flex items-center gap-3 px-4 py-3 border-b border-[var(--rm-border)] bg-[var(--rm-surface)]">
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="p-1.5 rounded-lg hover:bg-[var(--rm-surface-hover)] transition-colors"
          >
            {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>
          <span className="font-semibold text-sm">RepoMind</span>
        </div>

        {/* Main content */}
        <main className="flex-1 flex min-w-0 relative overflow-hidden">
          <div className="flex-1 flex flex-col min-w-0">
            {children}
          </div>
          {/* Right panel */}
          <AnimatePresence>
            {rightPanel && (
              <motion.div
                initial={{ width: 0, opacity: 0 }}
                animate={{ width: 320, opacity: 1 }}
                exit={{ width: 0, opacity: 0 }}
                transition={{ duration: 0.25, ease: 'easeInOut' }}
                className="hidden lg:block flex-shrink-0 overflow-hidden"
              >
                {rightPanel}
              </motion.div>
            )}
          </AnimatePresence>
        </main>
      </div>
    </div>
  );
};
