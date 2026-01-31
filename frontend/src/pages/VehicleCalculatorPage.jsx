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
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '../components/ui/dialog';
import { 
  Car, 
  Calculator, 
  AlertTriangle,
  Download,
  History,
  DollarSign,
  Percent,
  Globe,
  Loader2,
  Info,
  Sparkles,
  Upload,
  FileSpreadsheet,
  X,
  Fuel,
  Zap,
  Gauge,
  FileText,
  CheckCircle,
  ClipboardList,
  Truck
} from 'lucide-react';
import { toast } from 'sonner';
import { cn, formatCurrency, formatDate } from '../lib/utils';

const VEHICLE_TYPES = [
  { value: 'electric', label: 'Electric Vehicle', icon: Zap, description: '10-25% based on value' },
  { value: 'hybrid', label: 'Hybrid Vehicle', icon: Zap, description: '10-25% based on value' },
  { value: 'gasoline', label: 'Gasoline (Petrol)', icon: Fuel, description: '45-65% based on engine & value' },
  { value: 'diesel', label: 'Diesel', icon: Fuel, description: '45-65% based on engine & value' },
  { value: 'commercial', label: 'Commercial / Heavy', icon: Truck, description: '65-85% trucks & equipment' }
];

const ENGINE_SIZE_PRESETS = [
  { cc: 1000, label: '1.0L (1000cc)' },
  { cc: 1200, label: '1.2L (1200cc)' },
  { cc: 1400, label: '1.4L (1400cc)' },
  { cc: 1500, label: '1.5L (1500cc)' },
  { cc: 1600, label: '1.6L (1600cc)' },
  { cc: 1800, label: '1.8L (1800cc)' },
  { cc: 2000, label: '2.0L (2000cc)' },
  { cc: 2400, label: '2.4L (2400cc)' },
  { cc: 2500, label: '2.5L (2500cc)' },
  { cc: 3000, label: '3.0L (3000cc)' },
  { cc: 3500, label: '3.5L (3500cc)' },
  { cc: 4000, label: '4.0L (4000cc)' },
  { cc: 5000, label: '5.0L (5000cc)' }
];

const CONCESSION_TYPES = [
  { value: '', label: 'None - Standard Rate' },
  { value: 'first_vehicle', label: 'First-time Vehicle Owner' },
  { value: 'returning_resident', label: 'Returning Resident' },
  { value: 'disabled', label: 'Disabled Person Exemption' }
];

const POPULAR_MAKES = [
  'Toyota', 'Honda', 'Nissan', 'Ford', 'Chevrolet', 'Hyundai', 'Kia', 
  'BMW', 'Mercedes-Benz', 'Volkswagen', 'Tesla', 'Jeep', 'Mazda', 'Subaru'
];

const initialFormState = {
  vin: '',
  make: '',
  model: '',
  year: new Date().getFullYear(),
  vehicle_type: '',
  engine_size_cc: null,
  cif_value: 0,
  country_of_origin: '',
  is_new: true,
  fuel_type: '',
  color: '',
  mileage: null,
  is_first_time_owner: false,
  qualifies_for_concession: false,
  concession_type: '',
  is_antique: false,
  num_tires: 4
};

