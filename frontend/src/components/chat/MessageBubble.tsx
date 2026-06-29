import { useState } from 'react';
import { motion } from 'framer-motion';
import { Bot, User, Copy, Check } from 'lucide-react';
import { cn } from '../../utils/cn';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeHighlight from 'rehype-highlight';
import 'highlight.js/styles/github-dark.css';

interface MessageBubbleProps {
  content: string;
  role: 'user' | 'assistant';
  timestamp?: Date;
}

const CodeBlock = ({ children, className }: { children: string; className?: string }) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(children);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="relative group">
      <pre className={className}>
        <code>{children}</code>
      </pre>
      <button
        onClick={handleCopy}
        className="absolute top-2 right-2 p-1.5 rounded-lg bg-[var(--rm-surface-hover)] border border-[var(--rm-border)] opacity-0 group-hover:opacity-100 transition-opacity text-[var(--rm-text-muted)] hover:text-[var(--rm-text)]"
        title="Copy code"
      >
        {copied ? <Check className="w-3.5 h-3.5 text-[var(--rm-success)]" /> : <Copy className="w-3.5 h-3.5" />}
      </button>
    </div>
  );
};

export const MessageBubble = ({ content, role, timestamp }: MessageBubbleProps) => {
  const isUser = role === 'user';

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, ease: 'easeOut' }}
      className={cn(
        "flex w-full px-4 py-5 md:px-6",
        isUser ? "bg-transparent" : "bg-[var(--rm-surface)]/30"
      )}
    >
      <div className="mx-auto flex flex-1 gap-4 md:max-w-3xl lg:max-w-[40rem] xl:max-w-[48rem]">
        {/* Avatar */}
        <div className="flex-shrink-0">
          <div className={cn(
            "w-8 h-8 rounded-xl flex items-center justify-center shadow-md",
            isUser
              ? "bg-gradient-to-br from-[#8B5CF6] to-[#6D28D9]"
              : "bg-gradient-to-br from-emerald-500 to-teal-600"
          )}>
            {isUser ? <User className="w-4 h-4 text-white" /> : <Bot className="w-4 h-4 text-white" />}
          </div>
        </div>

        {/* Content */}
        <div className="relative flex w-full flex-col min-w-0">
          <div className="flex items-center gap-2 mb-1.5">
            <span className="font-semibold text-sm text-[var(--rm-text)]">
              {isUser ? 'You' : 'RepoMind'}
            </span>
            {timestamp && (
              <span className="text-[11px] text-[var(--rm-text-muted)]">
                {timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
              </span>
            )}
          </div>
          <div className="prose max-w-none break-words">
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              rehypePlugins={[rehypeHighlight]}
              components={{
                pre: ({ children, ...props }) => {
                  // Extract the text content from the code block
                  const codeElement = children as any;
                  if (codeElement?.props?.children) {
                    return (
                      <CodeBlock className={codeElement.props.className}>
                        {String(codeElement.props.children).replace(/\n$/, '')}
                      </CodeBlock>
                    );
                  }
                  return <pre {...props}>{children}</pre>;
                },
              }}
            >
              {content}
            </ReactMarkdown>
          </div>
        </div>
      </div>
    </motion.div>
  );
};
