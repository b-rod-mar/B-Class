import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Input } from '../components/ui/input';
import { 
  FileText, 
  Search, 
  ArrowRight,
  Clock,
  CheckCircle,
  AlertCircle,
  Calendar,
  Trash2,
  Loader2
} from 'lucide-react';
import { formatDate } from '../lib/utils';
import { toast } from 'sonner';

export default function HistoryPage() {
  const { api } = useAuth();
  const [classifications, setClassifications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [deleting, setDeleting] = useState(null);

  useEffect(() => {
    fetchClassifications();
  }, []);

  const fetchClassifications = async () => {
    try {
      const response = await api.get('/classifications');
      setClassifications(response.data);
    } catch (error) {
      toast.error('Failed to load history');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (classificationId, e) => {
    e.preventDefault();
    e.stopPropagation();
    
    if (!window.confirm('Are you sure you want to delete this classification? This action cannot be undone.')) {
      return;
    }
    
    setDeleting(classificationId);
    try {
      await api.delete(`/classifications/${classificationId}`);
      toast.success('Classification deleted');
      fetchClassifications();
    } catch (error) {
      toast.error('Failed to delete classification');
    } finally {
      setDeleting(null);
    }
  };

  const filteredClassifications = classifications.filter(c => 
    c.document_name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="text-muted-foreground animate-pulse">Loading history...</div>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in" data-testid="history-page">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold font-['Chivo'] tracking-tight">
            Classification History
          </h1>
          <p className="text-muted-foreground mt-1">
            View and manage your past classifications
          </p>
        </div>
        <div className="relative w-full sm:w-64">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search documents..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-9"
            data-testid="search-input"
          />
        </div>
      </div>

      {filteredClassifications.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12">
            <FileText className="h-12 w-12 text-muted-foreground opacity-50 mb-4" />
            <p className="text-muted-foreground mb-4">
              {searchTerm ? 'No classifications match your search' : 'No classifications yet'}
            </p>
            {!searchTerm && (
              <Link to="/upload">
                <Button>Upload Your First Document</Button>
              </Link>
            )}
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4">
          {filteredClassifications.map((classification, index) => (
            <Card 
              key={classification.id} 
              className="card-hover"
              style={{ animationDelay: `${index * 50}ms` }}
              data-testid={`history-card-${classification.id}`}
            >
              <CardContent className="p-6">
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                  <div className="flex items-start gap-4">
                    <div className="w-12 h-12 rounded-lg bg-primary/10 flex items-center justify-center flex-shrink-0">
                      <FileText className="h-6 w-6 text-primary" />
                    </div>
                    <div>
                      <h3 className="font-semibold text-lg">{classification.document_name}</h3>
                      <div className="flex items-center gap-4 mt-1 text-sm text-muted-foreground">
                        <span className="flex items-center gap-1">
                          <Clock className="h-3 w-3" />
                          {formatDate(classification.created_at)}
                        </span>
                        <span className="font-mono">{classification.total_items} items</span>
                      </div>
                    </div>
                  </div>
                  
                  <div className="flex items-center gap-4">
                    <div className="flex gap-2">
                      <Badge className="status-approved">
                        <CheckCircle className="h-3 w-3 mr-1" />
                        {classification.auto_approved_count} Approved
                      </Badge>
                      {classification.needs_review_count > 0 && (
                        <Badge className="status-review">
                          <AlertCircle className="h-3 w-3 mr-1" />
                          {classification.needs_review_count} Review
                        </Badge>
                      )}
                    </div>
                    <Link to={`/classification/${classification.id}`}>
                      <Button variant="outline" size="sm" data-testid={`view-btn-${classification.id}`}>
                        View Details
                        <ArrowRight className="h-4 w-4 ml-2" />
                      </Button>
                    </Link>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
