import { useState, useRef, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { ScrollArea } from './ui/scroll-area';
import { Card } from './ui/card';
import { 
  MessageCircle, 
  X, 
  Send, 
  Loader2, 
  Minimize2,
  Maximize2,
  HelpCircle,
  FileText,
  Globe,
  BookOpen,
  Phone
} from 'lucide-react';
import { cn } from '../lib/utils';

// Bahamian Flag SVG Component
const BahamianFlag = ({ className }) => (
  <svg viewBox="0 0 36 24" className={className} xmlns="http://www.w3.org/2000/svg">
    <rect width="36" height="24" fill="#00778B"/>
    <rect y="8" width="36" height="8" fill="#FFC72C"/>
    <polygon points="0,0 12,12 0,24" fill="#000"/>
  </svg>
);

const quickActions = [
  { icon: HelpCircle, label: 'How to classify items?', query: 'How do I classify items using this app?' },
  { icon: FileText, label: 'Which forms do I need?', query: 'What customs forms do I need for importing goods to The Bahamas?' },
  { icon: Globe, label: 'Ports of entry', query: 'What are the main ports of entry in The Bahamas?' },
  { icon: BookOpen, label: 'HS Code help', query: 'How do I find the correct HS code for my product?' },
  { icon: Phone, label: 'Contact Customs', query: 'How can I contact Bahamas Customs directly?' },
];

export default function ClassiChat() {
  const { api, user } = useAuth();
  const [isOpen, setIsOpen] = useState(false);
  const [isMinimized, setIsMinimized] = useState(false);
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: `Hello! I'm Classi, your Bahamas Customs assistant. 🇧🇸

I can help you with:
• HS code classification guidance
• Customs forms and procedures
• Duty rates and calculations
• Ports of entry information
• Import/export regulations
• Contact information for Bahamas Customs

How can I assist you today?`
    }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const scrollRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  useEffect(() => {
    if (isOpen && !isMinimized && inputRef.current) {
      inputRef.current.focus();
    }
  }, [isOpen, isMinimized]);

  const sendMessage = async (messageText) => {
    if (!messageText.trim() || loading) return;

    const userMessage = { role: 'user', content: messageText };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      const response = await api.post('/classi/chat', { message: messageText });
      setMessages(prev => [...prev, { role: 'assistant', content: response.data.response }]);
    } catch (error) {
      setMessages(prev => [...prev, { 
        role: 'assistant', 
        content: 'I apologize, but I encountered an issue. Please try again or contact Bahamas Customs directly at +1 (242) 325-6550.' 
      }]);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    sendMessage(input);
  };

  const handleQuickAction = (query) => {
    sendMessage(query);
  };

  if (!user) return null;

  return (
    <>
      {/* Chat Widget Button */}
      {!isOpen && (
        <button
          onClick={() => setIsOpen(true)}
          className="fixed bottom-6 right-6 z-50 w-14 h-14 rounded-full bg-primary shadow-lg hover:bg-primary/90 transition-all duration-300 hover:scale-110 flex items-center justify-center group"
          data-testid="classi-chat-toggle"
        >
          <div className="relative">
            <BahamianFlag className="w-8 h-8 rounded-full" />
            <span className="absolute -top-1 -right-1 w-3 h-3 bg-green-500 rounded-full border-2 border-primary animate-pulse" />
          </div>
          <span className="absolute -top-10 right-0 bg-card text-foreground text-sm px-3 py-1 rounded-lg shadow-lg opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap">
            Chat with Classi
          </span>
        </button>
      )}

      {/* Chat Window */}
      {isOpen && (
        <Card 
          className={cn(
            "fixed z-50 shadow-2xl border border-border/50 transition-all duration-300",
            isMinimized 
              ? "bottom-6 right-6 w-72 h-14" 
              : "bottom-6 right-6 w-96 h-[600px] max-h-[80vh]"
          )}
          data-testid="classi-chat-window"
        >
          {/* Header */}
          <div className="flex items-center justify-between p-3 border-b border-border bg-card rounded-t-lg">
            <div className="flex items-center gap-3">
              <div className="relative">
                <div className="w-10 h-10 rounded-full overflow-hidden border-2 border-primary/30">
                  <BahamianFlag className="w-full h-full" />
                </div>
                <span className="absolute bottom-0 right-0 w-3 h-3 bg-green-500 rounded-full border-2 border-card" />
              </div>
              <div>
                <h3 className="font-semibold text-sm">Classi</h3>
                <p className="text-xs text-muted-foreground">Customs Help Desk</p>
              </div>
            </div>
            <div className="flex items-center gap-1">
              <Button 
                variant="ghost" 
                size="icon" 
                className="h-8 w-8"
                onClick={() => setIsMinimized(!isMinimized)}
              >
                {isMinimized ? <Maximize2 className="h-4 w-4" /> : <Minimize2 className="h-4 w-4" />}
              </Button>
              <Button 
                variant="ghost" 
                size="icon" 
                className="h-8 w-8"
                onClick={() => setIsOpen(false)}
              >
                <X className="h-4 w-4" />
              </Button>
            </div>
          </div>

          {/* Chat Content */}
          {!isMinimized && (
            <>
              {/* Messages */}
              <ScrollArea className="flex-1 h-[calc(100%-140px)] p-4" ref={scrollRef}>
                <div className="space-y-4">
                  {messages.map((msg, idx) => (
                    <div 
                      key={idx} 
                      className={cn(
                        "flex gap-2",
                        msg.role === 'user' ? "justify-end" : "justify-start"
                      )}
                    >
                      {msg.role === 'assistant' && (
                        <div className="w-8 h-8 rounded-full overflow-hidden flex-shrink-0 border border-primary/30">
                          <BahamianFlag className="w-full h-full" />
                        </div>
                      )}
                      <div 
                        className={cn(
                          "max-w-[80%] rounded-lg px-3 py-2 text-sm",
                          msg.role === 'user' 
                            ? "bg-primary text-primary-foreground" 
                            : "bg-muted"
                        )}
                      >
                        <p className="whitespace-pre-wrap">{msg.content}</p>
                      </div>
                    </div>
                  ))}
                  {loading && (
                    <div className="flex gap-2 justify-start">
                      <div className="w-8 h-8 rounded-full overflow-hidden flex-shrink-0 border border-primary/30">
                        <BahamianFlag className="w-full h-full" />
                      </div>
                      <div className="bg-muted rounded-lg px-3 py-2">
                        <Loader2 className="h-4 w-4 animate-spin" />
                      </div>
                    </div>
                  )}
                </div>

                {/* Quick Actions (show only if few messages) */}
                {messages.length <= 2 && !loading && (
                  <div className="mt-4 space-y-2">
                    <p className="text-xs text-muted-foreground">Quick questions:</p>
                    <div className="flex flex-wrap gap-2">
                      {quickActions.map((action, idx) => (
                        <button
                          key={idx}
                          onClick={() => handleQuickAction(action.query)}
                          className="flex items-center gap-1.5 text-xs bg-muted hover:bg-muted/80 px-2.5 py-1.5 rounded-full transition-colors"
                        >
                          <action.icon className="h-3 w-3" />
                          {action.label}
                        </button>
                      ))}
                    </div>
                  </div>
                )}
              </ScrollArea>

              {/* Input */}
              <form onSubmit={handleSubmit} className="p-3 border-t border-border">
                <div className="flex gap-2">
                  <Input
                    ref={inputRef}
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    placeholder="Ask Classi anything..."
                    className="flex-1"
                    disabled={loading}
                    data-testid="classi-input"
                  />
                  <Button 
                    type="submit" 
                    size="icon" 
                    disabled={loading || !input.trim()}
                    data-testid="classi-send"
                  >
                    <Send className="h-4 w-4" />
                  </Button>
                </div>
              </form>
            </>
          )}
        </Card>
      )}
    </>
  );
}
