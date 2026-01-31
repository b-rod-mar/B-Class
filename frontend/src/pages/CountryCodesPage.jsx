import { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
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
  Globe, 
  Filter,
  Clipboard,
  Check,
  MapPin
} from 'lucide-react';
import { toast } from 'sonner';
import { cn } from '../lib/utils';

const REGION_COLORS = {
  'Caribbean': 'bg-cyan-500/10 text-cyan-400 border-cyan-500/30',
  'North America': 'bg-blue-500/10 text-blue-400 border-blue-500/30',
  'Central America': 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30',
  'South America': 'bg-amber-500/10 text-amber-400 border-amber-500/30',
  'Europe': 'bg-violet-500/10 text-violet-400 border-violet-500/30',
  'Asia': 'bg-rose-500/10 text-rose-400 border-rose-500/30',
  'Middle East': 'bg-orange-500/10 text-orange-400 border-orange-500/30',
  'Africa': 'bg-teal-500/10 text-teal-400 border-teal-500/30',
  'Oceania': 'bg-indigo-500/10 text-indigo-400 border-indigo-500/30',
};

export default function CountryCodesPage() {
  const { api } = useAuth();
  const [countries, setCountries] = useState([]);
  const [regions, setRegions] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedRegion, setSelectedRegion] = useState('');
  const [loading, setLoading] = useState(true);
  const [copiedCode, setCopiedCode] = useState(null);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [countriesRes, regionsRes] = await Promise.all([
        api.get('/country-codes'),
        api.get('/country-codes/regions')
      ]);
      setCountries(countriesRes.data);
      setRegions(regionsRes.data.regions || []);
    } catch (error) {
      toast.error('Failed to load country codes');
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (searchQuery) params.append('search', searchQuery);
      if (selectedRegion) params.append('region', selectedRegion);
      
      const response = await api.get(`/country-codes?${params.toString()}`);
      setCountries(response.data);
    } catch (error) {
      toast.error('Search failed');
    } finally {
      setLoading(false);
    }
  };

  const copyCode = (code) => {
    navigator.clipboard.writeText(code);
    setCopiedCode(code);
    toast.success(`Copied ${code}`);
    setTimeout(() => setCopiedCode(null), 2000);
  };

  const clearFilters = () => {
    setSearchQuery('');
    setSelectedRegion('');
    fetchData();
  };

  // Group by region
  const groupedCountries = countries.reduce((acc, country) => {
    if (!acc[country.region]) {
      acc[country.region] = [];
    }
    acc[country.region].push(country);
    return acc;
  }, {});

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="text-muted-foreground animate-pulse">Loading country codes...</div>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in" data-testid="country-codes-page">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold font-['Chivo'] tracking-tight flex items-center gap-3">
          <Globe className="h-8 w-8 text-primary" />
          Country Codes
        </h1>
        <p className="text-muted-foreground mt-1">
          ISO country codes for customs declarations and certificates of origin
        </p>
      </div>

      {/* Search */}
      <Card>
        <CardContent className="p-6">
          <div className="flex flex-col md:flex-row gap-4">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search by country name or code..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                className="pl-10"
                data-testid="country-search-input"
              />
            </div>
            <div className="w-full md:w-48">
              <Select value={selectedRegion || "all"} onValueChange={(val) => setSelectedRegion(val === "all" ? "" : val)}>
                <SelectTrigger>
                  <MapPin className="h-4 w-4 mr-2" />
                  <SelectValue placeholder="All Regions" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Regions</SelectItem>
                  {regions.map((region) => (
                    <SelectItem key={region} value={region}>{region}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <Button onClick={handleSearch} className="bg-primary text-primary-foreground">
              <Search className="h-4 w-4 mr-2" />
              Search
            </Button>
            {(searchQuery || selectedRegion) && (
              <Button variant="outline" onClick={clearFilters}>Clear</Button>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Results */}
      <div className="space-y-6">
        <p className="text-sm text-muted-foreground">
          Showing <span className="font-semibold text-foreground">{countries.length}</span> countries
        </p>

        {Object.entries(groupedCountries).map(([region, regionCountries]) => (
          <Card key={region}>
            <CardHeader className="pb-3 bg-muted/30">
              <div className="flex items-center gap-3">
                <Badge className={cn("px-3 py-1", REGION_COLORS[region] || 'bg-primary/10 text-primary')}>
                  {region}
                </Badge>
                <span className="text-sm text-muted-foreground">{regionCountries.length} countries</span>
              </div>
            </CardHeader>
            <CardContent className="p-0">
              <ScrollArea className="max-h-[400px]">
                <table className="w-full">
                  <thead className="sticky top-0 bg-card border-b border-border">
                    <tr className="text-xs text-muted-foreground uppercase tracking-wider">
                      <th className="text-left py-3 px-4 w-24">Code</th>
                      <th className="text-left py-3 px-4 w-24">Alpha-3</th>
                      <th className="text-left py-3 px-4">Country</th>
                      <th className="text-left py-3 px-4">Trade Agreement</th>
                      <th className="text-left py-3 px-4">Notes</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border/50">
                    {regionCountries.map((country) => (
                      <tr key={country.id} className="hover:bg-muted/30" data-testid={`country-${country.code}`}>
                        <td className="py-3 px-4">
                          <Button
                            variant="ghost"
                            size="sm"
                            className="font-mono font-bold text-primary hover:bg-primary/10 h-8 px-2"
                            onClick={() => copyCode(country.code)}
                          >
                            {copiedCode === country.code ? (
                              <Check className="h-4 w-4" />
                            ) : (
                              country.code
                            )}
                          </Button>
                        </td>
                        <td className="py-3 px-4 font-mono text-sm text-muted-foreground">
                          {country.alpha3}
                        </td>
                        <td className="py-3 px-4 font-medium">{country.name}</td>
                        <td className="py-3 px-4">
                          {country.trade_agreement ? (
                            <Badge className="bg-emerald-500/10 text-emerald-400 border-emerald-500/30">
                              {country.trade_agreement}
                            </Badge>
                          ) : (
                            <span className="text-xs text-muted-foreground">-</span>
                          )}
                        </td>
                        <td className="py-3 px-4 text-xs text-muted-foreground max-w-[200px] truncate" title={country.notes}>
                          {country.notes}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </ScrollArea>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Info Card */}
      <Card className="bg-card/50 border-dashed">
        <CardContent className="p-6">
          <h4 className="font-medium mb-2">CARICOM Trade Agreement</h4>
          <p className="text-sm text-muted-foreground">
            Countries marked with CARICOM may qualify for duty-free or reduced duty treatment. 
            A valid CARICOM Certificate of Origin (Form C505) is required for preferential rates.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
