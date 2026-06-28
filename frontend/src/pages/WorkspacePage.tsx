import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Layout } from '../components/Layout';
import { SourcePanel } from '../components/SourcePanel';
import { ChatWindow } from '../components/chat/ChatWindow';
import { apiService, type Citation } from '../services/api';
import { useWorkspace } from '../contexts/WorkspaceContext';
import { MessageSquare, Layers, Wand2, BookOpen, ShieldAlert } from 'lucide-react';
import { cn } from '../utils/cn';

type TabId = 'ask' | 'architecture' | 'improvements' | 'documentation' | 'security';

export const WorkspacePage = () => {
  const { owner, repo } = useParams<{ owner: string; repo: string }>();
  const navigate = useNavigate();
  const { currentRepo, setCurrentRepo } = useWorkspace();
  const [activeTab, setActiveTab] = useState<TabId>('ask');
  const [citations, setCitations] = useState<Citation[]>([]);

  useEffect(() => {
    const checkRepo = async () => {
      if (!owner || !repo) {
        navigate('/');
        return;
      }
      
      try {
        const status = await apiService.getRepositoryStatus(owner, repo);
        setCurrentRepo(status);
        if (!status.is_indexed) {
          // Fallback if accessed URL directly but not indexed
          navigate('/');
        }
      } catch {
        navigate('/');
      }
    };
    
    if (!currentRepo || currentRepo.repository_name !== `${owner}/${repo}`) {
      checkRepo();
    }
  }, [owner, repo, navigate, currentRepo, setCurrentRepo]);

  if (!currentRepo) {
    return <div className="h-screen w-full bg-background flex items-center justify-center">Loading Workspace...</div>;
  }

  const tabs = [
    { id: 'ask', label: 'Ask Questions', icon: MessageSquare },
    { id: 'architecture', label: 'Architecture', icon: Layers },
    { id: 'improvements', label: 'Improvements', icon: Wand2 },
    { id: 'documentation', label: 'Documentation', icon: BookOpen },
    { id: 'security', label: 'Security Review', icon: ShieldAlert },
  ] as const;

  const repoName = currentRepo.repository_name;

  return (
    <Layout rightPanel={<SourcePanel citations={citations} />}>
      {/* Top Navigation */}
      <div className="border-b border-border bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 z-10 sticky top-0 px-4 flex gap-6 overflow-x-auto">
        {tabs.map(tab => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={cn(
                "flex items-center gap-2 py-4 text-sm font-medium border-b-2 whitespace-nowrap transition-colors",
                isActive ? "border-primary text-foreground" : "border-transparent text-muted-foreground hover:text-foreground hover:border-muted"
              )}
            >
              <Icon className="w-4 h-4" />
              {tab.label}
            </button>
          );
        })}
      </div>

      {/* Main Content Area */}
      <div className="flex-1 overflow-hidden relative">
        {activeTab === 'ask' && (
          <ChatWindow 
            key="ask" 
            repoName={repoName} 
            setCitations={setCitations} 
          />
        )}
        
        {activeTab === 'architecture' && (
          <ChatWindow 
            key="architecture"
            repoName={repoName} 
            setCitations={setCitations}
            initialMessage="Generate a high-level architecture overview for this repository."
            systemPromptPrefix="You are an expert software architect. Analyze the provided context and explain the architecture of the system. Focus on module structure, design patterns, and major dependencies."
          />
        )}
        
        {activeTab === 'improvements' && (
          <ChatWindow 
            key="improvements"
            repoName={repoName} 
            setCitations={setCitations}
            initialMessage="Suggest code improvements and refactoring opportunities."
            systemPromptPrefix="You are an expert code reviewer. Suggest concrete performance improvements, refactoring strategies, and best practices for the provided context."
          />
        )}
        
        {activeTab === 'documentation' && (
          <ChatWindow 
            key="documentation"
            repoName={repoName} 
            setCitations={setCitations}
            initialMessage="Generate API documentation for the main modules."
            systemPromptPrefix="You are an expert technical writer. Write detailed documentation for the provided context including function signatures, parameters, and return types."
          />
        )}
        
        {activeTab === 'security' && (
          <ChatWindow 
            key="security"
            repoName={repoName} 
            setCitations={setCitations}
            initialMessage="Perform a security review of this codebase."
            systemPromptPrefix="You are an expert security auditor. Look for vulnerabilities, hardcoded secrets, injection flaws, and unsafe dependencies in the provided context."
          />
        )}
      </div>
    </Layout>
  );
};
