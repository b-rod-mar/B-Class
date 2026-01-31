import { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Textarea } from './ui/textarea';
import { Label } from './ui/label';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from './ui/dialog';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from './ui/select';
import { 
  MessageSquare, 
  Send, 
  Loader2,
  Bug,
  Lightbulb,
  HelpCircle,
  Star
} from 'lucide-react';
import { toast } from 'sonner';

const FEEDBACK_TYPES = [
  { value: 'general', label: 'General Feedback', icon: MessageSquare },
  { value: 'bug', label: 'Report a Bug', icon: Bug },
  { value: 'feature', label: 'Feature Request', icon: Lightbulb },
  { value: 'question', label: 'Question', icon: HelpCircle },
];

export default function FeedbackDialog() {
  const { api, user } = useAuth();
  const [open, setOpen] = useState(false);
  const [sending, setSending] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    subject: '',
    message: '',
    feedback_type: 'general'
  });

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!formData.name || !formData.email || !formData.subject || !formData.message) {
      toast.error('Please fill in all fields');
      return;
    }

    setSending(true);
    try {
      await api.post('/feedback', formData);
      toast.success('Thank you for your feedback!');
      setFormData({
        name: user?.name || '',
        email: user?.email || '',
        subject: '',
        message: '',
        feedback_type: 'general'
      });
      setOpen(false);
    } catch (error) {
      toast.error('Failed to send feedback. Please try again.');
    } finally {
      setSending(false);
    }
  };

  const handleOpen = (isOpen) => {
    setOpen(isOpen);
    if (isOpen && user) {
      setFormData(prev => ({
        ...prev,
        name: user.name || prev.name,
        email: user.email || prev.email
      }));
    }
  };

  return (
    <Dialog open={open} onOpenChange={handleOpen}>
      <DialogTrigger asChild>
        <Button 
          variant="outline" 
          size="sm"
          className="gap-2"
          data-testid="feedback-btn"
        >
          <Star className="h-4 w-4" />
          Share Feedback
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="font-['Chivo'] flex items-center gap-2">
            <MessageSquare className="h-5 w-5 text-primary" />
            Share Your Feedback
          </DialogTitle>
          <DialogDescription>
            Help us improve Class-B HS Code Agent. Your feedback is valuable!
          </DialogDescription>
        </DialogHeader>
        
        <form onSubmit={handleSubmit} className="space-y-4 mt-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="name">Name</Label>
              <Input
                id="name"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                placeholder="Your name"
                data-testid="feedback-name"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                placeholder="your@email.com"
                data-testid="feedback-email"
              />
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="type">Feedback Type</Label>
            <Select 
              value={formData.feedback_type} 
              onValueChange={(value) => setFormData({ ...formData, feedback_type: value })}
            >
              <SelectTrigger data-testid="feedback-type">
                <SelectValue placeholder="Select type" />
              </SelectTrigger>
              <SelectContent>
                {FEEDBACK_TYPES.map((type) => (
                  <SelectItem key={type.value} value={type.value}>
                    <div className="flex items-center gap-2">
                      <type.icon className="h-4 w-4" />
                      {type.label}
                    </div>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label htmlFor="subject">Subject</Label>
            <Input
              id="subject"
              value={formData.subject}
              onChange={(e) => setFormData({ ...formData, subject: e.target.value })}
              placeholder="Brief description"
              data-testid="feedback-subject"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="message">Message</Label>
            <Textarea
              id="message"
              value={formData.message}
              onChange={(e) => setFormData({ ...formData, message: e.target.value })}
              placeholder="Share your thoughts, report issues, or suggest improvements..."
              rows={4}
              data-testid="feedback-message"
            />
          </div>

          <Button 
            type="submit" 
            className="w-full bg-primary text-primary-foreground hover:bg-primary/90"
            disabled={sending}
            data-testid="feedback-submit"
          >
            {sending ? (
              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
            ) : (
              <Send className="h-4 w-4 mr-2" />
            )}
            Send Feedback
          </Button>
        </form>
      </DialogContent>
    </Dialog>
  );
}
