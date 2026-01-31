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
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from '../components/ui/accordion';
import { 
  Search, 
  BookOpen, 
  Scale,
  FileText,
  AlertTriangle,
  Shield,
  DollarSign,
  Plane,
  Gavel,
  HelpCircle,
  Filter,
  X,
  ChevronRight
} from 'lucide-react';
import { toast } from 'sonner';
import { cn } from '../lib/utils';

const CATEGORY_ICONS = {
  'Preliminary Provisions': BookOpen,
  'Administration': Shield,
  'Importation': Plane,
  'Duties and Rates': DollarSign,
  'Exemptions and Reliefs': FileText,
  'Procedures': FileText,
  'Enforcement': Gavel,
  'Appeals': Scale,
  'Special Provisions': AlertTriangle,
  'Trade Agreements': HelpCircle
};

const CATEGORY_COLORS = {
  'Preliminary Provisions': 'bg-slate-500/10 text-slate-400 border-slate-500/30',
  'Administration': 'bg-blue-500/10 text-blue-400 border-blue-500/30',
  'Importation': 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30',
  'Duties and Rates': 'bg-amber-500/10 text-amber-400 border-amber-500/30',
  'Exemptions and Reliefs': 'bg-violet-500/10 text-violet-400 border-violet-500/30',
  'Procedures': 'bg-cyan-500/10 text-cyan-400 border-cyan-500/30',
  'Enforcement': 'bg-rose-500/10 text-rose-400 border-rose-500/30',
  'Appeals': 'bg-indigo-500/10 text-indigo-400 border-indigo-500/30',
  'Special Provisions': 'bg-orange-500/10 text-orange-400 border-orange-500/30',
  'Trade Agreements': 'bg-teal-500/10 text-teal-400 border-teal-500/30'
};

