import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { FolderGit2, Loader2 } from 'lucide-react';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { apiService } from '../services/api';
import { useWorkspace } from '../contexts/WorkspaceContext';

export const LandingPage = () => {
  const [url, setUrl] = useState('');
  const [status, setStatus] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const navigate = useNavigate();
  const { setCurrentRepo } = useWorkspace();

  const handleIndex = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!url) return;

    setLoading(true);
    setError(null);
    setStatus('Cloning repository...');

    try {
      // 1. Clone
      const cloneRes = await apiService.cloneRepository(url);
      const repoName = cloneRes.repository_name;
      
      // 2. Index
      setStatus('Parsing and building vector store...');
      await apiService.indexRepository(repoName);
      
      // 3. Set Context & Navigate
      setStatus('Indexing complete! Navigating...');
      
      // We need owner/repo to navigate
      const parts = repoName.split('/');
      if (parts.length === 2) {
        const [owner, repo] = parts;
        const statusRes = await apiService.getRepositoryStatus(owner, repo);
        setCurrentRepo(statusRes);
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

  return (
    <div className="min-h-screen flex items-center justify-center bg-background text-foreground p-4">
      <div className="w-full max-w-md space-y-8 text-center">
        
        <div className="space-y-4">
          <div className="flex justify-center">
            <div className="p-3 bg-primary/10 rounded-2xl">
              <FolderGit2 className="w-12 h-12 text-primary" />
            </div>
          </div>
          <h1 className="text-4xl font-bold tracking-tight">RepoMind</h1>
          <p className="text-muted-foreground text-lg">
            Understand, explore and improve any GitHub repository with AI.
          </p>
        </div>

        <form onSubmit={handleIndex} className="space-y-4 pt-8">
          <div className="relative">
            <FolderGit2 className="absolute left-3 top-3 h-5 w-5 text-muted-foreground" />
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
            className="w-full h-12 text-md" 
            disabled={!url || loading}
          >
            {loading ? (
              <>
                <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                {status}
              </>
            ) : (
              'Clone & Index Repository'
            )}
          </Button>

          {error && (
            <div className="p-4 rounded-md bg-destructive/10 border border-destructive/20 text-destructive text-sm text-left">
              <p className="font-semibold">Error</p>
              <p>{error}</p>
            </div>
          )}
        </form>

      </div>
    </div>
  );
};
