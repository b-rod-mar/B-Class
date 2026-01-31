import { useState } from 'react';
import { Link } from 'react-router-dom';
import axios from 'axios';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { toast } from 'sonner';
import { Anchor, Loader2, ArrowLeft, Mail, CheckCircle } from 'lucide-react';

const API_URL = process.env.REACT_APP_BACKEND_URL;

export default function ForgotPasswordPage() {
  const [loading, setLoading] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [email, setEmail] = useState('');

  const handleSubmit = async (e) => {
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

  return (
    <div className="min-h-screen login-bg flex items-center justify-center p-4">
      <div className="w-full max-w-md animate-fade-in">
        <Card className="glass border-white/10">
          <CardHeader className="text-center pb-2">
            <div className="mx-auto w-14 h-14 rounded-xl bg-primary/10 flex items-center justify-center mb-4 glow-teal">
              <Anchor className="h-8 w-8 text-primary" />
            </div>
            <CardTitle className="text-2xl font-bold font-['Chivo']">
              {submitted ? 'Check Your Email' : 'Forgot Password'}
            </CardTitle>
            <CardDescription className="text-muted-foreground">
              {submitted 
                ? 'We sent a password reset link to your email'
                : 'Enter your email to receive a password reset link'
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
              <form onSubmit={handleSubmit} className="space-y-4">
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
