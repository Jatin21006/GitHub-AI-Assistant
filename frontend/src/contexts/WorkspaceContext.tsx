import React, { createContext, useContext, useState, useEffect, type ReactNode } from 'react';
import type { RepositoryStatusResponse } from '../services/api';

interface WorkspaceState {
  currentRepo: RepositoryStatusResponse | null;
  setCurrentRepo: (repo: RepositoryStatusResponse | null) => void;
  // Multi-repo support
  repositories: RepositoryStatusResponse[];
  addRepository: (repo: RepositoryStatusResponse) => void;
  // History of queries and responses
  conversationHistory: Array<{ query: string; id: string }>;
  setConversationHistory: React.Dispatch<React.SetStateAction<Array<{ query: string; id: string }>>>;
  // Sidebar state
  sidebarCollapsed: boolean;
  toggleSidebar: () => void;
}

const WorkspaceContext = createContext<WorkspaceState | undefined>(undefined);

const REPOS_KEY = 'repomind_repositories';

export const WorkspaceProvider = ({ children }: { children: ReactNode }) => {
  const [currentRepo, setCurrentRepo] = useState<RepositoryStatusResponse | null>(null);
  const [repositories, setRepositories] = useState<RepositoryStatusResponse[]>(() => {
    // Restore from localStorage
    const stored = localStorage.getItem(REPOS_KEY);
    if (stored) {
      try {
        return JSON.parse(stored);
      } catch {
        return [];
      }
    }
    return [];
  });
  const [conversationHistory, setConversationHistory] = useState<Array<{ query: string; id: string }>>([]);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  // Persist repositories to localStorage
  useEffect(() => {
    localStorage.setItem(REPOS_KEY, JSON.stringify(repositories));
  }, [repositories]);

  const addRepository = (repo: RepositoryStatusResponse) => {
    setRepositories(prev => {
      const exists = prev.some(r => r.repository_name === repo.repository_name);
      if (exists) {
        // Update existing
        return prev.map(r => r.repository_name === repo.repository_name ? repo : r);
      }
      return [...prev, repo];
    });
  };

  const toggleSidebar = () => setSidebarCollapsed(prev => !prev);

  return (
    <WorkspaceContext.Provider value={{
      currentRepo,
      setCurrentRepo,
      repositories,
      addRepository,
      conversationHistory,
      setConversationHistory,
      sidebarCollapsed,
      toggleSidebar,
    }}>
      {children}
    </WorkspaceContext.Provider>
  );
};

export const useWorkspace = () => {
  const context = useContext(WorkspaceContext);
  if (context === undefined) {
    throw new Error('useWorkspace must be used within a WorkspaceProvider');
  }
  return context;
};