export default function CMASearchPage() {
  const { api } = useAuth();
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('');
  const [categories, setCategories] = useState([]);
  const [regulations, setRegulations] = useState([]);
  const [loading, setLoading] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);

  useEffect(() => {
    fetchCategories();
    // Load all regulations on initial load
    searchRegulations('', '');
  }, []);

  const fetchCategories = async () => {
    try {
      const response = await api.get('/cma/categories');
      setCategories(response.data.categories || []);
    } catch (error) {
      console.error('Failed to load categories');
    }
  };

  const searchRegulations = async (query, category) => {
    setLoading(true);
    setHasSearched(true);
    try {
      const params = new URLSearchParams();
      if (query) params.append('q', query);
      if (category) params.append('category', category);
      
      const response = await api.get(`/cma/search?${params.toString()}`);
      setRegulations(response.data);
    } catch (error) {
      toast.error('Failed to search regulations');
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = () => {
    searchRegulations(searchQuery, selectedCategory);
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      handleSearch();
    }
  };

  const clearFilters = () => {
    setSearchQuery('');
    setSelectedCategory('');
    searchRegulations('', '');
  };

  const getCategoryIcon = (category) => {
    const Icon = CATEGORY_ICONS[category] || FileText;
    return Icon;
  };

  const highlightText = (text, query) => {
    if (!query) return text;
    const parts = text.split(new RegExp(`(${query})`, 'gi'));
    return parts.map((part, i) => 
      part.toLowerCase() === query.toLowerCase() 
        ? <mark key={i} className="bg-primary/30 text-foreground px-0.5 rounded">{part}</mark>
        : part
    );
  };

  // Group regulations by category
  const groupedRegulations = regulations.reduce((acc, reg) => {
    if (!acc[reg.category]) {
      acc[reg.category] = [];
    }
    acc[reg.category].push(reg);
    return acc;
  }, {});

  return (
    <div className="space-y-6 animate-fade-in" data-testid="cma-search-page">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold font-['Chivo'] tracking-tight flex items-center gap-3">
          <Scale className="h-8 w-8 text-primary" />
          CMA Reference Guide
        </h1>
        <p className="text-muted-foreground mt-1">
          Search the Bahamas Customs Management Act and Regulations
        </p>
      </div>

      {/* Search Section */}
      <Card className="card-hover">
        <CardContent className="p-6">
          <div className="flex flex-col md:flex-row gap-4">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search regulations (e.g., duty rates, exemptions, Electronic Single Window)..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyPress={handleKeyPress}
                className="pl-10"
                data-testid="cma-search-input"
              />
            </div>
            <div className="w-full md:w-64">
              <Select value={selectedCategory || "all"} onValueChange={(val) => setSelectedCategory(val === "all" ? "" : val)}>
                <SelectTrigger data-testid="cma-category-select">
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
            <Button 
              onClick={handleSearch}
              className="bg-primary text-primary-foreground hover:bg-primary/90"
              data-testid="cma-search-btn"
            >
              <Search className="h-4 w-4 mr-2" />
              Search
            </Button>
            {(searchQuery || selectedCategory) && (
              <Button variant="outline" onClick={clearFilters} data-testid="clear-filters-btn">
                <X className="h-4 w-4 mr-2" />
                Clear
              </Button>
            )}
          </div>

          {/* Quick Search Tags */}
          <div className="flex flex-wrap gap-2 mt-4">
            <span className="text-xs text-muted-foreground">Quick searches:</span>
            {['duty rates', 'exemptions', 'VAT', 'alcohol', 'vehicles', 'penalties', 'CARICOM', 'Electronic Single Window'].map((term) => (
              <Button
                key={term}
                variant="outline"
                size="sm"
                className="h-7 text-xs"
                onClick={() => {
                  setSearchQuery(term);
                  searchRegulations(term, selectedCategory);
                }}
              >
                {term}
              </Button>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Results */}
      {loading ? (
        <Card>
          <CardContent className="flex items-center justify-center py-16">
            <div className="text-muted-foreground animate-pulse">Searching regulations...</div>
          </CardContent>
        </Card>
      ) : regulations.length === 0 && hasSearched ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-16 text-center">
            <BookOpen className="h-12 w-12 text-muted-foreground opacity-50 mb-4" />
            <p className="text-muted-foreground mb-2">No regulations found</p>
            <p className="text-sm text-muted-foreground/70">
              Try different search terms or clear filters
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-6">
          {/* Results Summary */}
          <div className="flex items-center justify-between">
            <p className="text-sm text-muted-foreground">
              Found <span className="font-semibold text-foreground">{regulations.length}</span> regulations
              {searchQuery && <> matching &quot;<span className="text-primary">{searchQuery}</span>&quot;</>}
            </p>
          </div>

          {/* Grouped Results */}
          {Object.entries(groupedRegulations).map(([category, regs]) => {
            const CategoryIcon = getCategoryIcon(category);
            return (
              <Card key={category} className="overflow-hidden">
                <CardHeader className="pb-2 bg-muted/30">
                  <div className="flex items-center gap-3">
                    <div className={cn(
                      "w-10 h-10 rounded-lg flex items-center justify-center",
                      CATEGORY_COLORS[category]?.split(' ')[0] || 'bg-primary/10'
                    )}>
                      <CategoryIcon className="h-5 w-5" />
                    </div>
                    <div>
                      <CardTitle className="text-lg font-['Chivo']">{category}</CardTitle>
                      <CardDescription>{regs.length} regulation{regs.length > 1 ? 's' : ''}</CardDescription>
                    </div>
                  </div>
                </CardHeader>
                <CardContent className="p-0">
                  <Accordion type="single" collapsible className="w-full">
                    {regs.map((reg, idx) => (
                      <AccordionItem key={reg.id} value={reg.id} className="border-b-0">
                        <AccordionTrigger className="px-6 py-4 hover:bg-muted/30 hover:no-underline">
                          <div className="flex items-start gap-4 text-left">
                            <div className="flex-1">
                              <div className="flex items-center gap-2 mb-1">
                                <Badge variant="outline" className="text-xs font-mono">
                                  {reg.reference}
                                </Badge>
                                <span className="text-xs text-muted-foreground">{reg.section}</span>
                              </div>
                              <h4 className="font-medium">
                                {searchQuery ? highlightText(reg.title, searchQuery) : reg.title}
                              </h4>
                            </div>
                          </div>
                        </AccordionTrigger>
                        <AccordionContent className="px-6 pb-4">
                          <div className="bg-muted/30 rounded-lg p-4 space-y-4">
                            <p className="text-sm leading-relaxed">
                              {searchQuery ? highlightText(reg.content, searchQuery) : reg.content}
                            </p>
                            <div className="flex flex-wrap gap-2 pt-2 border-t border-border/50">
                              <span className="text-xs text-muted-foreground">Keywords:</span>
                              {reg.keywords.map((keyword, i) => (
                                <Badge 
                                  key={i} 
                                  variant="outline" 
                                  className="text-xs cursor-pointer hover:bg-primary/10"
                                  onClick={() => {
                                    setSearchQuery(keyword);
                                    searchRegulations(keyword, '');
                                  }}
                                >
                                  {keyword}
                                </Badge>
                              ))}
                            </div>
                          </div>
                        </AccordionContent>
                      </AccordionItem>
                    ))}
                  </Accordion>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}

      {/* Help Card */}
      <Card className="bg-card/50 border-dashed">
        <CardContent className="p-6">
          <div className="flex items-start gap-4">
            <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center flex-shrink-0">
              <HelpCircle className="h-5 w-5 text-primary" />
            </div>
            <div>
              <h4 className="font-medium mb-1">Need More Information?</h4>
              <p className="text-sm text-muted-foreground">
                For official rulings and specific guidance, contact the Bahamas Customs Department at{' '}
                <span className="text-primary">customs@bahamas.gov.bs</span> or visit{' '}
                <a href="https://www.bahamascustoms.gov.bs" target="_blank" rel="noopener noreferrer" className="text-primary hover:underline">
                  www.bahamascustoms.gov.bs
                </a>
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
