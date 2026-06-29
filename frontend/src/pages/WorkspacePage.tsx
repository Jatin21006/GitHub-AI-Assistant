import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Layout } from '../components/Layout';
import { SourcePanel } from '../components/SourcePanel';
import { ChatWindow } from '../components/chat/ChatWindow';
import { apiService, type Citation } from '../services/api';
import { useWorkspace } from '../contexts/WorkspaceContext';
import { MessageSquare, Layers, Wand2, BookOpen, ShieldAlert, Settings, ExternalLink } from 'lucide-react';
import { cn } from '../utils/cn';
import { FadeIn } from '../components/ui/PageTransition';

type TabId = 'ask' | 'architecture' | 'improvements' | 'documentation' | 'security';

export const WorkspacePage = () => {
  const { owner, repo } = useParams<{ owner: string; repo: string }>();
  const navigate = useNavigate();
  const { currentRepo, setCurrentRepo, addRepository } = useWorkspace();
  const [activeTab, setActiveTab] = useState<TabId>('ask');
  const [citations, setCitations] = useState<Citation[]>([]);

  useEffect(() => {
    const checkRepo = async () => {
      if (!owner || !repo) {
        navigate('/dashboard');
        return;
      }

      try {
        const status = await apiService.getRepositoryStatus(owner, repo);
        setCurrentRepo(status);
        addRepository(status);
        if (!status.is_indexed) {
          navigate('/dashboard');
        }
      } catch {
        navigate('/dashboard');
      }
    };

    if (!currentRepo || currentRepo.repository_name !== `${owner}/${repo}`) {
      checkRepo();
    }
  }, [owner, repo, navigate, currentRepo, setCurrentRepo, addRepository]);

  if (!currentRepo) {
    return (
      <Layout>
        <div className="h-full w-full flex items-center justify-center">
          <div className="flex items-center gap-3 text-[var(--rm-text-muted)]">
            <div className="w-5 h-5 border-2 border-[var(--rm-accent)] border-t-transparent rounded-full animate-spin" />
            <span>Loading workspace...</span>
          </div>
        </div>
      </Layout>
    );
  }

  const tabs = [
    { id: 'ask', label: 'Ask Questions', icon: MessageSquare },
    { id: 'architecture', label: 'Architecture', icon: Layers },
    { id: 'improvements', label: 'Improvements', icon: Wand2 },
    { id: 'documentation', label: 'Documentation', icon: BookOpen },
    { id: 'security', label: 'Security', icon: ShieldAlert },
  ] as const;

  const repoName = currentRepo.repository_name;

  return (
    <Layout rightPanel={<SourcePanel citations={citations} />}>
      {/* Repository Info Bar */}
      <FadeIn>
        <div className="px-6 py-3 border-b border-[var(--rm-border)] bg-[var(--rm-surface)]/50 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <h2 className="font-semibold text-sm text-[var(--rm-text)]">{owner}/{repo}</h2>
            <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium bg-[var(--rm-success)]/15 text-[var(--rm-success)] border border-[var(--rm-success)]/20">
              <span className="w-1.5 h-1.5 rounded-full bg-[var(--rm-success)]" />
              Indexed
            </span>
          </div>
          <div className="flex items-center gap-2">
            <button className="p-1.5 rounded-lg hover:bg-[var(--rm-surface-hover)] text-[var(--rm-text-muted)] hover:text-[var(--rm-text)] transition-colors">
              <Settings className="w-4 h-4" />
            </button>
            <a
              href={`https://github.com/${owner}/${repo}`}
              target="_blank"
              rel="noopener noreferrer"
              className="p-1.5 rounded-lg hover:bg-[var(--rm-surface-hover)] text-[var(--rm-text-muted)] hover:text-[var(--rm-text)] transition-colors"
            >
              <ExternalLink className="w-4 h-4" />
            </a>
          </div>
        </div>
      </FadeIn>

      {/* Tab Navigation */}
      <div className="px-6 border-b border-[var(--rm-border)] bg-[var(--rm-bg)] sticky top-0 z-10">
        <div className="flex gap-1 overflow-x-auto">
          {tabs.map(tab => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={cn(
                  "relative flex items-center gap-2 px-4 py-3 text-sm font-medium whitespace-nowrap transition-colors cursor-pointer",
                  isActive
                    ? "text-[var(--rm-accent)]"
                    : "text-[var(--rm-text-muted)] hover:text-[var(--rm-text)]"
                )}
              >
                <Icon className="w-4 h-4" />
                {tab.label}
                {isActive && (
                  <motion.div
                    layoutId="active-tab-indicator"
                    className="absolute bottom-0 left-0 right-0 h-[2px] bg-[var(--rm-accent)] rounded-full"
                    transition={{ type: 'spring', stiffness: 500, damping: 35 }}
                  />
                )}
              </button>
            );
          })}
        </div>
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
