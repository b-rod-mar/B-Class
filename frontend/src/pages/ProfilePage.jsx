import { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Separator } from '../components/ui/separator';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
  DialogDescription,
} from '../components/ui/dialog';
import { 
  User, 
  Mail, 
  Building2, 
  Lock, 
  Shield, 
  Loader2,
  Edit2,
  Save,
  AlertTriangle,
  CheckCircle,
  Calendar,
  Key
} from 'lucide-react';
import { toast } from 'sonner';
import { formatDate } from '../lib/utils';

export default function ProfilePage() {
  const { api, user: authUser } = useAuth();
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  
  // Dialog states
  const [editProfileOpen, setEditProfileOpen] = useState(false);
  const [editEmailOpen, setEditEmailOpen] = useState(false);
  const [editPasswordOpen, setEditPasswordOpen] = useState(false);
  const [editSecretOpen, setEditSecretOpen] = useState(false);
  
  // Form states
  const [profileForm, setProfileForm] = useState({ name: '', company: '', secret_code: '' });
  const [emailForm, setEmailForm] = useState({ new_email: '', secret_code: '' });
  const [passwordForm, setPasswordForm] = useState({ current_password: '', new_password: '', confirm_password: '', secret_code: '' });
  const [secretForm, setSecretForm] = useState({ current_secret: '', new_secret: '', confirm_secret: '' });

  useEffect(() => {
    fetchProfile();
  }, []);

  const fetchProfile = async () => {
    try {
      const response = await api.get('/auth/profile');
      setProfile(response.data);
      setProfileForm({ name: response.data.name || '', company: response.data.company || '', secret_code: '' });
    } catch (error) {
      toast.error('Failed to load profile');
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateProfile = async () => {
    if (!profileForm.secret_code) {
      toast.error('Account Secret Code is required');
      return;
    }
    
    setSaving(true);
    try {
      await api.put('/auth/profile', {
        name: profileForm.name,
        company: profileForm.company,
        secret_code: profileForm.secret_code
      });
      toast.success('Profile updated successfully');
      await fetchProfile();
      setEditProfileOpen(false);
      setProfileForm({ ...profileForm, secret_code: '' });
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to update profile');
    } finally {
      setSaving(false);
    }
  };

  const handleUpdateEmail = async () => {
    if (!emailForm.new_email || !emailForm.secret_code) {
      toast.error('All fields are required');
      return;
    }
    
    setSaving(true);
    try {
      const response = await api.put('/auth/email', emailForm);
      // Update token in localStorage
      localStorage.setItem('hs_token', response.data.token);
      toast.success('Email updated successfully');
      await fetchProfile();
      setEditEmailOpen(false);
      setEmailForm({ new_email: '', secret_code: '' });
      // Reload to refresh auth state
      window.location.reload();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to update email');
    } finally {
      setSaving(false);
    }
  };

  const handleUpdatePassword = async () => {
    if (!passwordForm.new_password || !passwordForm.secret_code) {
      toast.error('New password and Secret Code are required');
      return;
    }
    if (passwordForm.new_password !== passwordForm.confirm_password) {
      toast.error('Passwords do not match');
      return;
    }
    if (passwordForm.new_password.length < 6) {
      toast.error('Password must be at least 6 characters');
      return;
    }
    
    setSaving(true);
    try {
      await api.put('/auth/password', {
        current_password: passwordForm.current_password || undefined,
        new_password: passwordForm.new_password,
        secret_code: passwordForm.secret_code
      });
      toast.success('Password updated successfully');
      setEditPasswordOpen(false);
      setPasswordForm({ current_password: '', new_password: '', confirm_password: '', secret_code: '' });
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to update password');
    } finally {
      setSaving(false);
    }
  };

  const handleUpdateSecret = async () => {
    if (!secretForm.current_secret || !secretForm.new_secret) {
      toast.error('All fields are required');
      return;
    }
    if (secretForm.new_secret !== secretForm.confirm_secret) {
      toast.error('Secret codes do not match');
      return;
    }
    if (!/^\d{4,6}$/.test(secretForm.new_secret)) {
      toast.error('Secret code must be 4-6 digits');
      return;
    }
    
    setSaving(true);
    try {
      await api.put('/auth/secret-code', {
        current_secret: secretForm.current_secret,
        new_secret: secretForm.new_secret
      });
      toast.success('Account Secret Code updated successfully');
      setEditSecretOpen(false);
      setSecretForm({ current_secret: '', new_secret: '', confirm_secret: '' });
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to update secret code');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="text-muted-foreground animate-pulse">Loading profile...</div>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in max-w-3xl mx-auto" data-testid="profile-page">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold font-['Chivo'] tracking-tight flex items-center gap-3">
            <User className="h-8 w-8 text-primary" />
            My Profile
          </h1>
          <p className="text-muted-foreground mt-1">
            Manage your account information and security settings
          </p>
        </div>
      </div>

      {/* Profile Avatar Card */}
      <Card className="bg-gradient-to-br from-primary/10 to-primary/5 border-primary/20">
        <CardContent className="p-6">
          <div className="flex items-center gap-4">
            <div className="w-20 h-20 rounded-full bg-primary/20 flex items-center justify-center">
              <span className="text-3xl font-bold text-primary">
                {profile?.name?.charAt(0).toUpperCase() || 'U'}
              </span>
            </div>
            <div>
              <h2 className="text-2xl font-bold font-['Chivo']">{profile?.name || 'User'}</h2>
              <p className="text-muted-foreground">{profile?.email}</p>
              {profile?.company && (
                <p className="text-sm text-muted-foreground flex items-center gap-1 mt-1">
                  <Building2 className="h-3.5 w-3.5" />
                  {profile.company}
                </p>
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Account Information */}
      <Card>
        <CardHeader>
          <CardTitle className="font-['Chivo'] flex items-center gap-2">
            <User className="h-5 w-5 text-primary" />
            Account Information
          </CardTitle>
          <CardDescription>Your personal details and account settings</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-1">
              <p className="text-sm text-muted-foreground">Full Name</p>
              <p className="font-medium">{profile?.name || '-'}</p>
            </div>
            <div className="space-y-1">
              <p className="text-sm text-muted-foreground">Company</p>
              <p className="font-medium">{profile?.company || '-'}</p>
            </div>
            <div className="space-y-1">
              <p className="text-sm text-muted-foreground">Email Address</p>
              <p className="font-medium">{profile?.email}</p>
            </div>
            <div className="space-y-1">
              <p className="text-sm text-muted-foreground">Account Role</p>
              <p className="font-medium capitalize">{profile?.role || 'User'}</p>
            </div>
            <div className="space-y-1">
              <p className="text-sm text-muted-foreground">Member Since</p>
              <p className="font-medium flex items-center gap-1">
                <Calendar className="h-3.5 w-3.5" />
                {formatDate(profile?.created_at)}
              </p>
            </div>
          </div>
          <Separator className="my-4" />
          <Button 
            variant="outline" 
            onClick={() => {
              setProfileForm({ name: profile?.name || '', company: profile?.company || '', secret_code: '' });
              setEditProfileOpen(true);
            }}
            data-testid="edit-profile-btn"
          >
            <Edit2 className="h-4 w-4 mr-2" />
            Edit Profile
          </Button>
        </CardContent>
      </Card>

      {/* Security Settings */}
      <Card>
        <CardHeader>
          <CardTitle className="font-['Chivo'] flex items-center gap-2">
            <Shield className="h-5 w-5 text-primary" />
            Security Settings
          </CardTitle>
          <CardDescription>Manage your email, password, and account security</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Card className="bg-muted/30">
              <CardContent className="p-4">
                <div className="flex items-center gap-3 mb-3">
                  <div className="w-10 h-10 rounded-lg bg-blue-500/10 flex items-center justify-center">
                    <Mail className="h-5 w-5 text-blue-400" />
                  </div>
                  <div>
                    <p className="font-medium">Email Address</p>
                    <p className="text-xs text-muted-foreground">Update your email</p>
                  </div>
                </div>
                <Button 
                  variant="outline" 
                  size="sm" 
                  className="w-full"
                  onClick={() => setEditEmailOpen(true)}
                  data-testid="change-email-btn"
                >
                  Change Email
                </Button>
              </CardContent>
            </Card>

            <Card className="bg-muted/30">
              <CardContent className="p-4">
                <div className="flex items-center gap-3 mb-3">
                  <div className="w-10 h-10 rounded-lg bg-violet-500/10 flex items-center justify-center">
                    <Lock className="h-5 w-5 text-violet-400" />
                  </div>
                  <div>
                    <p className="font-medium">Password</p>
                    <p className="text-xs text-muted-foreground">Update password</p>
                  </div>
                </div>
                <Button 
                  variant="outline" 
                  size="sm" 
                  className="w-full"
                  onClick={() => setEditPasswordOpen(true)}
                  data-testid="change-password-btn"
                >
                  Change Password
                </Button>
              </CardContent>
            </Card>

            <Card className="bg-muted/30">
              <CardContent className="p-4">
                <div className="flex items-center gap-3 mb-3">
                  <div className="w-10 h-10 rounded-lg bg-amber-500/10 flex items-center justify-center">
                    <Key className="h-5 w-5 text-amber-400" />
                  </div>
                  <div>
                    <p className="font-medium">Secret Code</p>
                    <p className="text-xs text-muted-foreground">Update recovery code</p>
                  </div>
                </div>
                <Button 
                  variant="outline" 
                  size="sm" 
                  className="w-full"
                  onClick={() => setEditSecretOpen(true)}
                  data-testid="change-secret-btn"
                >
                  Change Code
                </Button>
              </CardContent>
            </Card>
          </div>
          
          <div className="p-3 bg-amber-500/10 border border-amber-500/20 rounded-lg">
            <div className="flex items-start gap-2">
              <AlertTriangle className="h-4 w-4 text-amber-400 mt-0.5 flex-shrink-0" />
              <p className="text-xs text-amber-400/80">
                All security changes require your Account Secret Code for verification. This is the 4-6 digit code you created during registration.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Edit Profile Dialog */}
      <Dialog open={editProfileOpen} onOpenChange={setEditProfileOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle className="font-['Chivo']">Edit Profile</DialogTitle>
            <DialogDescription>Update your personal information</DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="edit-name">Full Name</Label>
              <Input
                id="edit-name"
                value={profileForm.name}
                onChange={(e) => setProfileForm({ ...profileForm, name: e.target.value })}
                data-testid="edit-name-input"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="edit-company">Company</Label>
              <Input
                id="edit-company"
                value={profileForm.company}
                onChange={(e) => setProfileForm({ ...profileForm, company: e.target.value })}
                data-testid="edit-company-input"
              />
            </div>
            <Separator />
            <div className="space-y-2">
              <Label htmlFor="profile-secret" className="flex items-center gap-2">
                <Shield className="h-4 w-4 text-amber-400" />
                Account Secret Code *
              </Label>
              <Input
                id="profile-secret"
                type="password"
                inputMode="numeric"
                maxLength={6}
                placeholder="Enter your 4-6 digit code"
                value={profileForm.secret_code}
                onChange={(e) => setProfileForm({ ...profileForm, secret_code: e.target.value.replace(/\D/g, '').slice(0, 6) })}
                className="font-mono tracking-widest"
                data-testid="profile-secret-input"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setEditProfileOpen(false)}>Cancel</Button>
            <Button onClick={handleUpdateProfile} disabled={saving} data-testid="save-profile-btn">
              {saving ? <Loader2 className="h-4 w-4 animate-spin" /> : <><Save className="h-4 w-4 mr-2" />Save</>}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Edit Email Dialog */}
      <Dialog open={editEmailOpen} onOpenChange={setEditEmailOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle className="font-['Chivo']">Change Email Address</DialogTitle>
            <DialogDescription>You will need to log in again after changing your email</DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label>Current Email</Label>
              <p className="text-sm text-muted-foreground">{profile?.email}</p>
            </div>
            <div className="space-y-2">
              <Label htmlFor="new-email">New Email Address</Label>
              <Input
                id="new-email"
                type="email"
                placeholder="newemail@company.com"
                value={emailForm.new_email}
                onChange={(e) => setEmailForm({ ...emailForm, new_email: e.target.value })}
                data-testid="new-email-input"
              />
            </div>
            <Separator />
            <div className="space-y-2">
              <Label htmlFor="email-secret" className="flex items-center gap-2">
                <Shield className="h-4 w-4 text-amber-400" />
                Account Secret Code *
              </Label>
              <Input
                id="email-secret"
                type="password"
                inputMode="numeric"
                maxLength={6}
                placeholder="Enter your 4-6 digit code"
                value={emailForm.secret_code}
                onChange={(e) => setEmailForm({ ...emailForm, secret_code: e.target.value.replace(/\D/g, '').slice(0, 6) })}
                className="font-mono tracking-widest"
                data-testid="email-secret-input"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setEditEmailOpen(false)}>Cancel</Button>
            <Button onClick={handleUpdateEmail} disabled={saving} data-testid="save-email-btn">
              {saving ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Update Email'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Edit Password Dialog */}
      <Dialog open={editPasswordOpen} onOpenChange={setEditPasswordOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle className="font-['Chivo']">Change Password</DialogTitle>
            <DialogDescription>Create a new password for your account</DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="current-password">Current Password (Optional)</Label>
              <Input
                id="current-password"
                type="password"
                placeholder="••••••••"
                value={passwordForm.current_password}
                onChange={(e) => setPasswordForm({ ...passwordForm, current_password: e.target.value })}
                data-testid="current-password-input"
              />
              <p className="text-xs text-muted-foreground">Optional if using Secret Code</p>
            </div>
            <div className="space-y-2">
              <Label htmlFor="new-password">New Password *</Label>
              <Input
                id="new-password"
                type="password"
                placeholder="••••••••"
                value={passwordForm.new_password}
                onChange={(e) => setPasswordForm({ ...passwordForm, new_password: e.target.value })}
                data-testid="new-password-input"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="confirm-new-password">Confirm New Password *</Label>
              <Input
                id="confirm-new-password"
                type="password"
                placeholder="••••••••"
                value={passwordForm.confirm_password}
                onChange={(e) => setPasswordForm({ ...passwordForm, confirm_password: e.target.value })}
                data-testid="confirm-new-password-input"
              />
            </div>
            <Separator />
            <div className="space-y-2">
              <Label htmlFor="password-secret" className="flex items-center gap-2">
                <Shield className="h-4 w-4 text-amber-400" />
                Account Secret Code *
              </Label>
              <Input
                id="password-secret"
                type="password"
                inputMode="numeric"
                maxLength={6}
                placeholder="Enter your 4-6 digit code"
                value={passwordForm.secret_code}
                onChange={(e) => setPasswordForm({ ...passwordForm, secret_code: e.target.value.replace(/\D/g, '').slice(0, 6) })}
                className="font-mono tracking-widest"
                data-testid="password-secret-input"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setEditPasswordOpen(false)}>Cancel</Button>
            <Button onClick={handleUpdatePassword} disabled={saving} data-testid="save-password-btn">
              {saving ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Update Password'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Edit Secret Code Dialog */}
      <Dialog open={editSecretOpen} onOpenChange={setEditSecretOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle className="font-['Chivo']">Change Account Secret Code</DialogTitle>
            <DialogDescription>Update your 4-6 digit recovery code</DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="current-secret">Current Secret Code *</Label>
              <Input
                id="current-secret"
                type="password"
                inputMode="numeric"
                maxLength={6}
                placeholder="••••••"
                value={secretForm.current_secret}
                onChange={(e) => setSecretForm({ ...secretForm, current_secret: e.target.value.replace(/\D/g, '').slice(0, 6) })}
                className="font-mono tracking-widest"
                data-testid="current-secret-input"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="new-secret">New Secret Code * (4-6 digits)</Label>
              <Input
                id="new-secret"
                type="password"
                inputMode="numeric"
                maxLength={6}
                placeholder="••••••"
                value={secretForm.new_secret}
                onChange={(e) => setSecretForm({ ...secretForm, new_secret: e.target.value.replace(/\D/g, '').slice(0, 6) })}
                className="font-mono tracking-widest"
                data-testid="new-secret-input"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="confirm-secret">Confirm New Secret Code *</Label>
              <Input
                id="confirm-secret"
                type="password"
                inputMode="numeric"
                maxLength={6}
                placeholder="••••••"
                value={secretForm.confirm_secret}
                onChange={(e) => setSecretForm({ ...secretForm, confirm_secret: e.target.value.replace(/\D/g, '').slice(0, 6) })}
                className="font-mono tracking-widest"
                data-testid="confirm-secret-input"
              />
            </div>
            <div className="p-3 bg-amber-500/10 border border-amber-500/20 rounded-lg">
              <div className="flex items-start gap-2">
                <AlertTriangle className="h-4 w-4 text-amber-400 mt-0.5 flex-shrink-0" />
                <p className="text-xs text-amber-400/80">
                  Store your new secret code securely. It's required for all account security changes and cannot be retrieved if lost.
                </p>
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setEditSecretOpen(false)}>Cancel</Button>
            <Button onClick={handleUpdateSecret} disabled={saving} data-testid="save-secret-btn">
              {saving ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Update Secret Code'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