export default function VehicleCalculatorPage() {
  const { api } = useAuth();
  const [formData, setFormData] = useState(initialFormState);
  const [calculating, setCalculating] = useState(false);
  const [result, setResult] = useState(null);
  const [history, setHistory] = useState([]);
  const [showHistory, setShowHistory] = useState(false);
  const [rates, setRates] = useState(null);
  const [checklist, setChecklist] = useState(null);
  const [checklistOpen, setChecklistOpen] = useState(false);
  const [deleting, setDeleting] = useState(null);
  
  // Bulk upload state
  const [uploadFile, setUploadFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [batchResult, setBatchResult] = useState(null);
  const [isDragging, setIsDragging] = useState(false);

  useEffect(() => {
    fetchHistory();
    fetchRates();
    fetchChecklist();
  }, []);

  const fetchHistory = async () => {
    try {
      const response = await api.get('/vehicle/calculations');
      setHistory(response.data);
    } catch (error) {
      console.error('Failed to load history');
    }
  };

  const fetchRates = async () => {
    try {
      const response = await api.get('/vehicle/rates');
      setRates(response.data);
    } catch (error) {
      console.error('Failed to load rates');
    }
  };

  const fetchChecklist = async () => {
    try {
      const response = await api.get('/vehicle/checklist');
      setChecklist(response.data);
    } catch (error) {
      console.error('Failed to load checklist');
    }
  };

  const handleCalculate = async () => {
    if (!formData.make || !formData.model || !formData.vehicle_type || !formData.cif_value) {
      toast.error('Please fill in make, model, vehicle type, and CIF value');
      return;
    }

    setCalculating(true);
    try {
      const payload = {
        ...formData,
        engine_size_cc: formData.engine_size_cc || null,
        mileage: formData.mileage || null
      };
      const response = await api.post('/vehicle/calculate', payload);
      setResult(response.data);
      toast.success('Calculation complete!');
      fetchHistory();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Calculation failed');
    } finally {
      setCalculating(false);
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

  const handleDeleteCalculation = async (calcId) => {
    if (!window.confirm('Are you sure you want to delete this calculation?')) return;
    
    setDeleting(calcId);
    try {
      await api.delete(`/vehicle/calculations/${calcId}`);
      toast.success('Calculation deleted');
      fetchHistory();
      if (result?.id === calcId) {
        setResult(null);
      }
    } catch (error) {
      toast.error('Failed to delete calculation');
    } finally {
      setDeleting(null);
    }
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
      const response = await api.get('/vehicle/template', { responseType: 'blob' });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', 'vehicle_import_template.csv');
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
      
      const response = await api.post('/vehicle/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      
      setBatchResult(response.data);
      toast.success(`Processed ${response.data.successful} vehicles successfully!`);
      setUploadFile(null);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Upload failed');
    } finally {
      setUploading(false);
    }
  };

  const exportBatch = async (batchId, format = 'csv') => {
    try {
      const response = await api.get(`/vehicle/batches/${batchId}/export?format=${format}`, { responseType: 'blob' });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `vehicle_batch_${batchId.slice(0, 8)}.${format}`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      toast.success(`Exported as ${format.toUpperCase()}!`);
    } catch (error) {
      toast.error('Export failed');
    }
  };

  return (
    <div className="space-y-6 animate-fade-in" data-testid="vehicle-calculator-page">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold font-['Chivo'] tracking-tight flex items-center gap-3">
            <Car className="h-8 w-8 text-primary" />
            Vehicle Brokering Calculator
          </h1>
          <p className="text-muted-foreground mt-1">
            Calculate duties, VAT, levies & fees for importing vehicles into The Bahamas
          </p>
        </div>
        <div className="flex gap-2">
          <Dialog open={checklistOpen} onOpenChange={setChecklistOpen}>
            <DialogTrigger asChild>
              <Button variant="outline" data-testid="checklist-btn">
                <ClipboardList className="h-4 w-4 mr-2" />
                Clearance Checklist
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
              <DialogHeader>
                <DialogTitle className="font-['Chivo'] text-xl flex items-center gap-2">
                  <ClipboardList className="h-5 w-5 text-primary" />
                  Vehicle Clearance Checklist
                </DialogTitle>
                <DialogDescription>
                  Documents and procedures required for vehicle customs clearance in The Bahamas
                </DialogDescription>
              </DialogHeader>
              {checklist && (
                <div className="space-y-6 mt-4">
                  <div>
                    <h3 className="font-semibold text-lg mb-3 text-primary">Client Checklist</h3>
                    {checklist.client_checklist.map((category, idx) => (
                      <div key={idx} className="mb-4">
                        <h4 className="font-medium text-sm text-muted-foreground mb-2">{category.category}</h4>
                        <div className="space-y-2">
                          {category.items.map((item, itemIdx) => (
                            <div key={itemIdx} className="flex items-start gap-3 p-2 rounded bg-muted/30">
                              <div className={cn(
                                "w-5 h-5 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5",
                                item.required ? "bg-primary/20" : "bg-muted"
                              )}>
                                {item.required ? (
                                  <CheckCircle className="h-3 w-3 text-primary" />
                                ) : (
                                  <span className="text-[10px] text-muted-foreground">opt</span>
                                )}
                              </div>
                              <div>
                                <p className="text-sm font-medium">{item.item}</p>
                                <p className="text-xs text-muted-foreground">{item.notes}</p>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                  
                  <Separator />
                  
                  <div>
                    <h3 className="font-semibold text-lg mb-3 text-primary">Broker Checklist</h3>
                    {checklist.broker_checklist.map((category, idx) => (
                      <div key={idx} className="mb-4">
                        <h4 className="font-medium text-sm text-muted-foreground mb-2">{category.category}</h4>
                        <div className="space-y-2">
                          {category.items.map((item, itemIdx) => (
                            <div key={itemIdx} className="flex items-start gap-3 p-2 rounded bg-muted/30">
                              <CheckCircle className="h-4 w-4 text-primary flex-shrink-0 mt-0.5" />
                              <div>
                                <p className="text-sm font-medium">{item.item}</p>
                                <p className="text-xs text-muted-foreground">{item.notes}</p>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                  
                  <Separator />
                  
                  <div className="bg-primary/10 rounded-lg p-4">
                    <h4 className="font-semibold mb-2">Important Contacts</h4>
                    <div className="grid grid-cols-2 gap-2 text-sm">
                      <div>
                        <span className="text-muted-foreground">Customs:</span>{' '}
                        <span className="font-mono">{checklist.important_contacts.customs_main}</span>
                      </div>
                      <div>
                        <span className="text-muted-foreground">Road Traffic:</span>{' '}
                        <span className="font-mono">{checklist.important_contacts.road_traffic}</span>
                      </div>
                      <div>
                        <span className="text-muted-foreground">Email:</span>{' '}
                        <span className="font-mono text-xs">{checklist.important_contacts.customs_email}</span>
                      </div>
                      <div>
                        <span className="text-muted-foreground">Port Authority:</span>{' '}
                        <span className="font-mono">{checklist.important_contacts.port_authority}</span>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </DialogContent>
          </Dialog>
          <Button 
            variant="outline" 
            onClick={() => setShowHistory(!showHistory)}
            data-testid="toggle-history-btn"
          >
            <History className="h-4 w-4 mr-2" />
            {showHistory ? 'Hide History' : 'View History'}
          </Button>
        </div>
      </div>

      <Tabs defaultValue="single" className="w-full">
        <TabsList className="grid w-full max-w-md grid-cols-2 mb-6">
          <TabsTrigger value="single" data-testid="tab-single">
            <Calculator className="h-4 w-4 mr-2" />
            Single Vehicle
          </TabsTrigger>
          <TabsTrigger value="bulk" data-testid="tab-bulk">
            <Upload className="h-4 w-4 mr-2" />
            Bulk Upload
          </TabsTrigger>
        </TabsList>

        <TabsContent value="single">
          <div className="grid lg:grid-cols-2 gap-6">
            {/* Input Form */}
            <Card className="card-hover">
              <CardHeader>
                <CardTitle className="font-['Chivo'] flex items-center gap-2">
                  <Car className="h-5 w-5 text-primary" />
                  Vehicle Details
                </CardTitle>
                <CardDescription>Enter vehicle information for duty calculation</CardDescription>
              </CardHeader>
              <CardContent className="space-y-5">
                {/* VIN */}
                <div className="space-y-2">
                  <Label htmlFor="vin">VIN (Optional)</Label>
                  <Input
                    id="vin"
                    placeholder="e.g., 1HGBH41JXMN109186"
                    value={formData.vin}
                    onChange={(e) => setFormData({ ...formData, vin: e.target.value.toUpperCase() })}
                    className="font-mono"
                    maxLength={17}
                    data-testid="vin-input"
                  />
                </div>

                {/* Make & Model */}
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="make">Make *</Label>
                    <Select 
                      value={formData.make} 
                      onValueChange={(value) => setFormData({ ...formData, make: value })}
                    >
                      <SelectTrigger data-testid="make-select">
                        <SelectValue placeholder="Select make" />
                      </SelectTrigger>
                      <SelectContent>
                        {POPULAR_MAKES.map((make) => (
                          <SelectItem key={make} value={make}>{make}</SelectItem>
                        ))}
                        <SelectItem value="Other">Other</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="model">Model *</Label>
                    <Input
                      id="model"
                      placeholder="e.g., Camry, Civic"
                      value={formData.model}
                      onChange={(e) => setFormData({ ...formData, model: e.target.value })}
                      data-testid="model-input"
                    />
                  </div>
                </div>

                {/* Year & Condition */}
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="year">Year *</Label>
                    <Input
                      id="year"
                      type="number"
                      min="1990"
                      max={new Date().getFullYear() + 1}
                      value={formData.year}
                      onChange={(e) => setFormData({ ...formData, year: parseInt(e.target.value) || new Date().getFullYear() })}
                      data-testid="year-input"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Condition</Label>
                    <div className="flex items-center gap-4 h-10">
                      <Button
                        type="button"
                        variant={formData.is_new ? "default" : "outline"}
                        size="sm"
                        onClick={() => setFormData({ ...formData, is_new: true, mileage: 0 })}
                        className={formData.is_new ? "bg-primary text-primary-foreground" : ""}
                      >
                        New
                      </Button>
                      <Button
                        type="button"
                        variant={!formData.is_new ? "default" : "outline"}
                        size="sm"
                        onClick={() => setFormData({ ...formData, is_new: false })}
                        className={!formData.is_new ? "bg-primary text-primary-foreground" : ""}
                      >
                        Used
                      </Button>
                    </div>
                  </div>
                </div>

                {/* Vehicle Type */}
                <div className="space-y-2">
                  <Label>Vehicle Type *</Label>
                  <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                    {VEHICLE_TYPES.map((type) => (
                      <Button
                        key={type.value}
                        type="button"
                        variant="outline"
                        className={cn(
                          "h-auto py-3 flex flex-col items-center gap-1 text-xs",
                          formData.vehicle_type === type.value && "border-primary bg-primary/10 text-primary"
                        )}
                        onClick={() => setFormData({ 
                          ...formData, 
                          vehicle_type: type.value,
                          engine_size_cc: type.value === 'electric' ? null : formData.engine_size_cc
                        })}
                        data-testid={`type-${type.value}`}
                      >
                        <type.icon className="h-5 w-5" />
                        <span className="font-medium">{type.label}</span>
                        <span className="text-[10px] text-muted-foreground">{type.description}</span>
                      </Button>
                    ))}
                  </div>
                </div>

                {/* Engine Size (not for electric) */}
                {formData.vehicle_type && formData.vehicle_type !== 'electric' && (
                  <div className="space-y-2">
                    <Label htmlFor="engine_size">Engine Size (cc)</Label>
                    <Select 
                      value={formData.engine_size_cc?.toString() || ''} 
                      onValueChange={(value) => setFormData({ ...formData, engine_size_cc: parseInt(value) || null })}
                    >
                      <SelectTrigger data-testid="engine-select">
                        <SelectValue placeholder="Select engine size" />
                      </SelectTrigger>
                      <SelectContent>
                        {ENGINE_SIZE_PRESETS.map((preset) => (
                          <SelectItem key={preset.cc} value={preset.cc.toString()}>
                            {preset.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    <p className="text-xs text-muted-foreground">
                      Duty tiers: Under 1.5L (45%), 1.5-2.0L (45-65%), Over 2.0L (65%)
                    </p>
                  </div>
                )}

                {/* CIF Value */}
                <div className="space-y-2">
                  <Label htmlFor="cif_value">CIF Value (USD) *</Label>
                  <div className="relative">
                    <DollarSign className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                    <Input
                      id="cif_value"
                      type="number"
                      min="0"
                      step="100"
                      placeholder="0.00"
                      value={formData.cif_value || ''}
                      onChange={(e) => setFormData({ ...formData, cif_value: parseFloat(e.target.value) || 0 })}
                      className="pl-9"
                      data-testid="cif-value-input"
                    />
                  </div>
                  <p className="text-xs text-muted-foreground">Purchase price + shipping + insurance</p>
                </div>

                {/* Country of Origin */}
                <div className="space-y-2">
                  <Label htmlFor="country">Country of Origin *</Label>
                  <div className="relative">
                    <Globe className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                    <Input
                      id="country"
                      placeholder="e.g., Japan, USA, Germany"
                      value={formData.country_of_origin}
                      onChange={(e) => setFormData({ ...formData, country_of_origin: e.target.value })}
                      className="pl-9"
                      data-testid="country-input"
                    />
                  </div>
                </div>

                {/* Mileage (for used) */}
                {!formData.is_new && (
                  <div className="space-y-2">
                    <Label htmlFor="mileage">Mileage</Label>
                    <div className="relative">
                      <Gauge className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                      <Input
                        id="mileage"
                        type="number"
                        min="0"
                        placeholder="e.g., 50000"
                        value={formData.mileage || ''}
                        onChange={(e) => setFormData({ ...formData, mileage: parseInt(e.target.value) || null })}
                        className="pl-9"
                        data-testid="mileage-input"
                      />
                    </div>
                  </div>
                )}

                {/* Concessionary Rates */}
                <div className="p-4 bg-muted/50 rounded-lg space-y-3">
                  <div className="flex items-center justify-between">
                    <div className="space-y-0.5">
                      <Label htmlFor="concession">Apply for Concessionary Rate?</Label>
                      <p className="text-xs text-muted-foreground">Special reduced rates for eligible persons</p>
                    </div>
                    <Switch
                      id="concession"
                      checked={formData.qualifies_for_concession}
                      onCheckedChange={(checked) => setFormData({ 
                        ...formData, 
                        qualifies_for_concession: checked,
                        concession_type: checked ? formData.concession_type : ''
                      })}
                      data-testid="concession-switch"
                    />
                  </div>
                  
                  {formData.qualifies_for_concession && (
                    <Select 
                      value={formData.concession_type} 
                      onValueChange={(value) => setFormData({ ...formData, concession_type: value })}
                    >
                      <SelectTrigger data-testid="concession-type-select">
                        <SelectValue placeholder="Select concession type" />
                      </SelectTrigger>
                      <SelectContent>
                        {CONCESSION_TYPES.map((type) => (
                          <SelectItem key={type.value} value={type.value}>{type.label}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  )}
                </div>

                {/* Vehicle Age & Environmental Levy Options */}
                <div className="p-4 bg-amber-500/10 border border-amber-500/20 rounded-lg space-y-3">
                  <h4 className="text-sm font-medium text-amber-400 flex items-center gap-2">
                    <AlertTriangle className="h-4 w-4" />
                    Environmental Levy Options
                  </h4>
                  <div className="flex items-center justify-between">
                    <div className="space-y-0.5">
                      <Label htmlFor="is_antique">Antique/Vintage Vehicle?</Label>
                      <p className="text-xs text-muted-foreground">Classic cars requiring special approval ($200 flat levy)</p>
                    </div>
                    <Switch
                      id="is_antique"
                      checked={formData.is_antique}
                      onCheckedChange={(checked) => setFormData({ ...formData, is_antique: checked })}
                      data-testid="antique-switch"
                    />
                  </div>
                  
                  {!formData.is_new && (
                    <div className="space-y-2">
                      <Label htmlFor="num_tires">Number of Used Tires</Label>
                      <p className="text-xs text-muted-foreground">$5 levy per used tire imported on vehicle</p>
                      <Select 
                        value={formData.num_tires?.toString()} 
                        onValueChange={(value) => setFormData({ ...formData, num_tires: parseInt(value) })}
                      >
                        <SelectTrigger data-testid="num-tires-select">
                          <SelectValue placeholder="Select tire count" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="0">0 (No used tires)</SelectItem>
                          <SelectItem value="4">4 (Standard)</SelectItem>
                          <SelectItem value="5">5 (With spare)</SelectItem>
                          <SelectItem value="6">6 (Dual rear)</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  )}
                  
                  <p className="text-[10px] text-muted-foreground">
                    Note: Vehicles over 10 years old incur 20% Environmental Levy and require Ministry of Finance approval.
                  </p>
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
                    </div>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    {/* Vehicle Summary */}
                    <div className="p-4 bg-muted/50 rounded-lg space-y-2">
                      <h4 className="font-semibold">{result.year} {result.make} {result.model}</h4>
                      <div className="flex flex-wrap gap-2 text-sm">
                        <Badge variant="outline" className="bg-primary/10 text-primary">
                          <code className="font-mono">{result.hs_code}</code>
                        </Badge>
                        <Badge variant="outline">
                          {result.vehicle_type.charAt(0).toUpperCase() + result.vehicle_type.slice(1)}
                        </Badge>
                        <Badge variant="outline">
                          {result.engine_category}
                        </Badge>
                        <Badge variant={result.is_new ? "default" : "secondary"}>
                          {result.is_new ? 'New' : 'Used'}
                        </Badge>
                      </div>
                      <p className="text-xs text-muted-foreground">{result.hs_description}</p>
                      {result.vin && (
                        <p className="text-xs font-mono text-muted-foreground">VIN: {result.vin}</p>
                      )}
                    </div>

                    {/* Concessionary Savings Banner */}
                    {result.concessionary_applied && result.savings > 0 && (
                      <div className="p-3 bg-emerald-500/10 border border-emerald-500/20 rounded-lg">
                        <div className="flex items-center gap-2">
                          <CheckCircle className="h-5 w-5 text-emerald-400" />
                          <div>
                            <p className="font-medium text-emerald-400">Concessionary Rate Applied!</p>
                            <p className="text-sm text-emerald-400/80">
                              You save {formatCurrency(result.savings)} on import duty
                            </p>
                          </div>
                        </div>
                      </div>
                    )}

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
                          <div>
                            <span className="text-muted-foreground">Import Duty</span>
                            <p className="text-xs text-muted-foreground">{result.duty_rate_display}</p>
                          </div>
                          <span className="font-mono">{formatCurrency(result.import_duty)}</span>
                        </div>
                        <div className="flex justify-between py-2 border-b border-border/50">
                          <span className="text-muted-foreground">
                            Environmental Levy ({result.environmental_levy_rate})
                          </span>
                          <span className="font-mono">{formatCurrency(result.environmental_levy)}</span>
                        </div>
                        <div className="flex justify-between py-2 border-b border-border/50">
                          <span className="text-muted-foreground">
                            Stamp Duty ({result.stamp_duty_rate})
                          </span>
                          <span className="font-mono">{formatCurrency(result.stamp_duty)}</span>
                        </div>
                        <div className="flex justify-between py-2 border-b border-border/50">
                          <span className="text-muted-foreground">VAT ({result.vat_rate})</span>
                          <span className="font-mono">{formatCurrency(result.vat)}</span>
                        </div>
                        <div className="flex justify-between py-2 border-b border-border/50">
                          <span className="text-muted-foreground">Processing Fee</span>
                          <span className="font-mono">{formatCurrency(result.processing_fee)}</span>
                        </div>
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
                  </CardContent>
                </Card>
              ) : (
                <Card className="border-dashed">
                  <CardContent className="flex flex-col items-center justify-center py-16 text-center">
                    <Car className="h-12 w-12 text-muted-foreground opacity-50 mb-4" />
                    <p className="text-muted-foreground mb-2">No calculation yet</p>
                    <p className="text-sm text-muted-foreground/70">
                      Fill in the vehicle details and click &quot;Calculate Duties&quot;
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
                      Current Bahamas Vehicle Duty Rates
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="text-xs space-y-1 text-muted-foreground">
                    <p>• Electric/Hybrid (≤$50k): 10% | (&gt;$50k): 25%</p>
                    <p>• Gasoline/Diesel (&lt;1.5L): 45%</p>
                    <p>• Gasoline/Diesel (1.5-2.0L ≤$50k): 45% | (&gt;$50k): 65%</p>
                    <p>• Gasoline/Diesel (&gt;2.0L): 65%</p>
                    <p>• Commercial: 65-85%</p>
                    <Separator className="my-2" />
                    <p>• Environmental Levy: {Math.round(rates.environmental_levy_rate * 100)}%</p>
                    <p>• Stamp Duty: {Math.round(rates.stamp_duty_rate * 100)}%</p>
                    <p>• VAT: {Math.round(rates.vat_rate * 100)}%</p>
                    <p>• Processing Fee: ${rates.processing_fee}</p>
                    <p className="pt-2 text-xs opacity-70">Last updated: {rates.last_updated}</p>
                  </CardContent>
                </Card>
              )}
            </div>
          </div>
        </TabsContent>

        {/* Bulk Upload Tab */}
        <TabsContent value="bulk">
          <div className="grid lg:grid-cols-2 gap-6">
            {/* Upload Section */}
            <Card className="card-hover">
              <CardHeader>
                <CardTitle className="font-['Chivo'] flex items-center gap-2">
                  <Upload className="h-5 w-5 text-primary" />
                  Bulk Vehicle Upload
                </CardTitle>
                <CardDescription>
                  Upload a CSV or Excel file to calculate duties for multiple vehicles at once
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                {/* Template Download */}
                <div className="p-4 bg-muted/30 rounded-lg flex items-center justify-between">
                  <div>
                    <p className="font-medium text-sm">Download Template</p>
                    <p className="text-xs text-muted-foreground">
                      Get a pre-formatted CSV with sample data
                    </p>
                  </div>
                  <Button 
                    variant="outline" 
                    size="sm"
                    onClick={downloadTemplate}
                    data-testid="download-template-btn"
                  >
                    <Download className="h-4 w-4 mr-2" />
                    Template
                  </Button>
                </div>

                {/* Dropzone */}
                {!uploadFile ? (
                  <div
                    className={cn(
                      "border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all duration-200",
                      isDragging ? "border-primary bg-primary/5" : "border-border hover:border-primary/50"
                    )}
                    onDragEnter={handleDrag}
                    onDragLeave={handleDrag}
                    onDragOver={handleDrag}
                    onDrop={handleDrop}
                    onClick={() => document.getElementById('bulk-file-input').click()}
                    data-testid="bulk-dropzone"
                  >
                    <input
                      id="bulk-file-input"
                      type="file"
                      className="hidden"
                      accept=".csv,.xlsx,.xls"
                      onChange={handleFileSelect}
                    />
                    <FileSpreadsheet className={cn(
                      "h-10 w-10 mx-auto mb-3 transition-colors",
                      isDragging ? "text-primary" : "text-muted-foreground"
                    )} />
                    <p className="font-medium mb-1">Drop your file here or click to browse</p>
                    <p className="text-sm text-muted-foreground">
                      Supports CSV, XLSX, XLS
                    </p>
                  </div>
                ) : (
                  <div className="space-y-4">
                    <div className="flex items-center gap-4 p-4 bg-muted/50 rounded-lg">
                      <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
                        <FileSpreadsheet className="h-5 w-5 text-primary" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="font-medium truncate">{uploadFile.name}</p>
                        <p className="text-sm text-muted-foreground">
                          {(uploadFile.size / 1024).toFixed(1)} KB
                        </p>
                      </div>
                      <Button 
                        variant="ghost" 
                        size="icon"
                        onClick={() => setUploadFile(null)}
                        data-testid="remove-bulk-file-btn"
                      >
                        <X className="h-4 w-4" />
                      </Button>
                    </div>
                    <Button 
                      onClick={handleBulkUpload}
                      disabled={uploading}
                      className="w-full bg-primary text-primary-foreground hover:bg-primary/90 glow-teal"
                      data-testid="process-bulk-btn"
                    >
                      {uploading ? (
                        <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      ) : (
                        <Sparkles className="h-4 w-4 mr-2" />
                      )}
                      Process & Calculate Duties
                    </Button>
                  </div>
                )}

                {/* Template Columns Info */}
                <div className="text-xs text-muted-foreground space-y-1">
                  <p className="font-medium text-foreground">Required columns:</p>
                  <p>• make, model, year, vehicle_type, cif_value, country_of_origin</p>
                  <p className="font-medium text-foreground mt-2">Optional columns:</p>
                  <p>• vin, engine_size_cc, is_new, mileage, color</p>
                  <p className="font-medium text-foreground mt-2">Vehicle types:</p>
                  <p>• electric, hybrid, gasoline, diesel, commercial</p>
                </div>
              </CardContent>
            </Card>

            {/* Batch Results */}
            <div className="space-y-6">
              {batchResult ? (
                <Card className="border-primary/30 shadow-lg shadow-primary/10">
                  <CardHeader className="pb-2">
                    <div className="flex items-center justify-between flex-wrap gap-2">
                      <CardTitle className="font-['Chivo'] text-xl">Batch Results</CardTitle>
                      <div className="flex gap-2">
                        <Button 
                          variant="outline" 
                          size="sm"
                          onClick={() => exportBatch(batchResult.batch_id, 'csv')}
                          data-testid="export-batch-csv"
                        >
                          <Download className="h-4 w-4 mr-1" />
                          CSV
                        </Button>
                        <Button 
                          variant="outline" 
                          size="sm"
                          onClick={() => exportBatch(batchResult.batch_id, 'xlsx')}
                          data-testid="export-batch-xlsx"
                        >
                          <Download className="h-4 w-4 mr-1" />
                          Excel
                        </Button>
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    {/* Summary */}
                    <div className="grid grid-cols-2 gap-4">
                      <div className="p-3 bg-emerald-500/10 rounded-lg text-center">
                        <p className="text-2xl font-bold text-emerald-400">{batchResult.successful}</p>
                        <p className="text-xs text-emerald-400/70">Vehicles Processed</p>
                      </div>
                      {batchResult.failed > 0 && (
                        <div className="p-3 bg-rose-500/10 rounded-lg text-center">
                          <p className="text-2xl font-bold text-rose-400">{batchResult.failed}</p>
                          <p className="text-xs text-rose-400/70">Failed</p>
                        </div>
                      )}
                      <div className="p-3 bg-muted/50 rounded-lg text-center">
                        <p className="text-xl font-bold font-mono">{formatCurrency(batchResult.total_cif)}</p>
                        <p className="text-xs text-muted-foreground">Total CIF Value</p>
                      </div>
                      <div className="p-3 bg-muted/50 rounded-lg text-center">
                        <p className="text-xl font-bold font-mono">{formatCurrency(batchResult.total_duties)}</p>
                        <p className="text-xs text-muted-foreground">Total Import Duties</p>
                      </div>
                      <div className="p-3 bg-primary/10 rounded-lg text-center col-span-2">
                        <p className="text-2xl font-bold font-mono text-primary">
                          {formatCurrency(batchResult.total_landed_cost)}
                        </p>
                        <p className="text-xs text-primary/70">Total Landed Cost (All Vehicles)</p>
                      </div>
                    </div>

                    {/* Results Table */}
                    <ScrollArea className="h-[350px]">
                      <table className="w-full text-sm">
                        <thead className="sticky top-0 bg-card">
                          <tr className="border-b border-border">
                            <th className="text-left py-2 px-2">#</th>
                            <th className="text-left py-2 px-2">Vehicle</th>
                            <th className="text-left py-2 px-2">Type</th>
                            <th className="text-right py-2 px-2">CIF</th>
                            <th className="text-right py-2 px-2">Duty</th>
                            <th className="text-right py-2 px-2">Total</th>
                          </tr>
                        </thead>
                        <tbody>
                          {batchResult.results.map((item, idx) => (
                            <tr key={idx} className="border-b border-border/50 hover:bg-muted/30">
                              <td className="py-2 px-2 text-muted-foreground">{item.row}</td>
                              <td className="py-2 px-2">
                                <div>
                                  <p className="font-medium truncate max-w-[120px]">
                                    {item.year} {item.make}
                                  </p>
                                  <p className="text-xs text-muted-foreground">{item.model}</p>
                                </div>
                              </td>
                              <td className="py-2 px-2">
                                <Badge variant="outline" className="text-[10px]">
                                  {item.duty_rate_display}
                                </Badge>
                              </td>
                              <td className="py-2 px-2 text-right font-mono text-muted-foreground text-xs">
                                {formatCurrency(item.cif_value)}
                              </td>
                              <td className="py-2 px-2 text-right font-mono text-xs">
                                {formatCurrency(item.import_duty)}
                              </td>
                              <td className="py-2 px-2 text-right font-mono font-medium">
                                {formatCurrency(item.total_landed_cost)}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </ScrollArea>

                    {/* Errors */}
                    {batchResult.errors && batchResult.errors.length > 0 && (
                      <div className="space-y-2">
                        <p className="text-sm font-medium text-rose-400">Errors:</p>
                        {batchResult.errors.map((error, idx) => (
                          <div key={idx} className="text-xs text-rose-400 bg-rose-500/10 p-2 rounded">
                            Row {error.row}: {error.error}
                          </div>
                        ))}
                      </div>
                    )}
                  </CardContent>
                </Card>
              ) : (
                <Card className="border-dashed">
                  <CardContent className="flex flex-col items-center justify-center py-16 text-center">
                    <FileSpreadsheet className="h-12 w-12 text-muted-foreground opacity-50 mb-4" />
                    <p className="text-muted-foreground mb-2">No batch results yet</p>
                    <p className="text-sm text-muted-foreground/70">
                      Upload a CSV or Excel file to calculate duties for multiple vehicles
                    </p>
                  </CardContent>
                </Card>
              )}

              {/* Quick Info */}
              <Card className="bg-card/50">
                <CardContent className="p-4 text-xs text-muted-foreground">
                  <p className="font-medium text-foreground mb-2">Example Row:</p>
                  <code className="text-[10px] block bg-muted p-2 rounded overflow-x-auto">
                    1HGBH41JXMN109186,Toyota,Camry,2023,gasoline,2500,35000,Japan,true,0,White
                  </code>
                </CardContent>
              </Card>
            </div>
          </div>
        </TabsContent>
      </Tabs>

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
                        <p className="font-medium">{calc.year} {calc.make} {calc.model}</p>
                        <div className="flex gap-2 mt-1 text-xs text-muted-foreground">
                          <span>{calc.vehicle_type}</span>
                          <span>•</span>
                          <span>{calc.engine_category}</span>
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
