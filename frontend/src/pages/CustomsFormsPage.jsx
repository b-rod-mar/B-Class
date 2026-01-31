import { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Badge } from '../components/ui/badge';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../components/ui/select';
import { ScrollArea } from '../components/ui/scroll-area';
import { 
  Search, 
  FileText, 
  Filter,
  Download,
  ExternalLink,
  Clipboard,
  Check
} from 'lucide-react';
import { toast } from 'sonner';
import { cn } from '../lib/utils';

const CATEGORY_COLORS = {
  'Import': 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30',
  'Export': 'bg-blue-500/10 text-blue-400 border-blue-500/30',
  'Transit': 'bg-violet-500/10 text-violet-400 border-violet-500/30',
  'Warehousing': 'bg-amber-500/10 text-amber-400 border-amber-500/30',
  'Special': 'bg-cyan-500/10 text-cyan-400 border-cyan-500/30',
  'Exemptions': 'bg-rose-500/10 text-rose-400 border-rose-500/30',
  'Permits': 'bg-orange-500/10 text-orange-400 border-orange-500/30',
  'Payment': 'bg-teal-500/10 text-teal-400 border-teal-500/30',
  'Appeals': 'bg-indigo-500/10 text-indigo-400 border-indigo-500/30',
  'Certificates': 'bg-pink-500/10 text-pink-400 border-pink-500/30',
};

export default function CustomsFormsPage() {
  const { api } = useAuth();
  const [forms, setForms] = useState([]);
  const [categories, setCategories] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('');
  const [loading, setLoading] = useState(true);
  const [copiedId, setCopiedId] = useState(null);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [formsRes, catsRes] = await Promise.all([
        api.get('/customs-forms'),
        api.get('/customs-forms/categories')
      ]);
      setForms(formsRes.data);
      setCategories(catsRes.data.categories || []);
    } catch (error) {
      toast.error('Failed to load customs forms');
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (searchQuery) params.append('search', searchQuery);
      if (selectedCategory) params.append('category', selectedCategory);
      
      const response = await api.get(`/customs-forms?${params.toString()}`);
      setForms(response.data);
    } catch (error) {
      toast.error('Search failed');
    } finally {
      setLoading(false);
    }
  };

  const copyFormNumber = (formNumber) => {
    navigator.clipboard.writeText(formNumber);
    setCopiedId(formNumber);
    toast.success(`Copied ${formNumber}`);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const clearFilters = () => {
    setSearchQuery('');
    setSelectedCategory('');
    fetchData();
  };

  // Group forms by category
  const groupedForms = forms.reduce((acc, form) => {
    if (!acc[form.category]) {
      acc[form.category] = [];
    }
    acc[form.category].push(form);
    return acc;
  }, {});

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="text-muted-foreground animate-pulse">Loading customs forms...</div>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in" data-testid="customs-forms-page">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold font-['Chivo'] tracking-tight flex items-center gap-3">
          <FileText className="h-8 w-8 text-primary" />
          Bahamas Customs Forms
        </h1>
        <p className="text-muted-foreground mt-1">
          Complete reference for all customs forms and documents
        </p>
      </div>

      {/* Search */}
      <Card>
        <CardContent className="p-6">
          <div className="flex flex-col md:flex-row gap-4">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search by form number or name..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                className="pl-10"
                data-testid="forms-search-input"
              />
            </div>
            <div className="w-full md:w-48">
              <Select value={selectedCategory || "all"} onValueChange={(val) => setSelectedCategory(val === "all" ? "" : val)}>
                <SelectTrigger>
                  <Filter className="h-4 w-4 mr-2" />
                  <SelectValue placeholder="All Categories" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Categories</SelectItem>
                  {categories.map((cat) => (
                    <SelectItem key={cat} value={cat}>{cat}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <Button onClick={handleSearch} className="bg-primary text-primary-foreground">
              <Search className="h-4 w-4 mr-2" />
              Search
            </Button>
            {(searchQuery || selectedCategory) && (
              <Button variant="outline" onClick={clearFilters}>Clear</Button>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Results */}
      <div className="space-y-6">
        <p className="text-sm text-muted-foreground">
          Showing <span className="font-semibold text-foreground">{forms.length}</span> forms
        </p>

        {Object.entries(groupedForms).map(([category, categoryForms]) => (
          <Card key={category}>
            <CardHeader className="pb-3 bg-muted/30">
              <div className="flex items-center gap-3">
                <Badge className={cn("px-3 py-1", CATEGORY_COLORS[category] || 'bg-primary/10 text-primary')}>
                  {category}
                </Badge>
                <span className="text-sm text-muted-foreground">{categoryForms.length} forms</span>
              </div>
            </CardHeader>
            <CardContent className="p-0">
              <div className="divide-y divide-border">
                {categoryForms.map((form) => (
                  <div key={form.id} className="p-4 hover:bg-muted/30 transition-colors" data-testid={`form-${form.form_number}`}>
                    <div className="flex items-start gap-4">
                      <div className="flex-shrink-0">
                        <Button
                          variant="outline"
                          size="sm"
                          className="font-mono font-bold text-primary hover:bg-primary/10 min-w-[70px]"
                          onClick={() => copyFormNumber(form.form_number)}
                        >
                          {copiedId === form.form_number ? (
                            <Check className="h-4 w-4" />
                          ) : (
                            form.form_number
                          )}
                        </Button>
                      </div>
                      <div className="flex-1 min-w-0">
                        <h4 className="font-semibold">{form.form_name}</h4>
                        <p className="text-sm text-muted-foreground mt-1">{form.description}</p>
                        <div className="mt-2 text-xs space-y-1">
                          <p><span className="text-muted-foreground">Usage:</span> {form.usage}</p>
                          <p><span className="text-muted-foreground">Obtain:</span> {form.where_to_obtain}</p>
                          {form.related_section && (
                            <p><span className="text-muted-foreground">CMA Reference:</span> {form.related_section}</p>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
