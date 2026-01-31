import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { 
  FileText, 
  CheckCircle, 
  AlertCircle, 
  TrendingUp, 
  Upload, 
  ArrowRight,
  Clock,
  Package
} from 'lucide-react';
import { formatDate, getStatusColor, getStatusLabel } from '../lib/utils';
import { toast } from 'sonner';

export default function DashboardPage() {
  const { user, api } = useAuth();
  const [stats, setStats] = useState(null);
  const [recentClassifications, setRecentClassifications] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [statsRes, classificationsRes] = await Promise.all([
          api.get('/dashboard/stats'),
          api.get('/classifications')
        ]);
        setStats(statsRes.data);
        setRecentClassifications(classificationsRes.data.slice(0, 5));
      } catch (error) {
        toast.error('Failed to load dashboard data');
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [api]);

  const statCards = [
    {
      title: 'Total Classifications',
      value: stats?.total_classifications || 0,
      icon: FileText,
      color: 'text-primary',
      bgColor: 'bg-primary/10'
    },
    {
      title: 'Total Items Classified',
      value: stats?.total_items || 0,
      icon: Package,
      color: 'text-blue-400',
      bgColor: 'bg-blue-500/10'
    },
    {
      title: 'Auto Approved',
      value: stats?.auto_approved || 0,
      icon: CheckCircle,
      color: 'text-emerald-400',
      bgColor: 'bg-emerald-500/10'
    },
    {
      title: 'Pending Review',
      value: stats?.pending_review || 0,
      icon: AlertCircle,
      color: 'text-amber-400',
      bgColor: 'bg-amber-500/10'
    },
    {
      title: 'Avg Confidence',
      value: `${stats?.avg_confidence || 0}%`,
      icon: TrendingUp,
      color: 'text-violet-400',
      bgColor: 'bg-violet-500/10'
    }
  ];

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="text-muted-foreground animate-pulse">Loading dashboard...</div>
      </div>
    );
  }

  return (
    <div className="space-y-8 animate-fade-in" data-testid="dashboard-page">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold font-['Chivo'] tracking-tight">
            Welcome back, {user?.name?.split(' ')[0]}
          </h1>
          <p className="text-muted-foreground mt-1">
            Class-B HS Code Agent Dashboard
          </p>
        </div>
        <Link to="/upload">
          <Button className="bg-primary text-primary-foreground hover:bg-primary/90 glow-teal" data-testid="upload-btn">
            <Upload className="h-4 w-4 mr-2" />
            New Classification
          </Button>
        </Link>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
        {statCards.map((stat, index) => (
          <Card 
            key={stat.title} 
            className="stat-card"
            style={{ animationDelay: `${index * 50}ms` }}
            data-testid={`stat-${stat.title.toLowerCase().replace(/\s+/g, '-')}`}
          >
            <CardContent className="p-4">
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-xs text-muted-foreground uppercase tracking-wider">
                    {stat.title}
                  </p>
                  <p className="text-2xl font-bold mt-1 font-['Chivo']">
                    {stat.value}
                  </p>
                </div>
                <div className={`w-10 h-10 rounded-lg ${stat.bgColor} flex items-center justify-center`}>
                  <stat.icon className={`h-5 w-5 ${stat.color}`} />
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Recent Classifications */}
      <Card className="card-hover">
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle className="font-['Chivo']">Recent Classifications</CardTitle>
          <Link to="/history">
            <Button variant="ghost" size="sm" className="text-muted-foreground hover:text-foreground">
              View All
              <ArrowRight className="h-4 w-4 ml-1" />
            </Button>
          </Link>
        </CardHeader>
        <CardContent>
          {recentClassifications.length === 0 ? (
            <div className="text-center py-12">
              <FileText className="h-12 w-12 text-muted-foreground mx-auto mb-4 opacity-50" />
              <p className="text-muted-foreground">No classifications yet</p>
              <Link to="/upload">
                <Button variant="outline" className="mt-4">
                  Upload Your First Document
                </Button>
              </Link>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Document</th>
                    <th>Items</th>
                    <th>Status</th>
                    <th>Date</th>
                    <th></th>
                  </tr>
                </thead>
                <tbody>
                  {recentClassifications.map((classification) => (
                    <tr key={classification.id} data-testid={`classification-row-${classification.id}`}>
                      <td className="font-medium">{classification.document_name}</td>
                      <td>
                        <span className="font-mono">{classification.total_items}</span>
                      </td>
                      <td>
                        <div className="flex gap-2">
                          <Badge variant="outline" className="status-approved text-xs">
                            {classification.auto_approved_count} Approved
                          </Badge>
                          {classification.needs_review_count > 0 && (
                            <Badge variant="outline" className="status-review text-xs">
                              {classification.needs_review_count} Review
                            </Badge>
                          )}
                        </div>
                      </td>
                      <td className="text-muted-foreground">
                        <div className="flex items-center gap-1">
                          <Clock className="h-3 w-3" />
                          {formatDate(classification.created_at)}
                        </div>
                      </td>
                      <td>
                        <Link to={`/classification/${classification.id}`}>
                          <Button variant="ghost" size="sm">
                            View
                            <ArrowRight className="h-3 w-3 ml-1" />
                          </Button>
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Quick Actions */}
      <div className="grid md:grid-cols-2 gap-6">
        <Card className="card-hover bg-gradient-to-br from-primary/5 to-primary/10 border-primary/20">
          <CardContent className="p-6">
            <h3 className="font-bold text-lg font-['Chivo'] mb-2">CMA Compliance</h3>
            <p className="text-sm text-muted-foreground mb-4">
              All classifications follow Bahamas Customs Management Act guidelines and WCO HS Nomenclature.
            </p>
            <div className="flex items-center gap-2 text-xs text-primary">
              <CheckCircle className="h-4 w-4" />
              GRI Rules 1-6 Applied
            </div>
          </CardContent>
        </Card>
        <Card className="card-hover bg-gradient-to-br from-amber-500/5 to-amber-500/10 border-amber-500/20">
          <CardContent className="p-6">
            <h3 className="font-bold text-lg font-['Chivo'] mb-2">Electronic Single Window Ready</h3>
            <p className="text-sm text-muted-foreground mb-4">
              Export classifications in formats compatible with Electronic Single Window for seamless customs processing.
            </p>
            <div className="flex items-center gap-2 text-xs text-amber-400">
              <FileText className="h-4 w-4" />
              CSV, XLSX Export Available
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
