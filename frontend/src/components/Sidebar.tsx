import { FileText, FolderGit2, History, Plus } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useWorkspace } from '../contexts/WorkspaceContext';
import { Button } from './ui/Button';

export const Sidebar = () => {
  const { currentRepo, conversationHistory } = useWorkspace();
  const navigate = useNavigate();

  return (
    <div className="w-64 border-r border-border bg-muted/20 flex flex-col h-full">
      <div className="p-4 border-b border-border">
        <h2 className="font-semibold text-lg flex items-center gap-2">
          <FolderGit2 className="w-5 h-5" />
          RepoMind
        </h2>
      </div>

      <div className="flex-1 overflow-y-auto p-3 space-y-6">
        {/* Repositories Section */}
        <div>
          <div className="flex items-center justify-between mb-2 px-2">
            <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
              Repositories
            </h3>
            <Button variant="ghost" size="icon" className="h-5 w-5" onClick={() => navigate('/')}>
              <Plus className="w-4 h-4" />
            </Button>
          </div>
          
          <div className="space-y-1">
            {currentRepo ? (
              <div className="flex items-center gap-2 px-2 py-1.5 rounded-md bg-secondary text-sm font-medium">
                <FolderGit2 className="w-4 h-4 text-muted-foreground" />
                <span className="truncate">{currentRepo.repository_name}</span>
              </div>
            ) : (
              <div className="px-2 py-1.5 text-sm text-muted-foreground italic">
                No active repository
              </div>
            )}
          </div>
        </div>

        {/* Conversations Section */}
        <div>
          <div className="flex items-center justify-between mb-2 px-2">
            <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
              Recent Chats
            </h3>
          </div>
          
          <div className="space-y-1">
            {conversationHistory.length > 0 ? (
              conversationHistory.map((conv) => (
                <button
                  key={conv.id}
                  className="w-full flex items-center gap-2 px-2 py-1.5 rounded-md hover:bg-accent text-sm text-left"
                >
                  <History className="w-4 h-4 text-muted-foreground flex-shrink-0" />
                  <span className="truncate">{conv.query}</span>
                </button>
              ))
            ) : (
              <div className="px-2 py-1.5 text-sm text-muted-foreground italic">
                No recent chats
              </div>
            )}
          </div>
        </div>
      </div>
      
      <div className="p-4 border-t border-border">
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <FileText className="w-4 h-4" />
          <span>Workspace</span>
        </div>
      </div>
    </div>
  );
};
