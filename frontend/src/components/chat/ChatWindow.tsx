import { useState, useRef, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Send, Sparkles, MessageSquare, Layers, BookOpen, ShieldAlert, Wand2 } from 'lucide-react';
import { MessageBubble } from './MessageBubble';
import { TypingIndicator } from './TypingIndicator';
import { apiService, type Citation } from '../../services/api';
import { useWorkspace } from '../../contexts/WorkspaceContext';

interface ChatWindowProps {
  repoName: string;
  setCitations: (citations: Citation[]) => void;
  systemPromptPrefix?: string;
  initialMessage?: string;
}

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

const suggestions = [
  { icon: MessageSquare, text: 'Explain the project architecture', color: 'from-violet-500 to-purple-600' },
  { icon: BookOpen, text: 'Generate a README for this project', color: 'from-blue-500 to-cyan-500' },
  { icon: Wand2, text: 'Find performance bottlenecks', color: 'from-emerald-500 to-teal-500' },
  { icon: ShieldAlert, text: 'Review authentication security', color: 'from-orange-500 to-red-500' },
  { icon: Layers, text: 'Suggest code improvements', color: 'from-pink-500 to-rose-500' },
];

export const ChatWindow = ({ repoName, setCitations, systemPromptPrefix, initialMessage }: ChatWindowProps) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const { setConversationHistory } = useWorkspace();

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  useEffect(() => {
    if (initialMessage && messages.length === 0) {
      handleQuery(initialMessage, true);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [initialMessage]);

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 192)}px`;
    }
  }, [input]);

  const handleQuery = async (queryText: string, isSilentUserMessage = false) => {
    if (!queryText.trim()) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: queryText,
      timestamp: new Date(),
    };

    if (!isSilentUserMessage) {
      setMessages(prev => [...prev, userMessage]);
      setConversationHistory(prev => [{ query: queryText, id: userMessage.id }, ...prev]);
    }

    setInput('');
    setIsLoading(true);

    try {
      const finalQuery = systemPromptPrefix
        ? `${systemPromptPrefix}\n\n${queryText}`
        : queryText;

      const response = await apiService.queryRepository(repoName, finalQuery);

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response.answer,
        timestamp: new Date(),
      };

      setMessages(prev => [...prev, assistantMessage]);
      setCitations(response.citations);
    } catch (error: any) {
      setMessages(prev => [...prev, {
        id: Date.now().toString(),
        role: 'assistant',
        content: `**Error**: ${error.message || 'Something went wrong.'}`,
        timestamp: new Date(),
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    handleQuery(input);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleQuery(input);
    }
  };

  return (
    <div className="flex flex-col h-full relative">
      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto">
        {messages.length === 0 && !isLoading && (
          <div className="flex flex-col items-center justify-center h-full px-6">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5 }}
              className="text-center max-w-2xl"
            >
              {/* Hero icon */}
              <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-[#8B5CF6] to-[#6D28D9] flex items-center justify-center mx-auto mb-6 shadow-glow">
                <Sparkles className="w-8 h-8 text-white" />
              </div>
              <h2 className="text-2xl font-bold mb-2 text-[var(--rm-text)]">
                What would you like to know?
              </h2>
              <p className="text-[var(--rm-text-muted)] mb-8">
                Ask anything about this repository
              </p>

              {/* Suggestion cards */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 max-w-xl mx-auto">
                {suggestions.map((suggestion, index) => {
                  const Icon = suggestion.icon;
                  return (
                    <motion.button
                      key={suggestion.text}
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: 0.2 + index * 0.05 }}
                      onClick={() => handleQuery(suggestion.text)}
                      className="flex items-center gap-3 p-4 rounded-xl bg-[var(--rm-surface)] border border-[var(--rm-border)] hover:border-[var(--rm-border-active)] transition-all duration-200 text-left group cursor-pointer hover:shadow-glow"
                    >
                      <div className={`w-8 h-8 rounded-lg bg-gradient-to-br ${suggestion.color} flex items-center justify-center flex-shrink-0`}>
                        <Icon className="w-4 h-4 text-white" />
                      </div>
                      <span className="text-sm text-[var(--rm-text-secondary)] group-hover:text-[var(--rm-text)] transition-colors">
                        {suggestion.text}
                      </span>
                    </motion.button>
                  );
                })}
              </div>
            </motion.div>
          </div>
        )}

        {messages.map(msg => (
          <MessageBubble key={msg.id} role={msg.role} content={msg.content} timestamp={msg.timestamp} />
        ))}

        {isLoading && <TypingIndicator />}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="p-4 bg-[var(--rm-bg)]">
        <form onSubmit={handleSubmit} className="relative max-w-3xl lg:max-w-[40rem] xl:max-w-[48rem] mx-auto">
          <div className="relative bg-[var(--rm-surface)] border border-[var(--rm-border)] rounded-2xl overflow-hidden focus-within:border-[var(--rm-border-active)] focus-within:shadow-glow transition-all duration-200">
            <textarea
              ref={textareaRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask anything about this repository..."
              className="w-full min-h-[52px] max-h-48 resize-none bg-transparent px-4 py-3.5 pr-14 text-sm text-[var(--rm-text)] placeholder:text-[var(--rm-text-muted)] outline-none"
              rows={1}
              disabled={isLoading}
            />
            <button
              type="submit"
              disabled={!input.trim() || isLoading}
              className="absolute right-2 bottom-2 w-9 h-9 rounded-xl bg-[var(--rm-accent)] hover:bg-[var(--rm-accent-hover)] disabled:opacity-30 disabled:hover:bg-[var(--rm-accent)] flex items-center justify-center transition-all duration-200 active:scale-95 cursor-pointer disabled:cursor-not-allowed"
            >
              <Send className="w-4 h-4 text-white" />
            </button>
          </div>
          <p className="text-center text-[11px] text-[var(--rm-text-muted)] mt-2">
            RepoMind can make mistakes. Verify important information.
          </p>
        </form>
      </div>
    </div>
  );
};
