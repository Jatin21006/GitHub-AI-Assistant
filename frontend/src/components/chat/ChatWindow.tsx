import { useState, useRef, useEffect } from 'react';
import { Send, Loader2 } from 'lucide-react';
import { Button } from '../ui/Button';
import { MessageBubble } from './MessageBubble';
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
}

export const ChatWindow = ({ repoName, setCitations, systemPromptPrefix, initialMessage }: ChatWindowProps) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const { setConversationHistory } = useWorkspace();

  // Scroll to bottom
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    if (initialMessage && messages.length === 0) {
      handleQuery(initialMessage, true);
    }
  }, [initialMessage]);

  const handleQuery = async (queryText: string, isSilentUserMessage = false) => {
    if (!queryText.trim()) return;
    
    const userMessage: Message = { id: Date.now().toString(), role: 'user', content: queryText };
    
    if (!isSilentUserMessage) {
      setMessages(prev => [...prev, userMessage]);
      setConversationHistory(prev => [{ query: queryText, id: userMessage.id }, ...prev]);
    }
    
    setInput('');
    setIsLoading(true);

    try {
      // Append system instructions if we are in a special tab
      const finalQuery = systemPromptPrefix 
        ? `${systemPromptPrefix}\n\n${queryText}` 
        : queryText;
        
      const response = await apiService.queryRepository(repoName, finalQuery);
      
      const assistantMessage: Message = { 
        id: (Date.now() + 1).toString(), 
        role: 'assistant', 
        content: response.answer 
      };
      
      setMessages(prev => [...prev, assistantMessage]);
      setCitations(response.citations);
      
    } catch (error: any) {
      setMessages(prev => [...prev, {
        id: Date.now().toString(),
        role: 'assistant',
        content: `**Error**: ${error.message || 'Something went wrong.'}`
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
      <div className="flex-1 overflow-y-auto">
        {messages.length === 0 && !isLoading && (
          <div className="flex flex-col items-center justify-center h-full text-muted-foreground">
            <p>No messages yet. Start a conversation!</p>
          </div>
        )}
        
        {messages.map(msg => (
          <MessageBubble key={msg.id} role={msg.role} content={msg.content} />
        ))}
        
        {isLoading && (
          <div className="flex items-center justify-center py-6 text-muted-foreground">
            <Loader2 className="w-6 h-6 animate-spin mr-2" />
            <span>Thinking...</span>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className="p-4 border-t border-border bg-background">
        <form onSubmit={handleSubmit} className="relative max-w-3xl lg:max-w-[40rem] xl:max-w-[48rem] mx-auto flex items-end gap-2">
          <div className="relative flex-1 bg-background border border-input rounded-xl overflow-hidden focus-within:ring-2 focus-within:ring-ring focus-within:ring-offset-2">
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask anything about the repository..."
              className="w-full max-h-48 min-h-[56px] resize-none bg-transparent px-4 py-4 pr-12 text-sm outline-none"
              rows={1}
              disabled={isLoading}
            />
            <Button 
              type="submit" 
              size="icon" 
              variant="ghost" 
              className="absolute right-2 bottom-2 text-primary hover:bg-muted/50"
              disabled={!input.trim() || isLoading}
            >
              <Send className="w-5 h-5" />
            </Button>
          </div>
        </form>
        <p className="text-center text-xs text-muted-foreground mt-2">
          RepoMind can make mistakes. Verify important information.
        </p>
      </div>
    </div>
  );
};
