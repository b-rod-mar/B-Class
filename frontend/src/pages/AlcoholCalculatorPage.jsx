import { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Badge } from '../components/ui/badge';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../components/ui/select';
import { Switch } from '../components/ui/switch';
import { Separator } from '../components/ui/separator';
import { ScrollArea } from '../components/ui/scroll-area';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { 
  Wine, 
  Beer, 
  Calculator, 
  AlertTriangle,
  Download,
  History,
  DollarSign,
  Percent,
  Package,
  Globe,
  FileText,
  Shield,
  Loader2,
  Info,
  ChevronRight,
  Sparkles,
  Upload,
  FileSpreadsheet,
  CheckCircle,
  X
} from 'lucide-react';
import { toast } from 'sonner';
import { cn, formatCurrency, formatDate } from '../lib/utils';

const ALCOHOL_TYPES = [
  { value: 'wine', label: 'Wine', icon: Wine },
  { value: 'beer', label: 'Beer', icon: Beer },
  { value: 'spirits', label: 'Spirits (Rum, Vodka, Whiskey)', icon: Wine },
  { value: 'liqueur', label: 'Liqueur & Cordials', icon: Wine },
  { value: 'other', label: 'Other Alcohol', icon: Wine }
];

const VOLUME_PRESETS = [
  { ml: 330, label: '330ml (Beer)' },
  { ml: 500, label: '500ml' },
  { ml: 750, label: '750ml (Standard)' },
  { ml: 1000, label: '1L' },
  { ml: 1500, label: '1.5L (Magnum)' },
  { ml: 1750, label: '1.75L (Handle)' }
];

const initialFormState = {
  product_name: '',
  alcohol_type: '',
  volume_ml: 750,
  alcohol_percentage: 12,
  quantity: 1,
  cif_value: 0,
  country_of_origin: '',
  brand_label: '',
  has_liquor_license: false
};

