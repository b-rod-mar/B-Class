import { useState } from 'react';
import { Link } from 'react-router-dom';
import axios from 'axios';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { toast } from 'sonner';
import { Anchor, Loader2, ArrowLeft, Mail, CheckCircle, Shield, Key } from 'lucide-react';

const API_URL = process.env.REACT_APP_BACKEND_URL;

export default function ForgotPasswordPage() {
  const [loading, setLoading] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [resetSuccess, setResetSuccess] = useState(false);
  const [email, setEmail] = useState('');
  
  // Secret code recovery form
  const [secretForm, setSecretForm] = useState({
    email: '',
    secret_code: '',
    new_password: '',
    confirm_password: ''
  });

  const handleEmailSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      await axios.post(`${API_URL}/api/auth/forgot-password`, { email });
      setSubmitted(true);
      toast.success('Password reset email sent!');
    } catch (error) {
      // Still show success to prevent email enumeration
      setSubmitted(true);
      toast.success('If an account exists, you will receive a reset link.');
    } finally {
      setLoading(false);
    }
  };

  const handleSecretCodeSubmit = async (e) => {
    e.preventDefault();
    
    if (secretForm.new_password !== secretForm.confirm_password) {
      toast.error('Passwords do not match');
      return;
    }
    if (secretForm.new_password.length < 6) {
      toast.error('Password must be at least 6 characters');
      return;
    }
    
    setLoading(true);
    
    try {
      await axios.post(`${API_URL}/api/auth/recover-with-code`, {
        email: secretForm.email,
        secret_code: secretForm.secret_code,
        new_password: secretForm.new_password
      });
      setResetSuccess(true);
      toast.success('Password reset successfully!');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Invalid email or secret code');
    } finally {
      setLoading(false);
    }
  };

  if (resetSuccess) {
    return (
      <div className="min-h-screen login-bg flex items-center justify-center p-4">
        <div className="w-full max-w-md animate-fade-in">
          <Card className="glass border-white/10">
            <CardHeader className="text-center pb-2">
              <div className="mx-auto w-14 h-14 rounded-xl bg-emerald-500/10 flex items-center justify-center mb-4">
                <CheckCircle className="h-8 w-8 text-emerald-500" />
              </div>
              <CardTitle className="text-2xl font-bold font-['Chivo']">
                Password Reset!
              </CardTitle>
              <CardDescription className="text-muted-foreground">
                Your password has been successfully reset
              </CardDescription>
            </CardHeader>
            <CardContent className="pt-4">
              <Link to="/login" className="block">
                <Button className="w-full bg-primary text-primary-foreground hover:bg-primary/90 glow-teal">
                  Go to Login
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
              {submitted ? 'Check Your Email' : 'Reset Password'}
            </CardTitle>
            <CardDescription className="text-muted-foreground">
              {submitted 
                ? 'We sent a password reset link to your email'
                : 'Choose how you want to recover your account'
              }
            </CardDescription>
          </CardHeader>
          <CardContent className="pt-4">
            {submitted ? (
              <div className="space-y-6 text-center">
                <div className="mx-auto w-16 h-16 rounded-full bg-emerald-500/10 flex items-center justify-center">
                  <CheckCircle className="h-8 w-8 text-emerald-500" />
                </div>
                <div className="space-y-2">
                  <p className="text-sm text-muted-foreground">
                    If an account exists for <span className="text-foreground font-medium">{email}</span>, 
                    you will receive an email with instructions to reset your password.
                  </p>
                  <p className="text-xs text-muted-foreground">
                    The link will expire in 1 hour.
                  </p>
                </div>
                <div className="space-y-2">
                  <Button
                    variant="outline"
                    className="w-full"
                    onClick={() => setSubmitted(false)}
                    data-testid="try-another-email-btn"
                  >
                    <Mail className="h-4 w-4 mr-2" />
                    Try Another Email
                  </Button>
                  <Link to="/login" className="block">
                    <Button variant="ghost" className="w-full" data-testid="back-to-login-btn">
                      <ArrowLeft className="h-4 w-4 mr-2" />
                      Back to Login
                    </Button>
                  </Link>
                </div>
              </div>
            ) : (
              <Tabs defaultValue="email" className="space-y-4">
                <TabsList className="grid w-full grid-cols-2">
                  <TabsTrigger value="email" className="flex items-center gap-2">
                    <Mail className="h-4 w-4" />
                    Email Link
                  </TabsTrigger>
                  <TabsTrigger value="secret" className="flex items-center gap-2">
                    <Key className="h-4 w-4" />
                    Secret Code
                  </TabsTrigger>
                </TabsList>
                
                <TabsContent value="email">
                  <form onSubmit={handleEmailSubmit} className="space-y-4">
                    <div className="space-y-2">
                      <Label htmlFor="email">Email Address</Label>
                      <Input
                        id="email"
                        type="email"
                        placeholder="you@company.com"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        required
                        data-testid="forgot-email-input"
                        className="bg-background/50"
                      />
                    </div>
                    <Button 
                      type="submit" 
                      className="w-full bg-primary text-primary-foreground hover:bg-primary/90 glow-teal"
                      disabled={loading}
                      data-testid="forgot-submit-btn"
                    >
                      {loading ? (
                        <Loader2 className="h-4 w-4 animate-spin" />
                      ) : (
                        <>
                          <Mail className="h-4 w-4 mr-2" />
                          Send Reset Link
                        </>
                      )}
                    </Button>
                  </form>
                </TabsContent>
                
                <TabsContent value="secret">
                  <form onSubmit={handleSecretCodeSubmit} className="space-y-4">
                    <div className="p-3 bg-amber-500/10 border border-amber-500/20 rounded-lg mb-4">
                      <div className="flex items-start gap-2">
                        <Shield className="h-4 w-4 text-amber-400 mt-0.5 flex-shrink-0" />
                        <p className="text-xs text-amber-400/80">
                          Use your Account Secret Code (4-6 digit code created during registration) to reset your password instantly.
                        </p>
                      </div>
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="secret-email">Email Address</Label>
                      <Input
                        id="secret-email"
                        type="email"
                        placeholder="you@company.com"
                        value={secretForm.email}
                        onChange={(e) => setSecretForm({ ...secretForm, email: e.target.value })}
                        required
                        data-testid="secret-email-input"
                        className="bg-background/50"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="secret-code">Account Secret Code</Label>
                      <Input
                        id="secret-code"
                        type="password"
                        inputMode="numeric"
                        maxLength={6}
                        placeholder="••••••"
                        value={secretForm.secret_code}
                        onChange={(e) => setSecretForm({ ...secretForm, secret_code: e.target.value.replace(/\D/g, '').slice(0, 6) })}
                        required
                        data-testid="secret-code-input"
                        className="bg-background/50 font-mono tracking-widest"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="new-password">New Password</Label>
                      <Input
                        id="new-password"
                        type="password"
                        placeholder="••••••••"
                        value={secretForm.new_password}
                        onChange={(e) => setSecretForm({ ...secretForm, new_password: e.target.value })}
                        required
                        minLength={6}
                        data-testid="new-password-input"
                        className="bg-background/50"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="confirm-password">Confirm Password</Label>
                      <Input
                        id="confirm-password"
                        type="password"
                        placeholder="••••••••"
                        value={secretForm.confirm_password}
                        onChange={(e) => setSecretForm({ ...secretForm, confirm_password: e.target.value })}
                        required
                        minLength={6}
                        data-testid="confirm-password-input"
                        className="bg-background/50"
                      />
                    </div>
                    <Button 
                      type="submit" 
                      className="w-full bg-primary text-primary-foreground hover:bg-primary/90 glow-teal"
                      disabled={loading}
                      data-testid="secret-submit-btn"
                    >
                      {loading ? (
                        <Loader2 className="h-4 w-4 animate-spin" />
                      ) : (
                        <>
                          <Key className="h-4 w-4 mr-2" />
                          Reset Password
                        </>
                      )}
                    </Button>
                  </form>
                </TabsContent>
                
                <Link to="/login" className="block pt-2">
                  <Button variant="ghost" className="w-full" data-testid="back-to-login-link">
                    <ArrowLeft className="h-4 w-4 mr-2" />
                    Back to Login
                  </Button>
                </Link>
              </Tabs>
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
