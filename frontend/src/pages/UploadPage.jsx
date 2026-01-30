import { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Progress } from '../components/ui/progress';
import { 
  Upload, 
  FileSpreadsheet, 
  FileText, 
  X, 
  CheckCircle,
  AlertCircle,
  Loader2,
  Sparkles
} from 'lucide-react';
import { toast } from 'sonner';
import { cn } from '../lib/utils';

const ALLOWED_TYPES = {
  'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': 'xlsx',
  'application/vnd.ms-excel': 'xls',
  'text/csv': 'csv',
  'application/pdf': 'pdf'
};

export default function UploadPage() {
  const { api } = useAuth();
  const navigate = useNavigate();
  const [isDragging, setIsDragging] = useState(false);
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [classifying, setClassifying] = useState(false);
  const [progress, setProgress] = useState(0);
  const [uploadedDoc, setUploadedDoc] = useState(null);

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
      // Simulate progress for classification
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

  return (
    <div className="max-w-3xl mx-auto space-y-6 animate-fade-in" data-testid="upload-page">
      <div>
        <h1 className="text-3xl font-bold font-['Chivo'] tracking-tight">
          Upload & Classify
        </h1>
        <p className="text-muted-foreground mt-1">
          Upload commercial documents for AI-powered HS code classification
        </p>
      </div>

      <Card className="card-hover">
        <CardHeader>
          <CardTitle className="font-['Chivo']">Document Upload</CardTitle>
          <CardDescription>
            Supported formats: Excel (.xlsx, .xls), CSV, PDF (invoices, packing lists)
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
                Maximum file size: 50MB
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
                  <Button 
                    variant="ghost" 
                    size="icon" 
                    onClick={resetUpload}
                    data-testid="remove-file-btn"
                  >
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
                  <Button 
                    onClick={handleUpload} 
                    disabled={uploading}
                    className="flex-1 bg-primary text-primary-foreground hover:bg-primary/90"
                    data-testid="upload-btn"
                  >
                    {uploading ? (
                      <>
                        <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                        Uploading...
                      </>
                    ) : (
                      <>
                        <Upload className="h-4 w-4 mr-2" />
                        Upload File
                      </>
                    )}
                  </Button>
                ) : (
                  <Button 
                    onClick={handleClassify} 
                    disabled={classifying}
                    className="flex-1 bg-primary text-primary-foreground hover:bg-primary/90 glow-teal"
                    data-testid="classify-btn"
                  >
                    {classifying ? (
                      <>
                        <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                        Classifying...
                      </>
                    ) : (
                      <>
                        <Sparkles className="h-4 w-4 mr-2" />
                        Classify with AI
                      </>
                    )}
                  </Button>
                )}
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Info Cards */}
      <div className="grid md:grid-cols-3 gap-4">
        <Card className="bg-card/50">
          <CardContent className="p-4 flex items-start gap-3">
            <div className="w-8 h-8 rounded-lg bg-emerald-500/10 flex items-center justify-center flex-shrink-0">
              <CheckCircle className="h-4 w-4 text-emerald-400" />
            </div>
            <div>
              <p className="font-medium text-sm">GRI Compliant</p>
              <p className="text-xs text-muted-foreground">
                Follows WCO interpretation rules 1-6
              </p>
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
              <p className="text-xs text-muted-foreground">
                Automatic restriction alerts
              </p>
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
              <p className="text-xs text-muted-foreground">
                GPT-5.2 classification engine
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
