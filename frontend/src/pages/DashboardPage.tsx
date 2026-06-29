import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  Plus, FolderGit2, Loader2, MessageSquare, Layers,
  BookOpen, ShieldAlert, Wand2, ArrowRight, GitBranch
} from 'lucide-react';
import { Layout } from '../components/Layout';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { FadeIn } from '../components/ui/PageTransition';
import { apiService } from '../services/api';
import { useWorkspace } from '../contexts/WorkspaceContext';
import { useAuth } from '../contexts/AuthContext';

export const DashboardPage = () => {
  const [showNewRepo, setShowNewRepo] = useState(false);
  const [url, setUrl] = useState('');
  const [status, setStatus] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const navigate = useNavigate();
  const { setCurrentRepo, repositories, addRepository } = useWorkspace();
  const { user } = useAuth();

  const handleIndex = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!url) return;

    setLoading(true);
    setError(null);
    setStatus('Cloning repository...');

    try {
      const cloneRes = await apiService.cloneRepository(url);
      const repoName = cloneRes.repository_name;

      setStatus('Parsing and building vector store...');
      await apiService.indexRepository(repoName);

      setStatus('Indexing complete! Navigating...');

      const parts = repoName.split('/');
      if (parts.length === 2) {
        const [owner, repo] = parts;
        const statusRes = await apiService.getRepositoryStatus(owner, repo);
        setCurrentRepo(statusRes);
        addRepository(statusRes);
        navigate(`/workspace/${owner}/${repo}`);
      } else {
        throw new Error('Invalid repository name format returned by server.');
      }
    } catch (err: any) {
      setError(err.message || 'An unexpected error occurred');
      setStatus('');
    } finally {
      setLoading(false);
    }
  };

  const quickActions = [
    { icon: MessageSquare, label: 'Ask Questions', description: 'Chat with your codebase', color: 'from-violet-500 to-purple-600' },
    { icon: Layers, label: 'Architecture', description: 'Understand system design', color: 'from-blue-500 to-cyan-500' },
    { icon: BookOpen, label: 'Documentation', description: 'Generate API docs', color: 'from-emerald-500 to-teal-500' },
    { icon: ShieldAlert, label: 'Security Review', description: 'Find vulnerabilities', color: 'from-orange-500 to-red-500' },
    { icon: Wand2, label: 'Improvements', description: 'Refactoring suggestions', color: 'from-pink-500 to-rose-500' },
  ];

  const greeting = user?.name
    ? `Welcome back, ${user.name}`
    : 'Welcome to RepoMind';

  return (
    <Layout>
      <div className="flex-1 overflow-y-auto">
        <div className="max-w-5xl mx-auto px-6 py-10">
          {/* Header */}
          <FadeIn>
            <h1 className="text-3xl font-bold mb-2">{greeting}</h1>
            <p className="text-[var(--rm-text-secondary)] mb-8">
              Developer-friendly, AI-powered repository assistant
            </p>
          </FadeIn>

          {/* New Repository Card */}
          <FadeIn delay={0.1}>
            {!showNewRepo ? (
              <motion.button
                onClick={() => setShowNewRepo(true)}
                className="w-full p-6 rounded-2xl border-2 border-dashed border-[var(--rm-border)] hover:border-[var(--rm-accent)]/40 bg-[var(--rm-surface)]/30 hover:bg-[var(--rm-surface)]/50 transition-all duration-300 flex items-center gap-4 group cursor-pointer mb-8"
                whileHover={{ scale: 1.005 }}
                whileTap={{ scale: 0.995 }}
              >
                <div className="w-12 h-12 rounded-xl bg-[var(--rm-accent)]/10 flex items-center justify-center group-hover:bg-[var(--rm-accent)]/20 transition-colors">
                  <Plus className="w-6 h-6 text-[var(--rm-accent)]" />
                </div>
                <div className="text-left">
                  <p className="font-semibold text-[var(--rm-text)]">New Repository</p>
                  <p className="text-sm text-[var(--rm-text-muted)]">Clone and index a GitHub repository</p>
                </div>
                <ArrowRight className="ml-auto w-5 h-5 text-[var(--rm-text-muted)] group-hover:text-[var(--rm-accent)] transition-colors" />
              </motion.button>
            ) : (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                className="mb-8 p-6 rounded-2xl bg-[var(--rm-surface)] border border-[var(--rm-border)]"
              >
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-lg font-semibold flex items-center gap-2">
                    <GitBranch className="w-5 h-5 text-[var(--rm-accent)]" />
                    Clone & Index Repository
                  </h2>
                  <Button variant="ghost" size="sm" onClick={() => setShowNewRepo(false)}>
                    Cancel
                  </Button>
                </div>
                <form onSubmit={handleIndex} className="space-y-4">
                  <div className="relative">
                    <FolderGit2 className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-[var(--rm-text-muted)]" />
                    <Input
                      type="text"
                      placeholder="https://github.com/owner/repository"
                      value={url}
                      onChange={(e) => setUrl(e.target.value)}
                      className="pl-10 h-12"
                      disabled={loading}
                    />
                  </div>

                  <Button
                    type="submit"
                    className="w-full h-11"
                    disabled={!url || loading}
                  >
                    {loading ? (
                      <>
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        {status}
                      </>
                    ) : (
                      <>
                        Clone & Index Repository
                        <ArrowRight className="ml-2 h-4 w-4" />
                      </>
                    )}
                  </Button>

                  {error && (
                    <motion.div
                      initial={{ opacity: 0, y: -4 }}
                      animate={{ opacity: 1, y: 0 }}
                      className="p-3 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-sm"
                    >
                      {error}
                    </motion.div>
                  )}
                </form>
              </motion.div>
            )}
          </FadeIn>

          {/* Repositories */}
          {repositories.length > 0 && (
            <FadeIn delay={0.2}>
              <h2 className="text-lg font-semibold mb-4">Your Repositories</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-10">
                {repositories.map((repo, index) => {
                  const parts = repo.repository_name.split('/');
                  const owner = parts[0];
                  const repoName = parts[1];
                  return (
                    <motion.button
                      key={repo.repository_name}
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: 0.1 * index }}
                      onClick={() => {
                        setCurrentRepo(repo);
                        navigate(`/workspace/${owner}/${repoName}`);
                      }}
                      className="p-5 rounded-2xl bg-[var(--rm-surface)] border border-[var(--rm-border)] hover:border-[var(--rm-border-active)] transition-all duration-300 text-left group hover:shadow-glow cursor-pointer"
                    >
                      <div className="flex items-center gap-3 mb-3">
                        <div className="w-9 h-9 rounded-xl bg-[var(--rm-accent)]/10 flex items-center justify-center">
                          <FolderGit2 className="w-4 h-4 text-[var(--rm-accent)]" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="font-medium text-[var(--rm-text)] truncate">{repoName}</p>
                          <p className="text-xs text-[var(--rm-text-muted)]">{owner}</p>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className={`w-2 h-2 rounded-full ${repo.is_indexed ? 'bg-[var(--rm-success)]' : 'bg-yellow-500'}`} />
                        <span className="text-xs text-[var(--rm-text-muted)]">
                          {repo.is_indexed ? 'Indexed' : 'Not indexed'}
                        </span>
                      </div>
                    </motion.button>
                  );
                })}
              </div>
            </FadeIn>
          )}

          {/* Quick Actions */}
          <FadeIn delay={0.3}>
            <h2 className="text-lg font-semibold mb-4">Quick Actions</h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-4">
              {quickActions.map((action, index) => {
                const Icon = action.icon;
                return (
                  <motion.div
                    key={action.label}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.3 + index * 0.05 }}
                    className="p-5 rounded-2xl bg-[var(--rm-surface)] border border-[var(--rm-border)] hover:border-[var(--rm-border-active)] transition-all duration-300 group cursor-default"
                  >
                    <div className={`w-9 h-9 rounded-xl bg-gradient-to-br ${action.color} flex items-center justify-center mb-3 shadow-lg`}>
                      <Icon className="w-4 h-4 text-white" />
                    </div>
                    <p className="font-medium text-sm text-[var(--rm-text)] mb-1">{action.label}</p>
                    <p className="text-xs text-[var(--rm-text-muted)]">{action.description}</p>
                  </motion.div>
                );
              })}
            </div>
          </FadeIn>
        </div>
      </div>
    </Layout>
  );
};
