import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { toast } from 'sonner';
import { Anchor, Loader2, Shield, Lock, AlertTriangle, CheckCircle } from 'lucide-react';

export default function SetupAccountPage() {
  const { api, logout } = useAuth();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    new_password: '',
    confirm_password: '',
    secret_code: '',
    confirm_secret_code: ''
  });

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    // Validate password
    if (formData.new_password !== formData.confirm_password) {
      toast.error('Passwords do not match');
      return;
    }
    if (formData.new_password.length < 6) {
      toast.error('Password must be at least 6 characters');
      return;
    }
    
    // Validate secret code
    if (!formData.secret_code || formData.secret_code.length < 4 || formData.secret_code.length > 6) {
      toast.error('Secret code must be 4-6 digits');
      return;
    }
    if (!/^\d+$/.test(formData.secret_code)) {
      toast.error('Secret code must contain only numbers');
      return;
    }
    if (formData.secret_code !== formData.confirm_secret_code) {
      toast.error('Secret codes do not match');
      return;
    }
    
    setLoading(true);
    
    try {
      await api.post('/auth/complete-setup', {
        new_password: formData.new_password,
        secret_code: formData.secret_code
      });
      toast.success('Account setup completed! Please log in with your new password.');
      logout();
      navigate('/login');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Setup failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen login-bg flex items-center justify-center p-4">
      <div className="w-full max-w-md animate-fade-in">
        <Card className="glass border-white/10">
          <CardHeader className="text-center pb-2">
            <div className="mx-auto w-14 h-14 rounded-xl bg-amber-500/10 flex items-center justify-center mb-4">
              <Shield className="h-8 w-8 text-amber-500" />
            </div>
            <CardTitle className="text-2xl font-bold font-['Chivo']">
              Complete Account Setup
            </CardTitle>
            <CardDescription className="text-muted-foreground">
              Set your new password and security code to continue
            </CardDescription>
          </CardHeader>
          <CardContent className="pt-4">
            <div className="p-3 bg-amber-500/10 border border-amber-500/20 rounded-lg mb-4">
              <div className="flex items-start gap-2">
                <AlertTriangle className="h-4 w-4 text-amber-400 mt-0.5 flex-shrink-0" />
                <p className="text-xs text-amber-400/80">
                  For security, you must change your password and set an Account Secret Code before proceeding.
                </p>
              </div>
            </div>
            
            <form onSubmit={handleSubmit} className="space-y-4">
              {/* Password Section */}
              <div className="space-y-3">
                <div className="flex items-center gap-2">
                  <Lock className="h-4 w-4 text-primary" />
                  <Label className="font-medium">New Password</Label>
                </div>
                <div className="space-y-2">
                  <Input
                    type="password"
                    placeholder="Enter new password"
                    value={formData.new_password}
                    onChange={(e) => setFormData({ ...formData, new_password: e.target.value })}
                    required
                    minLength={6}
                    data-testid="new-password-input"
                    className="bg-background/50"
                  />
                  <Input
                    type="password"
                    placeholder="Confirm new password"
                    value={formData.confirm_password}
                    onChange={(e) => setFormData({ ...formData, confirm_password: e.target.value })}
                    required
                    minLength={6}
                    data-testid="confirm-password-input"
                    className="bg-background/50"
                  />
                </div>
              </div>
              
              {/* Secret Code Section */}
              <div className="space-y-3">
                <div className="flex items-center gap-2">
                  <Shield className="h-4 w-4 text-amber-400" />
                  <Label className="font-medium">Account Secret Code (4-6 digits)</Label>
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <Input
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
                    data-testid="secret-code-input"
                    className="bg-background/50 font-mono tracking-widest"
                  />
                  <Input
                    type="password"
                    inputMode="numeric"
                    pattern="[0-9]*"
                    maxLength={6}
                    placeholder="Confirm"
                    value={formData.confirm_secret_code}
                    onChange={(e) => {
                      const val = e.target.value.replace(/\D/g, '').slice(0, 6);
                      setFormData({ ...formData, confirm_secret_code: val });
                    }}
                    required
                    data-testid="confirm-secret-input"
                    className="bg-background/50 font-mono tracking-widest"
                  />
                </div>
                <p className="text-xs text-muted-foreground">
                  Store this code securely. It&apos;s required for account recovery and security changes.
                </p>
              </div>
              
              <Button 
                type="submit" 
                className="w-full bg-primary text-primary-foreground hover:bg-primary/90 glow-teal"
                disabled={loading}
                data-testid="complete-setup-btn"
              >
                {loading ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <>
                    <CheckCircle className="h-4 w-4 mr-2" />
                    Complete Setup
                  </>
                )}
              </Button>
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
