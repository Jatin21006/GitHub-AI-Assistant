import React, { createContext, useContext, useState, type ReactNode } from 'react';
import type { RepositoryStatusResponse } from '../services/api';

interface WorkspaceState {
  currentRepo: RepositoryStatusResponse | null;
  setCurrentRepo: (repo: RepositoryStatusResponse | null) => void;
  // History of queries and responses (mocked as simple array for this UI)
  conversationHistory: Array<{ query: string; id: string }>;
  setConversationHistory: React.Dispatch<React.SetStateAction<Array<{ query: string; id: string }>>>;
}

const WorkspaceContext = createContext<WorkspaceState | undefined>(undefined);

export const WorkspaceProvider = ({ children }: { children: ReactNode }) => {
  const [currentRepo, setCurrentRepo] = useState<RepositoryStatusResponse | null>(null);
  const [conversationHistory, setConversationHistory] = useState<Array<{ query: string; id: string }>>([]);

  return (
    <WorkspaceContext.Provider value={{
      currentRepo,
      setCurrentRepo,
      conversationHistory,
      setConversationHistory
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
