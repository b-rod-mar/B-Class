import { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Progress } from '../components/ui/progress';
import { Badge } from '../components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { ScrollArea } from '../components/ui/scroll-area';
import { 
  Upload, 
  FileSpreadsheet, 
  FileText, 
  X, 
  CheckCircle,
  AlertCircle,
  Loader2,
  Sparkles,
  Download,
  List,
  Package
} from 'lucide-react';
import { toast } from 'sonner';
import { cn, formatCurrency, getConfidenceColor } from '../lib/utils';

export default function UploadPage() {
  const { api } = useAuth();
  const navigate = useNavigate();
  
  // Document upload state
  const [isDragging, setIsDragging] = useState(false);
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [classifying, setClassifying] = useState(false);
  const [progress, setProgress] = useState(0);
  const [uploadedDoc, setUploadedDoc] = useState(null);
  
  // Bulk HS classification state
  const [bulkFile, setBulkFile] = useState(null);
  const [bulkUploading, setBulkUploading] = useState(false);
  const [bulkResult, setBulkResult] = useState(null);
  const [bulkDragging, setBulkDragging] = useState(false);

  // Document upload handlers
  const handleDrag = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setIsDragging(true);
    } else if (e.type === 'dragleave') {
      setIsDragging(false);
    }
  }, []);

  const validateFile = (file) => {
    const ext = file.name.split('.').pop().toLowerCase();
    if (!['xlsx', 'xls', 'csv', 'pdf'].includes(ext)) {
      toast.error('Invalid file type. Supported: Excel, CSV, PDF');
      return false;
    }
    if (file.size > 50 * 1024 * 1024) {
      toast.error('File too large. Maximum 50MB allowed.');
      return false;
    }
    return true;
  };

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
    const droppedFile = e.dataTransfer?.files?.[0];
    if (droppedFile && validateFile(droppedFile)) {
      setFile(droppedFile);
    }
  }, []);

  const handleFileSelect = (e) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile && validateFile(selectedFile)) {
      setFile(selectedFile);
    }
  };

  const getFileIcon = () => {
    if (!file) return Upload;
    const ext = file.name.split('.').pop().toLowerCase();
    if (['xlsx', 'xls', 'csv'].includes(ext)) return FileSpreadsheet;
    return FileText;
  };

  const FileIcon = getFileIcon();

  const handleUpload = async () => {
    if (!file) return;
    setUploading(true);
    setProgress(20);

    try {
      const formData = new FormData();
      formData.append('file', file);

      const uploadRes = await api.post('/documents/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        onUploadProgress: (progressEvent) => {
          const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          setProgress(Math.min(40, 20 + (percentCompleted * 0.2)));
        }
      });

      setUploadedDoc(uploadRes.data);
      setProgress(50);
      toast.success('File uploaded successfully!');
      setUploading(false);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Upload failed');
      setUploading(false);
      setProgress(0);
    }
  };

  const handleClassify = async () => {
    if (!uploadedDoc) return;
    setClassifying(true);
    setProgress(60);

    try {
      const progressInterval = setInterval(() => {
        setProgress((prev) => Math.min(90, prev + 5));
      }, 500);

      const classifyRes = await api.post(`/classifications/process/${uploadedDoc.id}`);
      
      clearInterval(progressInterval);
      setProgress(100);
      toast.success('Classification complete!');
      
      setTimeout(() => {
        navigate(`/classification/${classifyRes.data.id}`);
      }, 500);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Classification failed');
      setClassifying(false);
      setProgress(50);
    }
  };

  const resetUpload = () => {
    setFile(null);
    setUploadedDoc(null);
    setProgress(0);
  };

  // Bulk HS classification handlers
  const handleBulkDrag = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setBulkDragging(true);
    } else if (e.type === 'dragleave') {
      setBulkDragging(false);
    }
  }, []);

  const handleBulkDrop = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    setBulkDragging(false);
    const droppedFile = e.dataTransfer?.files?.[0];
    if (droppedFile) {
      const ext = droppedFile.name.split('.').pop().toLowerCase();
      if (['csv', 'xlsx', 'xls'].includes(ext)) {
        setBulkFile(droppedFile);
      } else {
        toast.error('Only CSV and Excel files are supported');
      }
    }
  }, []);

  const handleBulkFileSelect = (e) => {
    const file = e.target.files?.[0];
    if (file) {
      setBulkFile(file);
    }
  };

  const downloadTemplate = async () => {
    try {
      const response = await api.get('/hs-codes/template', { responseType: 'blob' });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', 'hs_classification_template.csv');
      document.body.appendChild(link);
      link.click();
      link.remove();
      toast.success('Template downloaded!');
    } catch (error) {
      toast.error('Failed to download template');
    }
  };

  const handleBulkClassify = async () => {
    if (!bulkFile) return;
    setBulkUploading(true);

    try {
      const formData = new FormData();
      formData.append('file', bulkFile);
      
      const response = await api.post('/hs-codes/bulk-classify', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      
      setBulkResult(response.data);
      toast.success(`Classified ${response.data.total_items} items!`);
      setBulkFile(null);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Classification failed');
    } finally {
      setBulkUploading(false);
    }
  };

  const exportBulkResult = async (format = 'csv') => {
    if (!bulkResult) return;
    try {
      const response = await api.get(`/hs-codes/batches/${bulkResult.batch_id}/export?format=${format}`, { 
        responseType: 'blob' 
      });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `hs_classification_${bulkResult.batch_id.slice(0, 8)}.${format}`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      toast.success(`Exported as ${format.toUpperCase()}`);
    } catch (error) {
      toast.error('Export failed');
    }
  };

  return (
    <div className="max-w-5xl mx-auto space-y-6 animate-fade-in" data-testid="upload-page">
      <div>
        <h1 className="text-3xl font-bold font-['Chivo'] tracking-tight">
          Upload & Classify
        </h1>
        <p className="text-muted-foreground mt-1">
          AI-powered HS code classification for Bahamas imports
        </p>
      </div>

      <Tabs defaultValue="document" className="w-full">
        <TabsList className="grid w-full max-w-md grid-cols-2 mb-6">
          <TabsTrigger value="document" data-testid="tab-document">
            <FileText className="h-4 w-4 mr-2" />
            Document Upload
          </TabsTrigger>
          <TabsTrigger value="bulk" data-testid="tab-bulk-hs">
            <List className="h-4 w-4 mr-2" />
            Bulk Item List
          </TabsTrigger>
        </TabsList>

        {/* Document Upload Tab */}
        <TabsContent value="document">
          <div className="grid lg:grid-cols-3 gap-6">
            <Card className="card-hover lg:col-span-2">
              <CardHeader>
                <CardTitle className="font-['Chivo']">Document Upload</CardTitle>
                <CardDescription>
                  Upload invoices, packing lists, or commercial documents (Excel, CSV, PDF)
                </CardDescription>
              </CardHeader>
              <CardContent>
                {!file ? (
                  <div
                    className={cn(
                      "dropzone cursor-pointer",
                      isDragging && "dropzone-active"
                    )}
                    onDragEnter={handleDrag}
                    onDragLeave={handleDrag}
                    onDragOver={handleDrag}
                    onDrop={handleDrop}
                    onClick={() => document.getElementById('file-input').click()}
                    data-testid="dropzone"
                  >
                    <input
                      id="file-input"
                      type="file"
                      className="hidden"
                      accept=".xlsx,.xls,.csv,.pdf"
                      onChange={handleFileSelect}
                      data-testid="file-input"
                    />
                    <Upload className={cn(
                      "h-12 w-12 mx-auto mb-4 transition-colors duration-200",
                      isDragging ? "text-primary" : "text-muted-foreground"
                    )} />
                    <p className="text-lg font-medium mb-1">
                      Drop your file here or click to browse
                    </p>
                    <p className="text-sm text-muted-foreground">
                      Supports: Excel, CSV, PDF • Max 50MB
                    </p>
                  </div>
                ) : (
                  <div className="space-y-4">
                    <div className="flex items-center gap-4 p-4 bg-muted/50 rounded-lg">
                      <div className="w-12 h-12 rounded-lg bg-primary/10 flex items-center justify-center">
                        <FileIcon className="h-6 w-6 text-primary" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="font-medium truncate">{file.name}</p>
                        <p className="text-sm text-muted-foreground">
                          {(file.size / 1024 / 1024).toFixed(2)} MB
                        </p>
                      </div>
                      {!uploading && !classifying && (
                        <Button variant="ghost" size="icon" onClick={resetUpload} data-testid="remove-file-btn">
                          <X className="h-4 w-4" />
                        </Button>
                      )}
                    </div>

                    {progress > 0 && (
                      <div className="space-y-2">
                        <div className="flex justify-between text-sm">
                          <span className="text-muted-foreground">
                            {progress < 50 ? 'Uploading...' : progress < 100 ? 'Classifying with AI...' : 'Complete!'}
                          </span>
                          <span className="font-mono text-primary">{progress}%</span>
                        </div>
                        <Progress value={progress} className="h-2" />
                      </div>
                    )}

                    <div className="flex gap-3">
                      {!uploadedDoc ? (
                        <Button onClick={handleUpload} disabled={uploading} className="flex-1 bg-primary text-primary-foreground hover:bg-primary/90" data-testid="upload-btn">
                          {uploading ? <><Loader2 className="h-4 w-4 mr-2 animate-spin" />Uploading...</> : <><Upload className="h-4 w-4 mr-2" />Upload File</>}
                        </Button>
                      ) : (
                        <Button onClick={handleClassify} disabled={classifying} className="flex-1 bg-primary text-primary-foreground hover:bg-primary/90 glow-teal" data-testid="classify-btn">
                          {classifying ? <><Loader2 className="h-4 w-4 mr-2 animate-spin" />Classifying...</> : <><Sparkles className="h-4 w-4 mr-2" />Classify with AI</>}
                        </Button>
                      )}
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Info Cards */}
            <div className="space-y-4">
              <Card className="bg-card/50">
                <CardContent className="p-4 flex items-start gap-3">
                  <div className="w-8 h-8 rounded-lg bg-emerald-500/10 flex items-center justify-center flex-shrink-0">
                    <CheckCircle className="h-4 w-4 text-emerald-400" />
                  </div>
                  <div>
                    <p className="font-medium text-sm">GRI Compliant</p>
                    <p className="text-xs text-muted-foreground">WCO rules 1-6</p>
                  </div>
                </CardContent>
              </Card>
              <Card className="bg-card/50">
                <CardContent className="p-4 flex items-start gap-3">
                  <div className="w-8 h-8 rounded-lg bg-amber-500/10 flex items-center justify-center flex-shrink-0">
                    <AlertCircle className="h-4 w-4 text-amber-400" />
                  </div>
                  <div>
                    <p className="font-medium text-sm">CMA Flags</p>
                    <p className="text-xs text-muted-foreground">Auto restriction alerts</p>
                  </div>
                </CardContent>
              </Card>
              <Card className="bg-card/50">
                <CardContent className="p-4 flex items-start gap-3">
                  <div className="w-8 h-8 rounded-lg bg-primary/10 flex items-center justify-center flex-shrink-0">
                    <Sparkles className="h-4 w-4 text-primary" />
                  </div>
                  <div>
                    <p className="font-medium text-sm">AI Powered</p>
                    <p className="text-xs text-muted-foreground">GPT-5.2 engine</p>
                  </div>
                </CardContent>
              </Card>
            </div>
          </div>
        </TabsContent>

        {/* Bulk Item List Tab */}
        <TabsContent value="bulk">
          <div className="grid lg:grid-cols-2 gap-6">
            {/* Upload Section */}
            <Card className="card-hover">
              <CardHeader>
                <CardTitle className="font-['Chivo'] flex items-center gap-2">
                  <List className="h-5 w-5 text-primary" />
                  Bulk HS Classification
                </CardTitle>
                <CardDescription>
                  Upload a list of items to get HS codes for each one
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                {/* Template Download */}
                <div className="p-4 bg-muted/30 rounded-lg flex items-center justify-between">
                  <div>
                    <p className="font-medium text-sm">Download Template</p>
                    <p className="text-xs text-muted-foreground">
                      Pre-formatted CSV with sample items
                    </p>
                  </div>
                  <Button variant="outline" size="sm" onClick={downloadTemplate} data-testid="download-hs-template-btn">
                    <Download className="h-4 w-4 mr-2" />
                    Template
                  </Button>
                </div>

                {/* Dropzone */}
                {!bulkFile ? (
                  <div
                    className={cn(
                      "border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all duration-200",
                      bulkDragging ? "border-primary bg-primary/5" : "border-border hover:border-primary/50"
                    )}
                    onDragEnter={handleBulkDrag}
                    onDragLeave={handleBulkDrag}
                    onDragOver={handleBulkDrag}
                    onDrop={handleBulkDrop}
                    onClick={() => document.getElementById('bulk-hs-file-input').click()}
                    data-testid="bulk-hs-dropzone"
                  >
                    <input
                      id="bulk-hs-file-input"
                      type="file"
                      className="hidden"
                      accept=".csv,.xlsx,.xls"
                      onChange={handleBulkFileSelect}
                    />
                    <FileSpreadsheet className={cn(
                      "h-10 w-10 mx-auto mb-3 transition-colors",
                      bulkDragging ? "text-primary" : "text-muted-foreground"
                    )} />
                    <p className="font-medium mb-1">Drop your item list here</p>
                    <p className="text-sm text-muted-foreground">CSV or Excel file</p>
                  </div>
                ) : (
                  <div className="space-y-4">
                    <div className="flex items-center gap-4 p-4 bg-muted/50 rounded-lg">
                      <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
                        <FileSpreadsheet className="h-5 w-5 text-primary" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="font-medium truncate">{bulkFile.name}</p>
                        <p className="text-sm text-muted-foreground">{(bulkFile.size / 1024).toFixed(1)} KB</p>
                      </div>
                      <Button variant="ghost" size="icon" onClick={() => setBulkFile(null)} data-testid="remove-bulk-hs-file-btn">
                        <X className="h-4 w-4" />
                      </Button>
                    </div>
                    <Button onClick={handleBulkClassify} disabled={bulkUploading} className="w-full bg-primary text-primary-foreground hover:bg-primary/90 glow-teal" data-testid="bulk-classify-btn">
                      {bulkUploading ? <><Loader2 className="h-4 w-4 mr-2 animate-spin" />Classifying...</> : <><Sparkles className="h-4 w-4 mr-2" />Classify All Items</>}
                    </Button>
                  </div>
                )}

                {/* Template Info */}
                <div className="text-xs text-muted-foreground space-y-1">
                  <p className="font-medium text-foreground">Required column:</p>
                  <p>• description</p>
                  <p className="font-medium text-foreground mt-2">Optional columns:</p>
                  <p>• quantity, unit, unit_value, total_value, country_of_origin</p>
                </div>
              </CardContent>
            </Card>

            {/* Results */}
            <div className="space-y-6">
              {bulkResult ? (
                <Card className="border-primary/30 shadow-lg shadow-primary/10">
                  <CardHeader className="pb-2">
                    <div className="flex items-center justify-between">
                      <CardTitle className="font-['Chivo'] text-xl">Classification Results</CardTitle>
                      <div className="flex gap-2">
                        <Button variant="outline" size="sm" onClick={() => exportBulkResult('csv')} data-testid="export-bulk-csv">
                          <Download className="h-4 w-4 mr-1" />
                          CSV
                        </Button>
                        <Button variant="outline" size="sm" onClick={() => exportBulkResult('xlsx')} data-testid="export-bulk-xlsx">
                          <Download className="h-4 w-4 mr-1" />
                          Excel
                        </Button>
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    {/* Summary */}
                    <div className="grid grid-cols-3 gap-3">
                      <div className="p-3 bg-muted/50 rounded-lg text-center">
                        <p className="text-2xl font-bold font-['Chivo']">{bulkResult.total_items}</p>
                        <p className="text-xs text-muted-foreground">Total Items</p>
                      </div>
                      <div className="p-3 bg-emerald-500/10 rounded-lg text-center">
                        <p className="text-2xl font-bold text-emerald-400">{bulkResult.auto_approved}</p>
                        <p className="text-xs text-emerald-400/70">Auto Approved</p>
                      </div>
                      <div className="p-3 bg-primary/10 rounded-lg text-center">
                        <p className="text-2xl font-bold text-primary">{bulkResult.avg_confidence}%</p>
                        <p className="text-xs text-primary/70">Avg Confidence</p>
                      </div>
                    </div>

                    {/* Results Table */}
                    <ScrollArea className="h-[400px]">
                      <table className="w-full text-sm">
                        <thead className="sticky top-0 bg-card">
                          <tr className="border-b border-border">
                            <th className="text-left py-2 px-2">Description</th>
                            <th className="text-left py-2 px-2">HS Code</th>
                            <th className="text-center py-2 px-2">Confidence</th>
                          </tr>
                        </thead>
                        <tbody>
                          {bulkResult.items.map((item, idx) => (
                            <tr key={idx} className="border-b border-border/50 hover:bg-muted/30">
                              <td className="py-2 px-2">
                                <p className="font-medium truncate max-w-[180px]" title={item.clean_description || item.original_description}>
                                  {item.clean_description || item.original_description}
                                </p>
                                {item.hs_description && (
                                  <p className="text-xs text-muted-foreground truncate max-w-[180px]" title={item.hs_description}>
                                    {item.hs_description}
                                  </p>
                                )}
                              </td>
                              <td className="py-2 px-2">
                                <code className="text-xs bg-primary/10 px-1.5 py-0.5 rounded text-primary font-mono">
                                  {item.hs_code || '-'}
                                </code>
                              </td>
                              <td className="py-2 px-2 text-center">
                                <Badge className={cn("font-mono text-xs", getConfidenceColor(item.confidence_score))}>
                                  {item.confidence_score}%
                                </Badge>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </ScrollArea>
                  </CardContent>
                </Card>
              ) : (
                <Card className="border-dashed">
                  <CardContent className="flex flex-col items-center justify-center py-16 text-center">
                    <Package className="h-12 w-12 text-muted-foreground opacity-50 mb-4" />
                    <p className="text-muted-foreground mb-2">No results yet</p>
                    <p className="text-sm text-muted-foreground/70">
                      Upload a CSV with item descriptions to classify
                    </p>
                  </CardContent>
                </Card>
              )}

              {/* Example */}
              <Card className="bg-card/50">
                <CardContent className="p-4 text-xs text-muted-foreground">
                  <p className="font-medium text-foreground mb-2">Example Items:</p>
                  <code className="text-[10px] block bg-muted p-2 rounded overflow-x-auto whitespace-pre">
{`description,quantity,unit_value
Apple iPhone 15 Pro,10,999.00
Nike Running Shoes,24,180.00
Samsung 65" Smart TV,5,1200.00`}
                  </code>
                </CardContent>
              </Card>
            </div>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
