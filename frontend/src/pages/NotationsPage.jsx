import { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Textarea } from '../components/ui/textarea';
import { Badge } from '../components/ui/badge';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../components/ui/select';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '../components/ui/dialog';
import { ScrollArea } from '../components/ui/scroll-area';
import { 
  Search, 
  StickyNote, 
  Plus,
  Edit2,
  Trash2,
  Loader2,
  Tag,
  FileText,
  Hash,
  Filter
} from 'lucide-react';
import { toast } from 'sonner';
import { cn, formatDate } from '../lib/utils';

const REFERENCE_TYPES = [
  { value: 'entry', label: 'Entry Reference', icon: FileText },
  { value: 'tariff_code', label: 'Tariff Code', icon: Hash },
  { value: 'general', label: 'General Note', icon: StickyNote },
];

const TYPE_COLORS = {
  'entry': 'bg-blue-500/10 text-blue-400 border-blue-500/30',
  'tariff_code': 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30',
  'general': 'bg-violet-500/10 text-violet-400 border-violet-500/30',
};

const emptyNotation = {
  label: '',
  content: '',
  reference_type: 'general',
  reference_id: ''
};

export default function NotationsPage() {
  const { api } = useAuth();
  const [notations, setNotations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterType, setFilterType] = useState('');
  const [editingNotation, setEditingNotation] = useState(null);
  const [isNew, setIsNew] = useState(false);
  const [saving, setSaving] = useState(false);
  const [wordCount, setWordCount] = useState(0);

  useEffect(() => {
    fetchNotations();
  }, []);

  const fetchNotations = async () => {
    try {
      const response = await api.get('/notations');
      setNotations(response.data);
    } catch (error) {
      toast.error('Failed to load notations');
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (searchQuery) params.append('search', searchQuery);
      if (filterType) params.append('reference_type', filterType);
      
      const response = await api.get(`/notations?${params.toString()}`);
      setNotations(response.data);
    } catch (error) {
      toast.error('Search failed');
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    if (!editingNotation?.label.trim()) {
      toast.error('Label is required');
      return;
    }
    if (!editingNotation?.content.trim()) {
      toast.error('Content is required');
      return;
    }
    if (wordCount > 100) {
      toast.error('Content exceeds 100 word limit');
      return;
    }

    setSaving(true);
    try {
      if (isNew) {
        await api.post('/notations', editingNotation);
        toast.success('Notation created');
      } else {
        await api.put(`/notations/${editingNotation.id}`, editingNotation);
        toast.success('Notation updated');
      }
      await fetchNotations();
      setEditingNotation(null);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to save notation');
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (notation) => {
    if (!window.confirm(`Delete notation "${notation.label}"?`)) return;
    
    try {
      await api.delete(`/notations/${notation.id}`);
      toast.success('Notation deleted');
      await fetchNotations();
    } catch (error) {
      toast.error('Failed to delete notation');
    }
  };

  const openNew = () => {
    setEditingNotation({ ...emptyNotation });
    setIsNew(true);
    setWordCount(0);
  };

  const openEdit = (notation) => {
    setEditingNotation({ ...notation });
    setIsNew(false);
    setWordCount(notation.content.split(/\s+/).filter(w => w).length);
  };

  const updateContent = (content) => {
    const words = content.split(/\s+/).filter(w => w).length;
    setWordCount(words);
    setEditingNotation({ ...editingNotation, content });
  };

  const clearFilters = () => {
    setSearchQuery('');
    setFilterType('');
    fetchNotations();
  };

  const getTypeLabel = (type) => {
    return REFERENCE_TYPES.find(t => t.value === type)?.label || type;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="text-muted-foreground animate-pulse">Loading notations...</div>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in" data-testid="notations-page">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold font-['Chivo'] tracking-tight flex items-center gap-3">
            <StickyNote className="h-8 w-8 text-primary" />
            My Notations
          </h1>
          <p className="text-muted-foreground mt-1">
            Personal notes and references for entries and tariff codes
          </p>
        </div>
        <Button 
          onClick={openNew}
          className="bg-primary text-primary-foreground hover:bg-primary/90"
          data-testid="add-notation-btn"
        >
          <Plus className="h-4 w-4 mr-2" />
          New Notation
        </Button>
      </div>

      {/* Search & Filter */}
      <Card>
        <CardContent className="p-6">
          <div className="flex flex-col md:flex-row gap-4">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search notations..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                className="pl-10"
                data-testid="notation-search-input"
              />
            </div>
            <div className="w-full md:w-48">
              <Select value={filterType || "all"} onValueChange={(val) => setFilterType(val === "all" ? "" : val)}>
                <SelectTrigger>
                  <Filter className="h-4 w-4 mr-2" />
                  <SelectValue placeholder="All Types" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Types</SelectItem>
                  {REFERENCE_TYPES.map((type) => (
                    <SelectItem key={type.value} value={type.value}>{type.label}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <Button onClick={handleSearch} className="bg-primary text-primary-foreground">
              <Search className="h-4 w-4 mr-2" />
              Search
            </Button>
            {(searchQuery || filterType) && (
              <Button variant="outline" onClick={clearFilters}>Clear</Button>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Notations List */}
      {notations.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-16 text-center">
            <StickyNote className="h-12 w-12 text-muted-foreground opacity-50 mb-4" />
            <p className="text-muted-foreground mb-4">No notations yet</p>
            <Button onClick={openNew}>
              <Plus className="h-4 w-4 mr-2" />
              Create Your First Notation
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {notations.map((notation) => (
            <Card key={notation.id} className="card-hover" data-testid={`notation-${notation.id}`}>
              <CardContent className="p-4">
                <div className="flex items-start justify-between gap-2 mb-3">
                  <div className="flex items-center gap-2">
                    <Tag className="h-4 w-4 text-muted-foreground" />
                    <h4 className="font-semibold truncate">{notation.label}</h4>
                  </div>
                  <Badge className={cn("text-xs flex-shrink-0", TYPE_COLORS[notation.reference_type])}>
                    {getTypeLabel(notation.reference_type)}
                  </Badge>
                </div>
                
                <p className="text-sm text-muted-foreground line-clamp-3 mb-3">
                  {notation.content}
                </p>
                
                {notation.reference_id && (
                  <p className="text-xs text-muted-foreground mb-3">
                    <span className="font-medium">Ref:</span> {notation.reference_id}
                  </p>
                )}
                
                <div className="flex items-center justify-between pt-3 border-t border-border/50">
                  <span className="text-xs text-muted-foreground">
                    {formatDate(notation.created_at)}
                  </span>
                  <div className="flex gap-1">
                    <Button 
                      variant="ghost" 
                      size="icon"
                      className="h-8 w-8"
                      onClick={() => openEdit(notation)}
                      data-testid={`edit-notation-${notation.id}`}
                    >
                      <Edit2 className="h-4 w-4" />
                    </Button>
                    <Button 
                      variant="ghost" 
                      size="icon"
                      className="h-8 w-8 text-destructive hover:text-destructive"
                      onClick={() => handleDelete(notation)}
                      data-testid={`delete-notation-${notation.id}`}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Add/Edit Dialog */}
      <Dialog open={editingNotation !== null} onOpenChange={() => setEditingNotation(null)}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle className="font-['Chivo']">
              {isNew ? 'New Notation' : 'Edit Notation'}
            </DialogTitle>
          </DialogHeader>
          {editingNotation && (
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label htmlFor="label">Label *</Label>
                <Input
                  id="label"
                  placeholder="e.g., Import Entry #12345"
                  value={editingNotation.label}
                  onChange={(e) => setEditingNotation({ ...editingNotation, label: e.target.value })}
                  data-testid="notation-label-input"
                />
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="reference_type">Reference Type</Label>
                <Select 
                  value={editingNotation.reference_type} 
                  onValueChange={(val) => setEditingNotation({ ...editingNotation, reference_type: val })}
                >
                  <SelectTrigger data-testid="notation-type-select">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {REFERENCE_TYPES.map((type) => (
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
                <Label htmlFor="reference_id">Reference ID (Optional)</Label>
                <Input
                  id="reference_id"
                  placeholder="e.g., Entry number, HS code"
                  value={editingNotation.reference_id || ''}
                  onChange={(e) => setEditingNotation({ ...editingNotation, reference_id: e.target.value })}
                  data-testid="notation-ref-input"
                />
              </div>
              
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <Label htmlFor="content">Content *</Label>
                  <span className={cn(
                    "text-xs",
                    wordCount > 100 ? "text-destructive" : "text-muted-foreground"
                  )}>
                    {wordCount}/100 words
                  </span>
                </div>
                <Textarea
                  id="content"
                  placeholder="Enter your notation (max 100 words)..."
                  value={editingNotation.content}
                  onChange={(e) => updateContent(e.target.value)}
                  rows={4}
                  data-testid="notation-content-input"
                />
              </div>
            </div>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => setEditingNotation(null)}>
              Cancel
            </Button>
            <Button 
              onClick={handleSave} 
              disabled={saving || wordCount > 100}
              className="bg-primary text-primary-foreground"
              data-testid="save-notation-btn"
            >
              {saving ? <Loader2 className="h-4 w-4 animate-spin" /> : isNew ? 'Create' : 'Save'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
