import { useState } from 'react';
import { Link, useSearchParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { toast } from 'sonner';
import { Anchor, Loader2, ArrowLeft, Lock, CheckCircle, AlertTriangle } from 'lucide-react';

const API_URL = process.env.REACT_APP_BACKEND_URL;

export default function ResetPasswordPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const token = searchParams.get('token');
  
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState(null);
  const [formData, setFormData] = useState({
    password: '',
    confirmPassword: ''
  });

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (formData.password !== formData.confirmPassword) {
      toast.error('Passwords do not match');
      return;
    }
    
    if (formData.password.length < 6) {
      toast.error('Password must be at least 6 characters');
      return;
    }
    
    setLoading(true);
    setError(null);
    
    try {
      await axios.post(`${API_URL}/api/auth/reset-password`, {
        token,
        new_password: formData.password
      });
      setSuccess(true);
      toast.success('Password reset successfully!');
    } catch (err) {
      const errorMsg = err.response?.data?.detail || 'Failed to reset password';
      setError(errorMsg);
      toast.error(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  // No token provided
  if (!token) {
    return (
      <div className="min-h-screen login-bg flex items-center justify-center p-4">
        <div className="w-full max-w-md animate-fade-in">
          <Card className="glass border-white/10">
            <CardHeader className="text-center pb-2">
              <div className="mx-auto w-14 h-14 rounded-xl bg-rose-500/10 flex items-center justify-center mb-4">
                <AlertTriangle className="h-8 w-8 text-rose-500" />
              </div>
              <CardTitle className="text-2xl font-bold font-['Chivo']">
                Invalid Reset Link
              </CardTitle>
              <CardDescription className="text-muted-foreground">
                This password reset link is invalid or has expired.
              </CardDescription>
            </CardHeader>
            <CardContent className="pt-4 space-y-4">
              <Link to="/forgot-password" className="block">
                <Button className="w-full bg-primary text-primary-foreground hover:bg-primary/90 glow-teal">
                  Request New Reset Link
                </Button>
              </Link>
              <Link to="/login" className="block">
                <Button variant="ghost" className="w-full">
                  <ArrowLeft className="h-4 w-4 mr-2" />
                  Back to Login
                </Button>
              </Link>
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen login-bg flex items-center justify-center p-4">
      <div className="w-full max-w-md animate-fade-in">
        <Card className="glass border-white/10">
          <CardHeader className="text-center pb-2">
            <div className="mx-auto w-14 h-14 rounded-xl bg-primary/10 flex items-center justify-center mb-4 glow-teal">
              <Anchor className="h-8 w-8 text-primary" />
            </div>
            <CardTitle className="text-2xl font-bold font-['Chivo']">
              {success ? 'Password Reset!' : 'Set New Password'}
            </CardTitle>
            <CardDescription className="text-muted-foreground">
              {success 
                ? 'Your password has been reset successfully'
                : 'Enter your new password below'
              }
            </CardDescription>
          </CardHeader>
          <CardContent className="pt-4">
            {success ? (
              <div className="space-y-6 text-center">
                <div className="mx-auto w-16 h-16 rounded-full bg-emerald-500/10 flex items-center justify-center">
                  <CheckCircle className="h-8 w-8 text-emerald-500" />
                </div>
                <p className="text-sm text-muted-foreground">
                  You can now log in with your new password.
                </p>
                <Button 
                  className="w-full bg-primary text-primary-foreground hover:bg-primary/90 glow-teal"
                  onClick={() => navigate('/login')}
                  data-testid="go-to-login-btn"
                >
                  Go to Login
                </Button>
              </div>
            ) : (
              <form onSubmit={handleSubmit} className="space-y-4">
                {error && (
                  <div className="p-3 bg-rose-500/10 border border-rose-500/20 rounded-lg text-sm text-rose-400 flex items-center gap-2">
                    <AlertTriangle className="h-4 w-4 flex-shrink-0" />
                    {error}
                  </div>
                )}
                <div className="space-y-2">
                  <Label htmlFor="password">New Password</Label>
                  <Input
                    id="password"
                    type="password"
                    placeholder="••••••••"
                    value={formData.password}
                    onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                    required
                    minLength={6}
                    data-testid="reset-password-input"
                    className="bg-background/50"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="confirmPassword">Confirm New Password</Label>
                  <Input
                    id="confirmPassword"
                    type="password"
                    placeholder="••••••••"
                    value={formData.confirmPassword}
                    onChange={(e) => setFormData({ ...formData, confirmPassword: e.target.value })}
                    required
                    minLength={6}
                    data-testid="reset-confirm-password-input"
                    className="bg-background/50"
                  />
                </div>
                <Button 
                  type="submit" 
                  className="w-full bg-primary text-primary-foreground hover:bg-primary/90 glow-teal"
                  disabled={loading}
                  data-testid="reset-submit-btn"
                >
                  {loading ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <>
                      <Lock className="h-4 w-4 mr-2" />
                      Reset Password
                    </>
                  )}
                </Button>
                <Link to="/login" className="block">
                  <Button variant="ghost" className="w-full" data-testid="back-to-login-link">
                    <ArrowLeft className="h-4 w-4 mr-2" />
                    Back to Login
                  </Button>
                </Link>
              </form>
            )}
          </CardContent>
        </Card>
        <p className="text-center text-xs text-muted-foreground mt-6">
          CMA Compliant • Electronic Single Window Ready • GRI 1-6 Classification
        </p>
      </div>
    </div>
  );
}
