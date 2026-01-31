import { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Textarea } from '../components/ui/textarea';
import { Switch } from '../components/ui/switch';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '../components/ui/dialog';
import { ScrollArea } from '../components/ui/scroll-area';
import { 
  BookOpen, 
  Search, 
  Plus,
  Edit2,
  Trash2,
  Shield,
  AlertTriangle,
  Loader2,
  FileCode,
  Upload,
  Download,
  FileSpreadsheet,
  X,
  CheckCircle
} from 'lucide-react';
import { toast } from 'sonner';
import { cn } from '../lib/utils';

const emptyHSCode = {
  code: '',
  description: '',
  chapter: '',
  section: '',
  notes: '',
  duty_rate: '',
  bahamas_extension: '',
  is_restricted: false,
  requires_permit: false
};

export default function HSLibraryPage() {
  const { api } = useAuth();
  const [hsCodes, setHsCodes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [editingCode, setEditingCode] = useState(null);
  const [isNew, setIsNew] = useState(false);
  const [saving, setSaving] = useState(false);
  
  // Import state
  const [importFile, setImportFile] = useState(null);
  const [importing, setImporting] = useState(false);
  const [importResult, setImportResult] = useState(null);
  const [isDragging, setIsDragging] = useState(false);

  useEffect(() => {
    fetchHSCodes();
  }, []);

  const fetchHSCodes = async () => {
    try {
      const response = await api.get('/hs-codes');
      setHsCodes(response.data);
    } catch (error) {
      toast.error('Failed to load HS codes');
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    if (!editingCode?.code || !editingCode?.description || !editingCode?.chapter) {
      toast.error('Code, description, and chapter are required');
      return;
    }

    setSaving(true);
    try {
      if (isNew) {
        await api.post('/hs-codes', editingCode);
        toast.success('HS code added to library');
      } else {
        await api.put(`/hs-codes/${editingCode.id}`, editingCode);
        toast.success('HS code updated');
      }
      await fetchHSCodes();
      setEditingCode(null);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to save HS code');
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (code) => {
    if (!window.confirm(`Delete HS code ${code.code}?`)) return;
    
    try {
      await api.delete(`/hs-codes/${code.id}`);
      toast.success('HS code deleted');
      await fetchHSCodes();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to delete HS code');
    }
  };

  const filteredCodes = hsCodes.filter(code => 
    code.code.toLowerCase().includes(searchTerm.toLowerCase()) ||
    code.description.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const openNew = () => {
    setEditingCode({ ...emptyHSCode });
    setIsNew(true);
  };

  const openEdit = (code) => {
    setEditingCode({ ...code });
    setIsNew(false);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="text-muted-foreground animate-pulse">Loading HS codes...</div>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in" data-testid="hs-library-page">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold font-['Chivo'] tracking-tight">
            HS Code Library
          </h1>
          <p className="text-muted-foreground mt-1">
            Manage your Bahamas-specific HS code database
          </p>
        </div>
        <div className="flex gap-3">
          <div className="relative w-full sm:w-64">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search codes..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-9"
              data-testid="search-hs-input"
            />
          </div>
          <Button 
            onClick={openNew}
            className="bg-primary text-primary-foreground hover:bg-primary/90"
            data-testid="add-hs-btn"
          >
            <Plus className="h-4 w-4 mr-2" />
            Add Code
          </Button>
        </div>
      </div>

      {filteredCodes.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12">
            <BookOpen className="h-12 w-12 text-muted-foreground opacity-50 mb-4" />
            <p className="text-muted-foreground mb-4">
              {searchTerm ? 'No codes match your search' : 'No HS codes in library'}
            </p>
            {!searchTerm && (
              <Button onClick={openNew}>
                <Plus className="h-4 w-4 mr-2" />
                Add Your First HS Code
              </Button>
            )}
          </CardContent>
        </Card>
      ) : (
        <Card>
          <CardContent className="p-0">
            <ScrollArea className="h-[600px]">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>HS Code</th>
                    <th>Description</th>
                    <th>Chapter</th>
                    <th>Duty Rate</th>
                    <th>Flags</th>
                    <th className="w-24"></th>
                  </tr>
                </thead>
                <tbody>
                  {filteredCodes.map((code, index) => (
                    <tr key={code.id} data-testid={`hs-row-${code.code}`}>
                      <td>
                        <code className="hs-code bg-primary/10 px-2 py-1 rounded">
                          {code.code}
                        </code>
                        {code.bahamas_extension && (
                          <span className="text-xs text-muted-foreground ml-1">
                            .{code.bahamas_extension}
                          </span>
                        )}
                      </td>
                      <td>
                        <p className="max-w-xs truncate" title={code.description}>
                          {code.description}
                        </p>
                      </td>
                      <td className="font-mono text-sm">{code.chapter}</td>
                      <td className="text-sm">{code.duty_rate || '-'}</td>
                      <td>
                        <div className="flex gap-1">
                          {code.is_restricted && (
                            <Badge variant="outline" className="bg-rose-500/10 text-rose-400 border-rose-500/30 text-xs">
                              <Shield className="h-3 w-3" />
                            </Badge>
                          )}
                          {code.requires_permit && (
                            <Badge variant="outline" className="bg-amber-500/10 text-amber-400 border-amber-500/30 text-xs">
                              <AlertTriangle className="h-3 w-3" />
                            </Badge>
                          )}
                        </div>
                      </td>
                      <td>
                        <div className="flex gap-1">
                          <Button 
                            variant="ghost" 
                            size="icon"
                            onClick={() => openEdit(code)}
                            data-testid={`edit-hs-${code.code}`}
                          >
                            <Edit2 className="h-4 w-4" />
                          </Button>
                          <Button 
                            variant="ghost" 
                            size="icon"
                            className="text-destructive hover:text-destructive"
                            onClick={() => handleDelete(code)}
                            data-testid={`delete-hs-${code.code}`}
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </ScrollArea>
          </CardContent>
        </Card>
      )}

      {/* Add/Edit Dialog */}
      <Dialog open={editingCode !== null} onOpenChange={() => setEditingCode(null)}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle className="font-['Chivo']">
              {isNew ? 'Add New HS Code' : 'Edit HS Code'}
            </DialogTitle>
          </DialogHeader>
          {editingCode && (
            <div className="space-y-4 py-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="code">HS Code *</Label>
                  <Input
                    id="code"
                    value={editingCode.code}
                    onChange={(e) => setEditingCode({ ...editingCode, code: e.target.value })}
                    placeholder="e.g., 8471.30"
                    className="font-mono"
                    data-testid="hs-code-input"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="chapter">Chapter *</Label>
                  <Input
                    id="chapter"
                    value={editingCode.chapter}
                    onChange={(e) => setEditingCode({ ...editingCode, chapter: e.target.value })}
                    placeholder="e.g., 84"
                    className="font-mono"
                    data-testid="hs-chapter-input"
                  />
                </div>
              </div>
              <div className="space-y-2">
                <Label htmlFor="description">Description *</Label>
                <Input
                  id="description"
                  value={editingCode.description}
                  onChange={(e) => setEditingCode({ ...editingCode, description: e.target.value })}
                  placeholder="Official HS nomenclature description"
                  data-testid="hs-description-input"
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="section">Section</Label>
                  <Input
                    id="section"
                    value={editingCode.section || ''}
                    onChange={(e) => setEditingCode({ ...editingCode, section: e.target.value })}
                    placeholder="e.g., XVI"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="bahamas_extension">Bahamas Extension</Label>
                  <Input
                    id="bahamas_extension"
                    value={editingCode.bahamas_extension || ''}
                    onChange={(e) => setEditingCode({ ...editingCode, bahamas_extension: e.target.value })}
                    placeholder="e.g., 10 (for 8-10 digit codes)"
                    className="font-mono"
                  />
                </div>
              </div>
              <div className="space-y-2">
                <Label htmlFor="duty_rate">Duty Rate</Label>
                <Input
                  id="duty_rate"
                  value={editingCode.duty_rate || ''}
                  onChange={(e) => setEditingCode({ ...editingCode, duty_rate: e.target.value })}
                  placeholder="e.g., 5%, Free, $0.10/kg"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="notes">Notes</Label>
                <Textarea
                  id="notes"
                  value={editingCode.notes || ''}
                  onChange={(e) => setEditingCode({ ...editingCode, notes: e.target.value })}
                  placeholder="Additional notes, exclusions, or clarifications..."
                  rows={3}
                />
              </div>
              <div className="flex gap-6 pt-2">
                <div className="flex items-center gap-2">
                  <Switch
                    id="is_restricted"
                    checked={editingCode.is_restricted}
                    onCheckedChange={(checked) => setEditingCode({ ...editingCode, is_restricted: checked })}
                  />
                  <Label htmlFor="is_restricted" className="text-sm">Restricted Item</Label>
                </div>
                <div className="flex items-center gap-2">
                  <Switch
                    id="requires_permit"
                    checked={editingCode.requires_permit}
                    onCheckedChange={(checked) => setEditingCode({ ...editingCode, requires_permit: checked })}
                  />
                  <Label htmlFor="requires_permit" className="text-sm">Requires Permit</Label>
                </div>
              </div>
            </div>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => setEditingCode(null)}>
              Cancel
            </Button>
            <Button 
              onClick={handleSave} 
              disabled={saving}
              className="bg-primary text-primary-foreground"
              data-testid="save-hs-btn"
            >
              {saving ? <Loader2 className="h-4 w-4 animate-spin" /> : isNew ? 'Add Code' : 'Save Changes'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
