import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { toast } from 'sonner';
import { Anchor, Loader2, ArrowRight, AlertTriangle, Shield } from 'lucide-react';

export default function RegisterPage() {
  const { register } = useAuth();
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    password: '',
    company: '',
    secret_code: '',
    confirm_secret_code: ''
  });

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    // Validate secret code
    if (!formData.secret_code || formData.secret_code.length < 4 || formData.secret_code.length > 6) {
      toast.error('Account Secret Code must be 4-6 digits');
      return;
    }
    if (!/^\d+$/.test(formData.secret_code)) {
      toast.error('Account Secret Code must contain only numbers');
      return;
    }
    if (formData.secret_code !== formData.confirm_secret_code) {
      toast.error('Secret codes do not match');
      return;
    }
    
    setLoading(true);
    
    try {
      await register(formData.name, formData.email, formData.password, formData.company, formData.secret_code);
      toast.success('Account created successfully!');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Registration failed');
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
              Create Account
            </CardTitle>
            <CardDescription className="text-muted-foreground">
              Start classifying imports today
            </CardDescription>
          </CardHeader>
          <CardContent className="pt-4">
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="name">Full Name</Label>
                <Input
                  id="name"
                  type="text"
                  placeholder="John Smith"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  required
                  data-testid="register-name-input"
                  className="bg-background/50"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="email">Email Address</Label>
                <Input
                  id="email"
                  type="email"
                  placeholder="you@company.com"
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  required
                  data-testid="register-email-input"
                  className="bg-background/50"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="company">Company (Optional)</Label>
                <Input
                  id="company"
                  type="text"
                  placeholder="Bahamas Freight Co."
                  value={formData.company}
                  onChange={(e) => setFormData({ ...formData, company: e.target.value })}
                  data-testid="register-company-input"
                  className="bg-background/50"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="password">Password</Label>
                <Input
                  id="password"
                  type="password"
                  placeholder="••••••••"
                  value={formData.password}
                  onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                  required
                  minLength={6}
                  data-testid="register-password-input"
                  className="bg-background/50"
                />
              </div>
              
              {/* Account Secret Code Section */}
              <div className="p-3 bg-amber-500/10 border border-amber-500/20 rounded-lg space-y-3">
                <div className="flex items-start gap-2">
                  <Shield className="h-4 w-4 text-amber-400 mt-0.5 flex-shrink-0" />
                  <div>
                    <p className="text-sm font-medium text-amber-400">Account Secret Code</p>
                    <p className="text-xs text-amber-400/70">Required for account recovery & security changes</p>
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div className="space-y-1">
                    <Label htmlFor="secret_code" className="text-xs">Secret Code (4-6 digits)</Label>
                    <Input
                      id="secret_code"
                      type="password"
                      inputMode="numeric"
                      pattern="[0-9]*"
                      maxLength={6}
                      placeholder="••••••"
                      value={formData.secret_code}
                      onChange={(e) => {
                        const val = e.target.value.replace(/\D/g, '').slice(0, 6);
                        setFormData({ ...formData, secret_code: val });
                      }}
                      required
                      data-testid="register-secret-code-input"
                      className="bg-background/50 font-mono tracking-widest"
                    />
                  </div>
                  <div className="space-y-1">
                    <Label htmlFor="confirm_secret_code" className="text-xs">Confirm Code</Label>
                    <Input
                      id="confirm_secret_code"
                      type="password"
                      inputMode="numeric"
                      pattern="[0-9]*"
                      maxLength={6}
                      placeholder="••••••"
                      value={formData.confirm_secret_code}
                      onChange={(e) => {
                        const val = e.target.value.replace(/\D/g, '').slice(0, 6);
                        setFormData({ ...formData, confirm_secret_code: val });
                      }}
                      required
                      data-testid="register-confirm-secret-input"
                      className="bg-background/50 font-mono tracking-widest"
                    />
                  </div>
                </div>
                <div className="flex items-start gap-2 pt-1">
                  <AlertTriangle className="h-3.5 w-3.5 text-amber-400 mt-0.5 flex-shrink-0" />
                  <p className="text-[10px] text-amber-400/80 leading-tight">
                    Store this code securely. It's required to update your account information or recover access. We cannot retrieve it if lost.
                  </p>
                </div>
              </div>
              
              <Button 
                type="submit" 
                className="w-full bg-primary text-primary-foreground hover:bg-primary/90 glow-teal"
                disabled={loading}
                data-testid="register-submit-btn"
              >
                {loading ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <>
                    Create Account
                    <ArrowRight className="h-4 w-4 ml-2" />
                  </>
                )}
              </Button>
            </form>
            <div className="mt-6 text-center text-sm text-muted-foreground">
              Already have an account?{' '}
              <Link 
                to="/login" 
                className="text-primary hover:underline font-medium"
                data-testid="login-link"
              >
                Sign In
              </Link>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
