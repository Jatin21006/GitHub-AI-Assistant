import { Bot, User } from 'lucide-react';
import { cn } from '../../utils/cn';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeHighlight from 'rehype-highlight';
import 'highlight.js/styles/github-dark.css';

interface MessageBubbleProps {
  content: string;
  role: 'user' | 'assistant';
}

export const MessageBubble = ({ content, role }: MessageBubbleProps) => {
  const isUser = role === 'user';
  
  return (
    <div className={cn(
      "flex w-full px-4 py-6 text-base md:px-5 lg:px-1 xl:px-5",
      isUser ? "bg-background" : "bg-muted/30"
    )}>
      <div className="mx-auto flex flex-1 gap-4 text-base md:gap-5 lg:gap-6 md:max-w-3xl lg:max-w-[40rem] xl:max-w-[48rem]">
        <div className="flex-shrink-0 flex flex-col relative items-end">
          <div className={cn(
            "w-8 h-8 rounded-sm flex items-center justify-center",
            isUser ? "bg-primary text-primary-foreground" : "bg-emerald-600 text-white"
          )}>
            {isUser ? <User className="w-5 h-5" /> : <Bot className="w-5 h-5" />}
          </div>
        </div>
        
        <div className="relative flex w-full flex-col lg:w-[calc(100%-115px)]">
          <div className="font-semibold mb-1">
            {isUser ? 'You' : 'RepoMind'}
          </div>
          <div className="prose prose-invert max-w-none break-words">
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              rehypePlugins={[rehypeHighlight]}
            >
              {content}
            </ReactMarkdown>
          </div>
        </div>
      </div>
    </div>
  );
};
