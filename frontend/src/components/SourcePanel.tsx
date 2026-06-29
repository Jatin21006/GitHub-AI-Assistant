import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import type { Citation } from '../services/api';
import { BookOpen, FileCode2, ChevronDown, ChevronRight, Hash, Eye } from 'lucide-react';

interface SourcePanelProps {
  citations: Citation[];
}

export const SourcePanel = ({ citations }: SourcePanelProps) => {
  const [expandedIndex, setExpandedIndex] = useState<number | null>(null);
  const [showAll, setShowAll] = useState(false);

  // File extension to color mapping
  const getFileColor = (path: string) => {
    const ext = path.split('.').pop()?.toLowerCase();
    const colorMap: Record<string, string> = {
      py: 'bg-blue-500',
      ts: 'bg-blue-400',
      tsx: 'bg-blue-400',
      js: 'bg-yellow-500',
      jsx: 'bg-yellow-500',
      md: 'bg-gray-400',
      json: 'bg-green-500',
      css: 'bg-pink-500',
      html: 'bg-orange-500',
      yml: 'bg-red-400',
      yaml: 'bg-red-400',
    };
    return colorMap[ext || ''] || 'bg-[var(--rm-accent)]';
  };

  const visibleCitations = showAll ? citations : citations.slice(0, 5);

  if (citations.length === 0) {
    return (
      <div className="w-full h-full border-l border-[var(--rm-border)] bg-[var(--rm-surface)]/50 p-5 flex flex-col">
        <div className="flex items-center gap-2 mb-6">
          <BookOpen className="w-4 h-4 text-[var(--rm-accent)]" />
          <h3 className="font-semibold text-sm text-[var(--rm-text)]">Sources Used</h3>
        </div>
        <div className="flex-1 flex flex-col items-center justify-center text-center px-4">
          <div className="w-12 h-12 rounded-2xl bg-[var(--rm-surface)] border border-[var(--rm-border)] flex items-center justify-center mb-4">
            <FileCode2 className="w-5 h-5 text-[var(--rm-text-muted)]" />
          </div>
          <p className="text-sm text-[var(--rm-text-muted)] leading-relaxed">
            No sources referenced yet. Ask a question to see relevant code citations.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="w-full h-full border-l border-[var(--rm-border)] bg-[var(--rm-surface)]/50 flex flex-col">
      {/* Header */}
      <div className="p-5 border-b border-[var(--rm-border)] flex items-center justify-between flex-shrink-0">
        <div className="flex items-center gap-2">
          <BookOpen className="w-4 h-4 text-[var(--rm-accent)]" />
          <h3 className="font-semibold text-sm text-[var(--rm-text)]">Sources Used</h3>
        </div>
        <span className="text-xs font-medium px-2 py-0.5 rounded-full bg-[var(--rm-accent)]/15 text-[var(--rm-accent)]">
          {citations.length}
        </span>
      </div>

      {/* Sources List */}
      <div className="flex-1 overflow-y-auto p-4 space-y-2">
        {visibleCitations.map((citation, index) => {
          const isExpanded = expandedIndex === index;
          const fileName = citation.file_path.split('/').pop();
          const colorClass = getFileColor(citation.file_path);

          return (
            <motion.div
              key={index}
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.03 }}
            >
              <button
                onClick={() => setExpandedIndex(isExpanded ? null : index)}
                className="w-full text-left p-3 rounded-xl border border-[var(--rm-border)] hover:border-[var(--rm-border-active)] bg-[var(--rm-bg)]/50 hover:bg-[var(--rm-bg)] transition-all duration-200 cursor-pointer group"
              >
                <div className="flex items-center gap-2.5">
                  <div className={`w-2 h-2 rounded-full ${colorClass} flex-shrink-0`} />
                  <FileCode2 className="w-3.5 h-3.5 text-[var(--rm-text-muted)] flex-shrink-0" />
                  <span className="text-sm font-medium text-[var(--rm-text)] truncate flex-1">{fileName}</span>
                  {isExpanded
                    ? <ChevronDown className="w-3.5 h-3.5 text-[var(--rm-text-muted)]" />
                    : <ChevronRight className="w-3.5 h-3.5 text-[var(--rm-text-muted)]" />
                  }
                </div>

                {/* File path */}
                <p className="text-[11px] text-[var(--rm-text-muted)] mt-1 ml-[18px] truncate">
                  {citation.file_path}
                </p>
              </button>

              {/* Expanded content */}
              <AnimatePresence>
                {isExpanded && (
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: 'auto', opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    transition={{ duration: 0.2 }}
                    className="overflow-hidden"
                  >
                    <div className="px-3 pt-2 pb-3">
                      {/* Line range */}
                      <div className="flex items-center gap-1.5 mb-2 text-[11px] text-[var(--rm-text-muted)]">
                        <Hash className="w-3 h-3" />
                        <span>Lines {citation.start_line}–{citation.end_line}</span>
                      </div>
                      {/* Code snippet */}
                      <div className="text-xs bg-[var(--rm-bg)] border border-[var(--rm-border)] p-3 rounded-lg font-mono text-[var(--rm-text-secondary)] overflow-x-auto max-h-40 leading-relaxed">
                        {citation.snippet}
                      </div>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </motion.div>
          );
        })}
      </div>

      {/* View All button */}
      {citations.length > 5 && (
        <div className="p-4 border-t border-[var(--rm-border)] flex-shrink-0">
          <button
            onClick={() => setShowAll(!showAll)}
            className="w-full flex items-center justify-center gap-2 py-2 rounded-xl border border-[var(--rm-border)] hover:border-[var(--rm-border-active)] bg-[var(--rm-bg)]/50 hover:bg-[var(--rm-bg)] text-sm text-[var(--rm-text-secondary)] hover:text-[var(--rm-accent)] transition-all duration-200 cursor-pointer"
          >
            <Eye className="w-4 h-4" />
            {showAll ? 'Show Less' : `View All Sources`}
          </button>
        </div>
      )}
    </div>
  );
};