export default function AlcoholCalculatorPage() {
  const { api } = useAuth();
  const [formData, setFormData] = useState(initialFormState);
  const [calculating, setCalculating] = useState(false);
  const [result, setResult] = useState(null);
  const [history, setHistory] = useState([]);
  const [showHistory, setShowHistory] = useState(false);
  const [rates, setRates] = useState(null);
  
  // Bulk upload state
  const [uploadFile, setUploadFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [batchResult, setBatchResult] = useState(null);
  const [isDragging, setIsDragging] = useState(false);

  useEffect(() => {
    fetchHistory();
    fetchRates();
  }, []);

  const fetchHistory = async () => {
    try {
      const response = await api.get('/alcohol/calculations');
      setHistory(response.data);
    } catch (error) {
      console.error('Failed to load history');
    }
  };

  const fetchRates = async () => {
    try {
      const response = await api.get('/alcohol/rates');
      setRates(response.data);
    } catch (error) {
      console.error('Failed to load rates');
    }
  };

  const handleCalculate = async () => {
    if (!formData.product_name || !formData.alcohol_type || !formData.cif_value) {
      toast.error('Please fill in product name, type, and CIF value');
      return;
    }

    setCalculating(true);
    try {
      const response = await api.post('/alcohol/calculate', formData);
      setResult(response.data);
      toast.success('Calculation complete!');
      fetchHistory();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Calculation failed');
    } finally {
      setCalculating(false);
    }
  };

  const handleExport = async (calcId) => {
    try {
      const response = await api.get(`/alcohol/calculations/${calcId}/export`);
      const data = response.data;
      
      // Create printable HTML
      const printWindow = window.open('', '_blank');
      printWindow.document.write(`
        <!DOCTYPE html>
        <html>
        <head>
          <title>${data.title}</title>
          <style>
            body { font-family: Arial, sans-serif; padding: 40px; max-width: 800px; margin: 0 auto; }
            h1 { color: #0f172a; border-bottom: 2px solid #2dd4bf; padding-bottom: 10px; }
            .header { display: flex; justify-content: space-between; margin-bottom: 20px; }
            .section { margin: 20px 0; }
            .section h3 { color: #1e293b; margin-bottom: 10px; }
            table { width: 100%; border-collapse: collapse; }
            td { padding: 8px; border-bottom: 1px solid #e2e8f0; }
            td:first-child { font-weight: 500; width: 50%; }
            .total { background: #f1f5f9; font-weight: bold; font-size: 1.1em; }
            .warning { background: #fef3c7; padding: 10px; border-radius: 4px; margin: 10px 0; }
            .disclaimer { color: #64748b; font-size: 0.85em; margin-top: 30px; padding-top: 20px; border-top: 1px solid #e2e8f0; }
            @media print { body { padding: 20px; } }
          </style>
        </head>
        <body>
          <h1>${data.title}</h1>
          <div class="header">
            <div><strong>Reference:</strong> ${data.reference_number}</div>
            <div><strong>Date:</strong> ${data.date}</div>
          </div>
          
          <div class="section">
            <h3>Product Details</h3>
            <table>
              ${Object.entries(data.product_details).map(([key, value]) => `
                <tr><td>${key}</td><td>${value}</td></tr>
              `).join('')}
            </table>
          </div>
          
          <div class="section">
            <h3>Duty & Tax Breakdown</h3>
            <table>
              ${Object.entries(data.duty_breakdown).map(([key, value]) => `
                <tr class="${key === 'TOTAL LANDED COST' ? 'total' : ''}">
                  <td>${key}</td><td>${value}</td>
                </tr>
              `).join('')}
            </table>
          </div>
          
          ${data.warnings.length > 0 ? `
            <div class="section">
              <h3>Warnings & Notes</h3>
              ${data.warnings.map(w => `<div class="warning">⚠️ ${w}</div>`).join('')}
            </div>
          ` : ''}
          
          <div class="disclaimer">${data.disclaimer}</div>
        </body>
        </html>
      `);
      printWindow.document.close();
      printWindow.print();
      
      toast.success('Export ready for printing');
    } catch (error) {
      toast.error('Export failed');
    }
  };

  const resetForm = () => {
    setFormData(initialFormState);
    setResult(null);
  };

  const loadFromHistory = (calc) => {
    setResult(calc);
    setShowHistory(false);
  };

  // Bulk upload handlers
  const handleDrag = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setIsDragging(true);
    } else if (e.type === 'dragleave') {
      setIsDragging(false);
    }
  }, []);

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
    const droppedFile = e.dataTransfer?.files?.[0];
    if (droppedFile) {
      const ext = droppedFile.name.split('.').pop().toLowerCase();
      if (['csv', 'xlsx', 'xls'].includes(ext)) {
        setUploadFile(droppedFile);
      } else {
        toast.error('Only CSV and Excel files are supported');
      }
    }
  }, []);

  const handleFileSelect = (e) => {
    const file = e.target.files?.[0];
    if (file) {
      setUploadFile(file);
    }
  };

  const downloadTemplate = async () => {
    try {
      const response = await api.get('/alcohol/template', { responseType: 'blob' });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', 'alcohol_import_template.csv');
      document.body.appendChild(link);
      link.click();
      link.remove();
      toast.success('Template downloaded!');
    } catch (error) {
      toast.error('Failed to download template');
    }
  };

  const handleBulkUpload = async () => {
    if (!uploadFile) return;
    
    setUploading(true);
    try {
      const formData = new FormData();
      formData.append('file', uploadFile);
      
      const response = await api.post('/alcohol/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      
      setBatchResult(response.data);
      toast.success(`Processed ${response.data.successful} items successfully!`);
      setUploadFile(null);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Upload failed');
    } finally {
      setUploading(false);
    }
  };

  const exportBatch = async (batchId) => {
    try {
      const response = await api.get(`/alcohol/batches/${batchId}/export`, { responseType: 'blob' });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `alcohol_batch_${batchId.slice(0, 8)}.csv`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      toast.success('Batch exported!');
    } catch (error) {
      toast.error('Export failed');
    }
  };

  return (
    <div className="space-y-6 animate-fade-in" data-testid="alcohol-calculator-page">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold font-['Chivo'] tracking-tight flex items-center gap-3">
            <Wine className="h-8 w-8 text-primary" />
            B-CLASS Alcohol Calculator
          </h1>
          <p className="text-muted-foreground mt-1">
            Calculate duties, excise, VAT & fees for Bahamas alcohol imports
          </p>
        </div>
        <Button 
          variant="outline" 
          onClick={() => setShowHistory(!showHistory)}
          data-testid="toggle-history-btn"
        >
          <History className="h-4 w-4 mr-2" />
          {showHistory ? 'Hide History' : 'View History'}
        </Button>
      </div>

      <div className="grid lg:grid-cols-2 gap-6">
        {/* Input Form */}
        <Card className="card-hover">
          <CardHeader>
            <CardTitle className="font-['Chivo'] flex items-center gap-2">
              <Calculator className="h-5 w-5 text-primary" />
              Shipment Details
            </CardTitle>
            <CardDescription>Enter alcohol product information for duty calculation</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Product Name */}
            <div className="space-y-2">
              <Label htmlFor="product_name">Product Name *</Label>
              <Input
                id="product_name"
                placeholder="e.g., Bacardi Superior Rum"
                value={formData.product_name}
                onChange={(e) => setFormData({ ...formData, product_name: e.target.value })}
                data-testid="product-name-input"
              />
            </div>

            {/* Alcohol Type */}
            <div className="space-y-2">
              <Label>Beverage Type *</Label>
              <Select 
                value={formData.alcohol_type} 
                onValueChange={(value) => setFormData({ ...formData, alcohol_type: value })}
              >
                <SelectTrigger data-testid="alcohol-type-select">
                  <SelectValue placeholder="Select beverage type" />
                </SelectTrigger>
                <SelectContent>
                  {ALCOHOL_TYPES.map((type) => (
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

            {/* Volume & Quantity */}
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="volume_ml">Volume per Unit (ml)</Label>
                <Select 
                  value={formData.volume_ml.toString()} 
                  onValueChange={(value) => setFormData({ ...formData, volume_ml: parseInt(value) })}
                >
                  <SelectTrigger data-testid="volume-select">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {VOLUME_PRESETS.map((preset) => (
                      <SelectItem key={preset.ml} value={preset.ml.toString()}>
                        {preset.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label htmlFor="quantity">Quantity (bottles)</Label>
                <Input
                  id="quantity"
                  type="number"
                  min="1"
                  value={formData.quantity}
                  onChange={(e) => setFormData({ ...formData, quantity: parseInt(e.target.value) || 1 })}
                  data-testid="quantity-input"
                />
              </div>
            </div>

            {/* ABV */}
            <div className="space-y-2">
              <Label htmlFor="alcohol_percentage">Alcohol by Volume (% ABV)</Label>
              <div className="flex items-center gap-4">
                <Input
                  id="alcohol_percentage"
                  type="number"
                  min="0"
                  max="100"
                  step="0.1"
                  value={formData.alcohol_percentage}
                  onChange={(e) => setFormData({ ...formData, alcohol_percentage: parseFloat(e.target.value) || 0 })}
                  className="flex-1"
                  data-testid="abv-input"
                />
                <div className="flex gap-2">
                  {[5, 12, 40].map((abv) => (
                    <Button
                      key={abv}
                      variant="outline"
                      size="sm"
                      onClick={() => setFormData({ ...formData, alcohol_percentage: abv })}
                      className={cn(formData.alcohol_percentage === abv && "border-primary bg-primary/10")}
                    >
                      {abv}%
                    </Button>
                  ))}
                </div>
              </div>
            </div>

            {/* CIF Value */}
            <div className="space-y-2">
              <Label htmlFor="cif_value">CIF Value (USD) *</Label>
              <div className="relative">
                <DollarSign className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  id="cif_value"
                  type="number"
                  min="0"
                  step="0.01"
                  placeholder="0.00"
                  value={formData.cif_value || ''}
                  onChange={(e) => setFormData({ ...formData, cif_value: parseFloat(e.target.value) || 0 })}
                  className="pl-9"
                  data-testid="cif-value-input"
                />
              </div>
              <p className="text-xs text-muted-foreground">Cost + Insurance + Freight value</p>
            </div>

            {/* Country of Origin */}
            <div className="space-y-2">
              <Label htmlFor="country_of_origin">Country of Origin</Label>
              <div className="relative">
                <Globe className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  id="country_of_origin"
                  placeholder="e.g., Puerto Rico"
                  value={formData.country_of_origin}
                  onChange={(e) => setFormData({ ...formData, country_of_origin: e.target.value })}
                  className="pl-9"
                  data-testid="country-input"
                />
              </div>
            </div>

            {/* Brand/Label */}
            <div className="space-y-2">
              <Label htmlFor="brand_label">Brand/Label (Optional)</Label>
              <Input
                id="brand_label"
                placeholder="e.g., Premium Reserve"
                value={formData.brand_label}
                onChange={(e) => setFormData({ ...formData, brand_label: e.target.value })}
                data-testid="brand-input"
              />
            </div>

            {/* License Toggle */}
            <div className="flex items-center justify-between p-4 bg-muted/50 rounded-lg">
              <div className="space-y-0.5">
                <Label htmlFor="has_license">Liquor License Holder</Label>
                <p className="text-xs text-muted-foreground">Do you have a valid Bahamas liquor import license?</p>
              </div>
              <Switch
                id="has_license"
                checked={formData.has_liquor_license}
                onCheckedChange={(checked) => setFormData({ ...formData, has_liquor_license: checked })}
                data-testid="license-switch"
              />
            </div>

            {/* Action Buttons */}
            <div className="flex gap-3 pt-4">
              <Button 
                onClick={handleCalculate} 
                disabled={calculating}
                className="flex-1 bg-primary text-primary-foreground hover:bg-primary/90 glow-teal"
                data-testid="calculate-btn"
              >
                {calculating ? (
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                ) : (
                  <Sparkles className="h-4 w-4 mr-2" />
                )}
                Calculate Duties
              </Button>
              <Button variant="outline" onClick={resetForm} data-testid="reset-btn">
                Reset
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Results */}
        <div className="space-y-6">
          {result ? (
            <Card className="border-primary/30 shadow-lg shadow-primary/10">
              <CardHeader className="pb-2">
                <div className="flex items-center justify-between">
                  <CardTitle className="font-['Chivo'] text-xl">Duty Calculation Results</CardTitle>
                  <Button 
                    variant="outline" 
                    size="sm"
                    onClick={() => handleExport(result.id)}
                    data-testid="export-result-btn"
                  >
                    <Download className="h-4 w-4 mr-2" />
                    Export PDF
                  </Button>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                {/* Product Summary */}
                <div className="p-4 bg-muted/50 rounded-lg space-y-2">
                  <h4 className="font-semibold">{result.product_name}</h4>
                  <div className="flex flex-wrap gap-2 text-sm">
                    <Badge variant="outline" className="bg-primary/10 text-primary">
                      <code className="font-mono">{result.hs_code}</code>
                    </Badge>
                    <Badge variant="outline">
                      {result.quantity} × {(result.total_volume_liters / result.quantity * 1000).toFixed(0)}ml
                    </Badge>
                    <Badge variant="outline">
                      {result.alcohol_percentage}% ABV
                    </Badge>
                  </div>
                  <p className="text-xs text-muted-foreground">{result.hs_description}</p>
                </div>

                {/* Duty Breakdown */}
                <div className="space-y-3">
                  <h4 className="font-semibold text-sm uppercase tracking-wider text-muted-foreground">
                    Cost Breakdown
                  </h4>
                  
                  <div className="space-y-2">
                    <div className="flex justify-between py-2 border-b border-border/50">
                      <span className="text-muted-foreground">CIF Value</span>
                      <span className="font-mono">{formatCurrency(result.cif_value)}</span>
                    </div>
                    <div className="flex justify-between py-2 border-b border-border/50">
                      <span className="text-muted-foreground">
                        Import Duty ({result.import_duty_rate})
                      </span>
                      <span className="font-mono">{formatCurrency(result.import_duty)}</span>
                    </div>
                    <div className="flex justify-between py-2 border-b border-border/50">
                      <div>
                        <span className="text-muted-foreground">Excise Duty</span>
                        <p className="text-xs text-muted-foreground">{result.excise_calculation}</p>
                      </div>
                      <span className="font-mono">{formatCurrency(result.excise_duty)}</span>
                    </div>
                    <div className="flex justify-between py-2 border-b border-border/50">
                      <span className="text-muted-foreground">VAT ({result.vat_rate})</span>
                      <span className="font-mono">{formatCurrency(result.vat)}</span>
                    </div>
                    {result.license_fee > 0 && (
                      <div className="flex justify-between py-2 border-b border-border/50">
                        <span className="text-muted-foreground">License/Processing Fee</span>
                        <span className="font-mono">{formatCurrency(result.license_fee)}</span>
                      </div>
                    )}
                  </div>

                  <Separator />

                  {/* Total */}
                  <div className="flex justify-between items-center py-3 bg-primary/10 rounded-lg px-4">
                    <span className="font-bold text-lg">Total Landed Cost</span>
                    <span className="font-mono font-bold text-2xl text-primary">
                      {formatCurrency(result.total_landed_cost)}
                    </span>
                  </div>
                </div>

                {/* Warnings */}
                {result.warnings && result.warnings.length > 0 && (
                  <div className="space-y-2">
                    {result.warnings.map((warning, idx) => (
                      <div 
                        key={idx}
                        className="flex items-start gap-2 p-3 bg-amber-500/10 border border-amber-500/20 rounded-lg text-sm"
                      >
                        <AlertTriangle className="h-4 w-4 text-amber-400 flex-shrink-0 mt-0.5" />
                        <span className="text-amber-200">{warning}</span>
                      </div>
                    ))}
                  </div>
                )}

                {/* Permit Required */}
                {result.requires_permit && (
                  <div className="flex items-center gap-2 p-3 bg-rose-500/10 border border-rose-500/20 rounded-lg">
                    <Shield className="h-4 w-4 text-rose-400" />
                    <span className="text-sm text-rose-200">Import permit required for this product type</span>
                  </div>
                )}
              </CardContent>
            </Card>
          ) : (
            <Card className="border-dashed">
              <CardContent className="flex flex-col items-center justify-center py-16 text-center">
                <Calculator className="h-12 w-12 text-muted-foreground opacity-50 mb-4" />
                <p className="text-muted-foreground mb-2">No calculation yet</p>
                <p className="text-sm text-muted-foreground/70">
                  Fill in the shipment details and click "Calculate Duties"
                </p>
              </CardContent>
            </Card>
          )}

          {/* Rates Info */}
          {rates && (
            <Card className="bg-card/50">
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium flex items-center gap-2">
                  <Info className="h-4 w-4 text-primary" />
                  Current Bahamas Duty Rates
                </CardTitle>
              </CardHeader>
              <CardContent className="text-xs space-y-1 text-muted-foreground">
                <p>• Wine: 35% import duty + $3.50/L excise</p>
                <p>• Beer: 35% import duty + $1.50/L excise</p>
                <p>• Spirits: 45% import duty + $20.00/LPA excise</p>
                <p>• VAT: {rates.vat_rate * 100}% (on CIF + duties)</p>
                <p className="pt-2 text-xs opacity-70">Last updated: {rates.last_updated}</p>
              </CardContent>
            </Card>
          )}
        </div>
      </div>

      {/* History Panel */}
      {showHistory && (
        <Card className="animate-fade-in">
          <CardHeader>
            <CardTitle className="font-['Chivo']">Calculation History</CardTitle>
          </CardHeader>
          <CardContent>
            {history.length === 0 ? (
              <p className="text-center text-muted-foreground py-8">No previous calculations</p>
            ) : (
              <ScrollArea className="h-[300px]">
                <div className="space-y-3">
                  {history.map((calc) => (
                    <div 
                      key={calc.id}
                      className="flex items-center justify-between p-4 bg-muted/30 rounded-lg hover:bg-muted/50 transition-colors cursor-pointer"
                      onClick={() => loadFromHistory(calc)}
                      data-testid={`history-item-${calc.id}`}
                    >
                      <div>
                        <p className="font-medium">{calc.product_name}</p>
                        <div className="flex gap-2 mt-1 text-xs text-muted-foreground">
                          <span>{calc.alcohol_type}</span>
                          <span>•</span>
                          <span>{calc.quantity} units</span>
                          <span>•</span>
                          <span>{formatDate(calc.created_at)}</span>
                        </div>
                      </div>
                      <div className="text-right">
                        <p className="font-mono font-bold text-primary">
                          {formatCurrency(calc.total_landed_cost)}
                        </p>
                        <p className="text-xs text-muted-foreground">Total</p>
                      </div>
                    </div>
                  ))}
                </div>
              </ScrollArea>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
