import type { Citation } from '../services/api';
import { BookOpen, FileCode2 } from 'lucide-react';

interface SourcePanelProps {
  citations: Citation[];
}

export const SourcePanel = ({ citations }: SourcePanelProps) => {
  if (citations.length === 0) {
    return (
      <div className="w-80 border-l border-border bg-background p-4 flex flex-col h-full hidden lg:flex">
        <h3 className="font-semibold text-sm flex items-center gap-2 mb-4">
          <BookOpen className="w-4 h-4" />
          Sources Used
        </h3>
        <div className="flex-1 flex items-center justify-center text-sm text-muted-foreground italic text-center">
          No sources referenced yet. Ask a question to see citations.
        </div>
      </div>
    );
  }

  return (
    <div className="w-80 border-l border-border bg-background flex flex-col h-full hidden lg:flex">
      <div className="p-4 border-b border-border">
        <h3 className="font-semibold text-sm flex items-center gap-2">
          <BookOpen className="w-4 h-4" />
          Sources Used
        </h3>
      </div>
      
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {citations.map((citation, index) => (
          <div key={index} className="border border-border rounded-md p-3 hover:bg-accent/50 transition-colors cursor-pointer group">
            <div className="flex items-start gap-2 mb-2">
              <FileCode2 className="w-4 h-4 text-primary mt-0.5" />
              <div className="flex-1 overflow-hidden">
                <p className="text-sm font-medium truncate" title={citation.file_path}>
                  {citation.file_path.split('/').pop()}
                </p>
                <p className="text-xs text-muted-foreground truncate" title={citation.file_path}>
                  {citation.file_path}
                </p>
              </div>
            </div>
            
            <div className="text-xs bg-muted p-2 rounded text-muted-foreground font-mono overflow-x-auto max-h-24 opacity-80 group-hover:opacity-100">
              {citation.snippet}
            </div>
            <div className="text-xs text-muted-foreground mt-2 text-right">
              Lines {citation.start_line}-{citation.end_line}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
