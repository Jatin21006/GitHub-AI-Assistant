import { useNavigate, useLocation } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  LayoutDashboard, Plus, FolderGit2,
  Settings, History, ChevronLeft, ChevronRight, LogOut
} from 'lucide-react';
import { RepoMindLogo } from './ui/RepoMindLogo';
import { useWorkspace } from '../contexts/WorkspaceContext';
import { useAuth } from '../contexts/AuthContext';
import { cn } from '../utils/cn';

export const Sidebar = () => {
  const { currentRepo, conversationHistory, repositories, sidebarCollapsed, toggleSidebar } = useWorkspace();
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const navItems = [
    { icon: LayoutDashboard, label: 'Dashboard', path: '/dashboard' },
    { icon: Plus, label: 'New Repository', path: '/dashboard', action: 'new-repo' },
  ];

  const isActive = (path: string) => location.pathname === path;

  return (
    <div className="flex flex-col h-full bg-[var(--rm-surface)] border-r border-[var(--rm-border)] w-full overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-[var(--rm-border)] flex-shrink-0">
        {!sidebarCollapsed && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.1 }}
          >
            <RepoMindLogo size="sm" />
          </motion.div>
        )}
        <button
          onClick={toggleSidebar}
          className="p-1.5 rounded-lg hover:bg-[var(--rm-surface-hover)] transition-colors text-[var(--rm-text-muted)] hover:text-[var(--rm-text)] hidden md:flex"
        >
          {sidebarCollapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
        </button>
      </div>

      {/* Navigation */}
      <div className="flex-1 overflow-y-auto p-3 space-y-6">
        {/* Main Nav */}
        <div>
          {!sidebarCollapsed && (
            <p className="text-[10px] font-semibold uppercase tracking-widest text-[var(--rm-text-muted)] px-3 mb-2">
              Main
            </p>
          )}
          <div className="space-y-1">
            {navItems.map(item => {
              const Icon = item.icon;
              const active = isActive(item.path) && !item.action;
              return (
                <button
                  key={item.label}
                  onClick={() => navigate(item.path)}
                  className={cn(
                    "w-full flex items-center gap-3 px-3 py-2 rounded-xl text-sm font-medium transition-all duration-200 cursor-pointer",
                    active
                      ? "bg-[var(--rm-accent)]/15 text-[var(--rm-accent)] shadow-[inset_0_0_0_1px_var(--rm-accent-glow)]"
                      : "text-[var(--rm-text-secondary)] hover:bg-[var(--rm-surface-hover)] hover:text-[var(--rm-text)]",
                    sidebarCollapsed && "justify-center px-2"
                  )}
                  title={sidebarCollapsed ? item.label : undefined}
                >
                  <Icon className="w-4 h-4 flex-shrink-0" />
                  {!sidebarCollapsed && <span>{item.label}</span>}
                </button>
              );
            })}
          </div>
        </div>

        {/* Repositories */}
        {!sidebarCollapsed && repositories.length > 0 && (
          <div>
            <p className="text-[10px] font-semibold uppercase tracking-widest text-[var(--rm-text-muted)] px-3 mb-2">
              Repositories
            </p>
            <div className="space-y-1">
              {repositories.map(repo => {
                const parts = repo.repository_name.split('/');
                const owner = parts[0];
                const repoName = parts[1];
                const isCurrentRepo = currentRepo?.repository_name === repo.repository_name;
                return (
                  <button
                    key={repo.repository_name}
                    onClick={() => navigate(`/workspace/${owner}/${repoName}`)}
                    className={cn(
                      "w-full flex items-center gap-3 px-3 py-2 rounded-xl text-sm transition-all duration-200 cursor-pointer",
                      isCurrentRepo
                        ? "bg-[var(--rm-accent)]/15 text-[var(--rm-accent)]"
                        : "text-[var(--rm-text-secondary)] hover:bg-[var(--rm-surface-hover)] hover:text-[var(--rm-text)]"
                    )}
                  >
                    <FolderGit2 className="w-4 h-4 flex-shrink-0" />
                    <span className="truncate">{owner}/{repoName}</span>
                    <span className={`ml-auto w-2 h-2 rounded-full flex-shrink-0 ${repo.is_indexed ? 'bg-[var(--rm-success)]' : 'bg-yellow-500'}`} />
                  </button>
                );
              })}
            </div>
          </div>
        )}

        {/* Conversations */}
        {!sidebarCollapsed && conversationHistory.length > 0 && (
          <div>
            <p className="text-[10px] font-semibold uppercase tracking-widest text-[var(--rm-text-muted)] px-3 mb-2">
              Conversations
            </p>
            <div className="space-y-1">
              {conversationHistory.slice(0, 8).map((conv) => (
                <button
                  key={conv.id}
                  className="w-full flex items-center gap-3 px-3 py-2 rounded-xl text-sm text-[var(--rm-text-secondary)] hover:bg-[var(--rm-surface-hover)] hover:text-[var(--rm-text)] transition-all duration-200 cursor-pointer"
                >
                  <History className="w-4 h-4 flex-shrink-0 text-[var(--rm-text-muted)]" />
                  <span className="truncate">{conv.query}</span>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Settings */}
        {!sidebarCollapsed && (
          <div>
            <button
              className="w-full flex items-center gap-3 px-3 py-2 rounded-xl text-sm text-[var(--rm-text-secondary)] hover:bg-[var(--rm-surface-hover)] hover:text-[var(--rm-text)] transition-all duration-200 cursor-pointer"
            >
              <Settings className="w-4 h-4 flex-shrink-0" />
              <span>Settings</span>
            </button>
          </div>
        )}
      </div>

      {/* User Profile */}
      <div className="p-3 border-t border-[var(--rm-border)] flex-shrink-0">
        <div className={cn(
          "flex items-center gap-3 px-3 py-2 rounded-xl",
          sidebarCollapsed && "justify-center px-2"
        )}>
          {/* Avatar */}
          <div className="w-8 h-8 rounded-full bg-gradient-to-br from-[#8B5CF6] to-[#6D28D9] flex items-center justify-center text-white text-xs font-bold flex-shrink-0">
            {user?.name?.charAt(0).toUpperCase() || 'U'}
          </div>
          {!sidebarCollapsed && (
            <>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-[var(--rm-text)] truncate">{user?.name || 'User'}</p>
                <p className="text-xs text-[var(--rm-text-muted)] truncate">{user?.email || ''}</p>
              </div>
              <button
                onClick={() => {
                  logout();
                  navigate('/');
                }}
                className="p-1.5 rounded-lg hover:bg-[var(--rm-surface-hover)] text-[var(--rm-text-muted)] hover:text-red-400 transition-colors"
                title="Sign out"
              >
                <LogOut className="w-4 h-4" />
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
};
