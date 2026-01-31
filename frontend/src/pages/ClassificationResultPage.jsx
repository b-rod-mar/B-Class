import { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Input } from '../components/ui/input';
import { Textarea } from '../components/ui/textarea';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '../components/ui/dialog';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '../components/ui/dropdown-menu';
import { ScrollArea } from '../components/ui/scroll-area';
import { 
  ArrowLeft, 
  Download, 
  FileSpreadsheet, 
  FileText, 
  CheckCircle, 
  AlertCircle,
  AlertTriangle,
  Edit2,
  ChevronDown,
  Shield,
  Info,
  Loader2,
  BookOpen,
  Trash2,
  X
} from 'lucide-react';
import { toast } from 'sonner';
import { cn, formatDate, getConfidenceColor, getConfidenceLabel, getStatusColor, getStatusLabel, formatCurrency } from '../lib/utils';
import HSCodeAutoSuggest from '../components/HSCodeAutoSuggest';

export default function ClassificationResultPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { api } = useAuth();
  const [classification, setClassification] = useState(null);
  const [loading, setLoading] = useState(true);
  const [editingItem, setEditingItem] = useState(null);
  const [editIndex, setEditIndex] = useState(null);
  const [saving, setSaving] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [deletingItem, setDeletingItem] = useState(null);

  useEffect(() => {
    fetchClassification();
  }, [id]);

  const fetchClassification = async () => {
    try {
      const response = await api.get(`/classifications/${id}`);
      setClassification(response.data);
    } catch (error) {
      toast.error('Failed to load classification');
    } finally {
      setLoading(false);
    }
  };

  const handleExport = async (format) => {
    try {
      const response = await api.get(`/classifications/${id}/export?format=${format}`, {
        responseType: 'blob'
      });
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `classification_${id}.${format}`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      
      toast.success(`Exported as ${format.toUpperCase()}`);
    } catch (error) {
      toast.error('Export failed');
    }
  };

  const handleEditItem = (item, index) => {
    setEditingItem({ ...item });
    setEditIndex(index);
  };

  const handleSaveItem = async () => {
    if (editIndex === null || !editingItem) return;
    
    setSaving(true);
    try {
      await api.put(`/classifications/${id}/items/${editIndex}`, editingItem);
      await fetchClassification();
      toast.success('Item updated successfully');
      setEditingItem(null);
      setEditIndex(null);
    } catch (error) {
      toast.error('Failed to update item');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="text-muted-foreground animate-pulse">Loading classification...</div>
      </div>
    );
  }

  if (!classification) {
    return (
      <div className="text-center py-12">
        <p className="text-muted-foreground">Classification not found</p>
        <Link to="/history">
          <Button variant="outline" className="mt-4">Back to History</Button>
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in" data-testid="classification-result-page">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div className="flex items-center gap-4">
          <Link to="/history">
            <Button variant="ghost" size="icon">
              <ArrowLeft className="h-5 w-5" />
            </Button>
          </Link>
          <div>
            <h1 className="text-2xl font-bold font-['Chivo'] tracking-tight">
              {classification.document_name}
            </h1>
            <p className="text-sm text-muted-foreground">
              Classified on {formatDate(classification.created_at)}
            </p>
          </div>
        </div>
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button className="bg-primary text-primary-foreground hover:bg-primary/90" data-testid="export-btn">
              <Download className="h-4 w-4 mr-2" />
              Export
              <ChevronDown className="h-4 w-4 ml-2" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem onClick={() => handleExport('csv')} data-testid="export-csv">
              <FileText className="h-4 w-4 mr-2" />
              Export as CSV
            </DropdownMenuItem>
            <DropdownMenuItem onClick={() => handleExport('xlsx')} data-testid="export-xlsx">
              <FileSpreadsheet className="h-4 w-4 mr-2" />
              Export as Excel
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card className="bg-card/50">
          <CardContent className="p-4 text-center">
            <p className="text-3xl font-bold font-['Chivo'] text-foreground">{classification.total_items}</p>
            <p className="text-xs text-muted-foreground uppercase tracking-wider">Total Items</p>
          </CardContent>
        </Card>
        <Card className="bg-emerald-500/10 border-emerald-500/20">
          <CardContent className="p-4 text-center">
            <p className="text-3xl font-bold font-['Chivo'] text-emerald-400">{classification.auto_approved_count}</p>
            <p className="text-xs text-emerald-400/70 uppercase tracking-wider">Auto Approved</p>
          </CardContent>
        </Card>
        <Card className="bg-amber-500/10 border-amber-500/20">
          <CardContent className="p-4 text-center">
            <p className="text-3xl font-bold font-['Chivo'] text-amber-400">{classification.needs_review_count}</p>
            <p className="text-xs text-amber-400/70 uppercase tracking-wider">Needs Review</p>
          </CardContent>
        </Card>
        <Card className="bg-primary/10 border-primary/20">
          <CardContent className="p-4 text-center">
            <p className="text-3xl font-bold font-['Chivo'] text-primary">
              {classification.items.length > 0 
                ? Math.round(classification.items.reduce((acc, item) => acc + (item.confidence_score || 0), 0) / classification.items.length)
                : 0}%
            </p>
            <p className="text-xs text-primary/70 uppercase tracking-wider">Avg Confidence</p>
          </CardContent>
        </Card>
      </div>

      {/* Classification Table */}
      <Card>
        <CardHeader>
          <CardTitle className="font-['Chivo']">Classification Results</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          <ScrollArea className="h-[500px]">
            <div className="overflow-x-auto">
              <table className="data-table">
                <thead>
                  <tr>
                    <th className="w-8">#</th>
                    <th>Description</th>
                    <th>HS Code</th>
                    <th>Confidence</th>
                    <th>GRI Rules</th>
                    <th>Status</th>
                    <th>Flags</th>
                    <th className="w-12"></th>
                  </tr>
                </thead>
                <tbody>
                  {classification.items.map((item, index) => (
                    <tr key={index} data-testid={`item-row-${index}`}>
                      <td className="text-muted-foreground font-mono text-xs">{index + 1}</td>
                      <td>
                        <div className="max-w-xs">
                          <p className="font-medium truncate" title={item.clean_description}>
                            {item.clean_description || item.original_description}
                          </p>
                          {item.quantity && (
                            <p className="text-xs text-muted-foreground">
                              Qty: {item.quantity} {item.unit || ''} 
                              {item.total_value && ` • ${formatCurrency(item.total_value)}`}
                            </p>
                          )}
                        </div>
                      </td>
                      <td>
                        <code className="hs-code bg-primary/10 px-2 py-1 rounded text-sm">
                          {item.hs_code || '-'}
                        </code>
                        {item.hs_description && (
                          <p className="text-xs text-muted-foreground mt-1 max-w-[200px] truncate" title={item.hs_description}>
                            {item.hs_description}
                          </p>
                        )}
                      </td>
                      <td>
                        <Badge className={cn("font-mono", getConfidenceColor(item.confidence_score))}>
                          {item.confidence_score}%
                        </Badge>
                      </td>
                      <td>
                        <div className="flex flex-wrap gap-1">
                          {item.gri_rules_applied?.map((rule, i) => (
                            <Badge key={i} variant="outline" className="text-xs">
                              {rule}
                            </Badge>
                          ))}
                        </div>
                      </td>
                      <td>
                        <Badge className={cn("text-xs", getStatusColor(item.review_status))}>
                          {getStatusLabel(item.review_status)}
                        </Badge>
                      </td>
                      <td>
                        <div className="flex gap-1">
                          {item.is_restricted && (
                            <Badge variant="outline" className="bg-rose-500/10 text-rose-400 border-rose-500/30 text-xs">
                              <Shield className="h-3 w-3 mr-1" />
                              Restricted
                            </Badge>
                          )}
                          {item.requires_permit && (
                            <Badge variant="outline" className="bg-amber-500/10 text-amber-400 border-amber-500/30 text-xs">
                              <AlertTriangle className="h-3 w-3 mr-1" />
                              Permit
                            </Badge>
                          )}
                        </div>
                      </td>
                      <td>
                        <Button 
                          variant="ghost" 
                          size="icon" 
                          onClick={() => handleEditItem(item, index)}
                          data-testid={`edit-item-${index}`}
                        >
                          <Edit2 className="h-4 w-4" />
                        </Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </ScrollArea>
        </CardContent>
      </Card>

      {/* Edit Dialog */}
      <Dialog open={editingItem !== null} onOpenChange={() => { setEditingItem(null); setEditIndex(null); }}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle className="font-['Chivo']">Edit Classification Item</DialogTitle>
          </DialogHeader>
          {editingItem && (
            <div className="space-y-4 py-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <label className="text-sm font-medium flex items-center gap-2">
                    HS Code
                    <Link to="/hs-library" target="_blank" className="text-primary hover:underline">
                      <BookOpen className="h-3.5 w-3.5" />
                    </Link>
                  </label>
                  <HSCodeAutoSuggest
                    value={editingItem.hs_code || ''}
                    onChange={(value) => setEditingItem({ ...editingItem, hs_code: value })}
                    onSelect={(suggestion) => {
                      setEditingItem({ 
                        ...editingItem, 
                        hs_code: suggestion.code,
                        hs_description: suggestion.description,
                        is_restricted: suggestion.is_restricted,
                        requires_permit: suggestion.requires_permit
                      });
                      toast.success(`Selected: ${suggestion.code}`);
                    }}
                    placeholder="Search or type HS code..."
                  />
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium">Review Status</label>
                  <select
                    className="w-full h-10 px-3 bg-background border border-input rounded-md text-sm"
                    value={editingItem.review_status}
                    onChange={(e) => setEditingItem({ ...editingItem, review_status: e.target.value })}
                    data-testid="edit-status"
                  >
                    <option value="auto_approved">Auto Approved</option>
                    <option value="needs_review">Needs Review</option>
                    <option value="reviewed">Reviewed</option>
                    <option value="rejected">Rejected</option>
                  </select>
                </div>
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">HS Description</label>
                <Input
                  value={editingItem.hs_description || ''}
                  onChange={(e) => setEditingItem({ ...editingItem, hs_description: e.target.value })}
                  placeholder="Official HS nomenclature description"
                  data-testid="edit-hs-description"
                />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">Classification Reasoning</label>
                <Textarea
                  value={editingItem.reasoning || ''}
                  onChange={(e) => setEditingItem({ ...editingItem, reasoning: e.target.value })}
                  placeholder="Explain the classification logic..."
                  rows={3}
                  data-testid="edit-reasoning"
                />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">CMA / Regulatory Notes</label>
                <Textarea
                  value={editingItem.cma_notes || ''}
                  onChange={(e) => setEditingItem({ ...editingItem, cma_notes: e.target.value })}
                  placeholder="Compliance notes, permit requirements, restrictions..."
                  rows={2}
                  data-testid="edit-cma-notes"
                />
              </div>
              <div className="flex gap-4">
                <label className="flex items-center gap-2 text-sm">
                  <input
                    type="checkbox"
                    checked={editingItem.is_restricted || false}
                    onChange={(e) => setEditingItem({ ...editingItem, is_restricted: e.target.checked })}
                    className="rounded border-input"
                  />
                  Restricted Item
                </label>
                <label className="flex items-center gap-2 text-sm">
                  <input
                    type="checkbox"
                    checked={editingItem.requires_permit || false}
                    onChange={(e) => setEditingItem({ ...editingItem, requires_permit: e.target.checked })}
                    className="rounded border-input"
                  />
                  Requires Permit
                </label>
              </div>
            </div>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => { setEditingItem(null); setEditIndex(null); }}>
              Cancel
            </Button>
            <Button 
              onClick={handleSaveItem} 
              disabled={saving}
              className="bg-primary text-primary-foreground"
              data-testid="save-edit-btn"
            >
              {saving ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Save Changes'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
