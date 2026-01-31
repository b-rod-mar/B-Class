import { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Badge } from '../components/ui/badge';
import { Separator } from '../components/ui/separator';
import { Textarea } from '../components/ui/textarea';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
  DialogDescription,
} from '../components/ui/dialog';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../components/ui/select';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '../components/ui/table';
import { 
  Shield, 
  Users, 
  Bell, 
  Settings, 
  Download,
  Plus,
  Edit2,
  Trash2,
  UserPlus,
  UserX,
  UserCheck,
  Search,
  FileSpreadsheet,
  Loader2,
  AlertTriangle,
  CheckCircle,
  Info,
  Send,
  History,
  RefreshCw
} from 'lucide-react';
import { toast } from 'sonner';
import { formatDate } from '../lib/utils';

export default function AdminDashboardPage() {
  const { api, user } = useAuth();
  const [stats, setStats] = useState(null);
  const [users, setUsers] = useState([]);
  const [notifications, setNotifications] = useState([]);
  const [auditLogs, setAuditLogs] = useState([]);
  const [settings, setSettings] = useState({ terms_of_use: '', disclaimer_text: '', weekly_email_enabled: true, classi_knowledge: '' });
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  
  // Dialog states
  const [createUserOpen, setCreateUserOpen] = useState(false);
  const [editUserOpen, setEditUserOpen] = useState(false);
  const [broadcastOpen, setBroadcastOpen] = useState(false);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [deleteUserOpen, setDeleteUserOpen] = useState(false);
  const [selectedUser, setSelectedUser] = useState(null);
  const [saving, setSaving] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [deleteConfirmText, setDeleteConfirmText] = useState('');

  // Form states
  const [newUser, setNewUser] = useState({ email: '', name: '', company: '', password: '', role: 'user', admin_access_level: '' });
  const [notification, setNotification] = useState({ title: '', message: '', notification_type: 'info' });

  useEffect(() => {
    loadAdminData();
  }, []);

  const loadAdminData = async () => {
    setLoading(true);
    try {
      const [statsRes, usersRes, notifRes, logsRes, settingsRes] = await Promise.all([
        api.get('/admin/stats'),
        api.get('/admin/users'),
        api.get('/admin/notifications'),
        api.get('/admin/audit-logs?limit=50'),
        api.get('/admin/settings')
      ]);
      setStats(statsRes.data);
      setUsers(usersRes.data);
      setNotifications(notifRes.data);
      setAuditLogs(logsRes.data);
      setSettings(settingsRes.data);
    } catch (error) {
      toast.error('Failed to load admin data');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateUser = async () => {
    if (!newUser.email || !newUser.name || !newUser.password) {
      toast.error('Please fill all required fields');
      return;
    }
    setSaving(true);
    try {
      await api.post('/admin/users/create', {
        ...newUser,
        admin_access_level: newUser.role !== 'user' ? newUser.admin_access_level || 'view_only' : undefined
      });
      toast.success('User created successfully');
      setCreateUserOpen(false);
      setNewUser({ email: '', name: '', company: '', password: '', role: 'user', admin_access_level: '' });
      loadAdminData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to create user');
    } finally {
      setSaving(false);
    }
  };

  const handleUpdateUser = async () => {
    if (!selectedUser) return;
    setSaving(true);
    try {
      await api.put(`/admin/users/${selectedUser.id}`, {
        name: selectedUser.name,
        email: selectedUser.email,
        company: selectedUser.company,
        role: selectedUser.role,
        admin_access_level: selectedUser.admin_access_level,
        account_status: selectedUser.account_status
      });
      toast.success('User updated successfully');
      setEditUserOpen(false);
      loadAdminData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to update user');
    } finally {
      setSaving(false);
    }
  };

  const handleSuspendUser = async (userId) => {
    try {
      await api.post(`/admin/users/${userId}/suspend`);
      toast.success('User suspended');
      loadAdminData();
    } catch (error) {
      toast.error('Failed to suspend user');
    }
  };

  const handleReactivateUser = async (userId) => {
    try {
      await api.post(`/admin/users/${userId}/reactivate`);
      toast.success('User reactivated');
      loadAdminData();
    } catch (error) {
      toast.error('Failed to reactivate user');
    }
  };

  const handlePermanentDeleteUser = async () => {
    if (!selectedUser) return;
    if (deleteConfirmText !== 'DELETE') {
      toast.error('Please type DELETE to confirm');
      return;
    }
    
    setDeleting(true);
    try {
      const response = await api.delete(`/admin/users/${selectedUser.id}/permanent`);
      toast.success(`User ${selectedUser.email} and all their data permanently deleted`);
      setDeleteUserOpen(false);
      setSelectedUser(null);
      setDeleteConfirmText('');
      loadAdminData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to delete user');
    } finally {
      setDeleting(false);
    }
  };

  const handleBroadcast = async () => {
    if (!notification.title || !notification.message) {
      toast.error('Please fill all fields');
      return;
    }
    setSaving(true);
    try {
      await api.post('/admin/notifications/broadcast', notification);
      toast.success('Notification broadcast sent!');
      setBroadcastOpen(false);
      setNotification({ title: '', message: '', notification_type: 'info' });
      loadAdminData();
    } catch (error) {
      toast.error('Failed to broadcast notification');
    } finally {
      setSaving(false);
    }
  };

  const handleUpdateSettings = async () => {
    setSaving(true);
    try {
      await api.put('/admin/settings', settings);
      toast.success('Settings updated successfully');
      setSettingsOpen(false);
    } catch (error) {
      toast.error('Failed to update settings');
    } finally {
      setSaving(false);
    }
  };

  const handleExportUsers = async () => {
    try {
      const response = await api.get('/admin/users/export', { responseType: 'blob' });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `users_export_${new Date().toISOString().split('T')[0]}.xlsx`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      toast.success('Users exported!');
    } catch (error) {
      toast.error('Export failed');
    }
  };

  const filteredUsers = users.filter(u => 
    u.name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    u.email?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    u.company?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const getStatusBadge = (status) => {
    switch (status) {
      case 'suspended': return <Badge className="bg-amber-500/20 text-amber-400">Suspended</Badge>;
      case 'deactivated': return <Badge className="bg-rose-500/20 text-rose-400">Deactivated</Badge>;
      default: return <Badge className="bg-emerald-500/20 text-emerald-400">Active</Badge>;
    }
  };

  const getRoleBadge = (role) => {
    switch (role) {
      case 'super_admin': return <Badge className="bg-purple-500/20 text-purple-400">Super Admin</Badge>;
      case 'admin': return <Badge className="bg-blue-500/20 text-blue-400">Admin</Badge>;
      default: return <Badge variant="outline">User</Badge>;
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="text-muted-foreground animate-pulse">Loading admin dashboard...</div>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in" data-testid="admin-dashboard">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold font-['Chivo'] tracking-tight flex items-center gap-3">
            <Shield className="h-8 w-8 text-purple-500" />
            Admin Dashboard
          </h1>
          <p className="text-muted-foreground mt-1">
            System administration and user management
          </p>
        </div>
        <Button onClick={() => loadAdminData()} variant="outline" data-testid="refresh-btn">
          <RefreshCw className="h-4 w-4 mr-2" />
          Refresh
        </Button>
      </div>

      {/* Stats Cards */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          <Card className="bg-card/50">
            <CardContent className="p-4 text-center">
              <p className="text-2xl font-bold font-['Chivo'] text-foreground">{stats.users.total}</p>
              <p className="text-xs text-muted-foreground uppercase tracking-wider">Total Users</p>
            </CardContent>
          </Card>
          <Card className="bg-emerald-500/10 border-emerald-500/20">
            <CardContent className="p-4 text-center">
              <p className="text-2xl font-bold font-['Chivo'] text-emerald-400">{stats.users.active}</p>
              <p className="text-xs text-emerald-400/70 uppercase tracking-wider">Active</p>
            </CardContent>
          </Card>
          <Card className="bg-purple-500/10 border-purple-500/20">
            <CardContent className="p-4 text-center">
              <p className="text-2xl font-bold font-['Chivo'] text-purple-400">{stats.users.admins}</p>
              <p className="text-xs text-purple-400/70 uppercase tracking-wider">Admins</p>
            </CardContent>
          </Card>
          <Card className="bg-blue-500/10 border-blue-500/20">
            <CardContent className="p-4 text-center">
              <p className="text-2xl font-bold font-['Chivo'] text-blue-400">{stats.users.new_this_week}</p>
              <p className="text-xs text-blue-400/70 uppercase tracking-wider">New This Week</p>
            </CardContent>
          </Card>
          <Card className="bg-amber-500/10 border-amber-500/20">
            <CardContent className="p-4 text-center">
              <p className="text-2xl font-bold font-['Chivo'] text-amber-400">{stats.notifications.active}</p>
              <p className="text-xs text-amber-400/70 uppercase tracking-wider">Active Alerts</p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Tabs */}
      <Tabs defaultValue="users" className="space-y-4">
        <TabsList>
          <TabsTrigger value="users" className="flex items-center gap-2">
            <Users className="h-4 w-4" />
            User Management
          </TabsTrigger>
          <TabsTrigger value="notifications" className="flex items-center gap-2">
            <Bell className="h-4 w-4" />
            Notifications
          </TabsTrigger>
          <TabsTrigger value="settings" className="flex items-center gap-2">
            <Settings className="h-4 w-4" />
            Settings
          </TabsTrigger>
          <TabsTrigger value="audit" className="flex items-center gap-2">
            <History className="h-4 w-4" />
            Audit Logs
          </TabsTrigger>
        </TabsList>

        {/* Users Tab */}
        <TabsContent value="users" className="space-y-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle>User Accounts</CardTitle>
                <CardDescription>Manage all user accounts</CardDescription>
              </div>
              <div className="flex gap-2">
                <Button variant="outline" size="sm" onClick={handleExportUsers} data-testid="export-users-btn">
                  <Download className="h-4 w-4 mr-2" />
                  Export
                </Button>
                <Button size="sm" onClick={() => setCreateUserOpen(true)} data-testid="create-user-btn">
                  <UserPlus className="h-4 w-4 mr-2" />
                  Add User
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              <div className="flex items-center gap-4 mb-4">
                <div className="relative flex-1 max-w-sm">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                  <Input
                    placeholder="Search users..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="pl-9"
                    data-testid="search-users-input"
                  />
                </div>
              </div>
              <div className="rounded-md border max-h-[400px] overflow-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Name</TableHead>
                      <TableHead>Email</TableHead>
                      <TableHead>Role</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Created</TableHead>
                      <TableHead>Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {filteredUsers.map((u) => (
                      <TableRow key={u.id}>
                        <TableCell className="font-medium">{u.name}</TableCell>
                        <TableCell className="text-muted-foreground">{u.email}</TableCell>
                        <TableCell>{getRoleBadge(u.role)}</TableCell>
                        <TableCell>{getStatusBadge(u.account_status)}</TableCell>
                        <TableCell className="text-sm text-muted-foreground">{formatDate(u.created_at)}</TableCell>
                        <TableCell>
                          <div className="flex gap-1">
                            <Button 
                              variant="ghost" 
                              size="icon"
                              onClick={() => { setSelectedUser(u); setEditUserOpen(true); }}
                              data-testid={`edit-user-${u.id}`}
                            >
                              <Edit2 className="h-4 w-4" />
                            </Button>
                            {u.account_status === 'active' ? (
                              <Button 
                                variant="ghost" 
                                size="icon"
                                onClick={() => handleSuspendUser(u.id)}
                                className="text-amber-500 hover:text-amber-400"
                                data-testid={`suspend-user-${u.id}`}
                              >
                                <UserX className="h-4 w-4" />
                              </Button>
                            ) : (
                              <Button 
                                variant="ghost" 
                                size="icon"
                                onClick={() => handleReactivateUser(u.id)}
                                className="text-emerald-500 hover:text-emerald-400"
                                data-testid={`reactivate-user-${u.id}`}
                              >
                                <UserCheck className="h-4 w-4" />
                              </Button>
                            )}
                          </div>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Notifications Tab */}
        <TabsContent value="notifications" className="space-y-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle>Broadcast Notifications</CardTitle>
                <CardDescription>Send system-wide notifications to all users</CardDescription>
              </div>
              <Button size="sm" onClick={() => setBroadcastOpen(true)} data-testid="broadcast-btn">
                <Send className="h-4 w-4 mr-2" />
                New Broadcast
              </Button>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {notifications.length === 0 ? (
                  <p className="text-muted-foreground text-center py-8">No notifications yet</p>
                ) : (
                  notifications.map((n) => (
                    <Card key={n.id} className={`${n.is_active ? '' : 'opacity-50'}`}>
                      <CardContent className="p-4">
                        <div className="flex items-start justify-between">
                          <div className="flex items-start gap-3">
                            {n.notification_type === 'urgent' && <AlertTriangle className="h-5 w-5 text-rose-400 mt-0.5" />}
                            {n.notification_type === 'warning' && <AlertTriangle className="h-5 w-5 text-amber-400 mt-0.5" />}
                            {n.notification_type === 'info' && <Info className="h-5 w-5 text-blue-400 mt-0.5" />}
                            {n.notification_type === 'update' && <CheckCircle className="h-5 w-5 text-emerald-400 mt-0.5" />}
                            <div>
                              <p className="font-medium">{n.title}</p>
                              <p className="text-sm text-muted-foreground">{n.message}</p>
                              <p className="text-xs text-muted-foreground mt-1">
                                By {n.created_by_name} • {formatDate(n.created_at)}
                              </p>
                            </div>
                          </div>
                          <Badge variant={n.is_active ? 'default' : 'outline'}>
                            {n.is_active ? 'Active' : 'Inactive'}
                          </Badge>
                        </div>
                      </CardContent>
                    </Card>
                  ))
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Settings Tab */}
        <TabsContent value="settings" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>System Settings</CardTitle>
              <CardDescription>Configure global application settings</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label>Terms of Use</Label>
                <Textarea 
                  value={settings.terms_of_use || ''} 
                  onChange={(e) => setSettings({ ...settings, terms_of_use: e.target.value })}
                  placeholder="Enter terms of use content..."
                  rows={6}
                  data-testid="terms-textarea"
                />
              </div>
              <div className="space-y-2">
                <Label>Disclaimer Text</Label>
                <Textarea 
                  value={settings.disclaimer_text || ''} 
                  onChange={(e) => setSettings({ ...settings, disclaimer_text: e.target.value })}
                  placeholder="Enter disclaimer text..."
                  rows={4}
                  data-testid="disclaimer-textarea"
                />
              </div>
              <Separator />
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium">Weekly Email Reports</p>
                  <p className="text-sm text-muted-foreground">Send weekly account creation logs</p>
                </div>
                <Button 
                  variant={settings.weekly_email_enabled ? 'default' : 'outline'}
                  onClick={() => setSettings({ ...settings, weekly_email_enabled: !settings.weekly_email_enabled })}
                  data-testid="weekly-email-toggle"
                >
                  {settings.weekly_email_enabled ? 'Enabled' : 'Disabled'}
                </Button>
              </div>
              <Button onClick={handleUpdateSettings} disabled={saving} className="w-full" data-testid="save-settings-btn">
                {saving ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : null}
                Save Settings
              </Button>
            </CardContent>
          </Card>

          {/* Classi AI Knowledge Card */}
          <Card className="border-purple-500/20">
            <CardHeader>
              <div className="flex items-center gap-3">
                <div className="h-10 w-10 rounded-full bg-gradient-to-br from-[#00778B] via-[#FFC72C] to-[#000] flex items-center justify-center">
                  <span className="text-white font-bold text-sm">C</span>
                </div>
                <div>
                  <CardTitle>Classi AI Knowledge Base</CardTitle>
                  <CardDescription>Add custom information for Classi to use when helping users</CardDescription>
                </div>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="p-3 bg-purple-500/10 border border-purple-500/20 rounded-lg">
                <p className="text-sm text-purple-300">
                  <Info className="h-4 w-4 inline mr-2" />
                  Any information added here will be included in Classi's knowledge when answering user questions. 
                  Use this to add updates about regulations, new procedures, or company-specific guidance.
                </p>
              </div>
              <div className="space-y-2">
                <Label>Additional Knowledge for Classi</Label>
                <Textarea 
                  value={settings.classi_knowledge || ''} 
                  onChange={(e) => setSettings({ ...settings, classi_knowledge: e.target.value })}
                  placeholder="Example: As of January 2026, the new EPA agreement affects duty rates on certain EU goods. Users should check form C-18 for EPA preferential treatment claims..."
                  rows={8}
                  className="font-mono text-sm"
                  data-testid="classi-knowledge-textarea"
                />
                <p className="text-xs text-muted-foreground">
                  Format tips: Use clear headings, bullet points, and specific details. This text is sent directly to the AI.
                </p>
              </div>
              <Button onClick={handleUpdateSettings} disabled={saving} className="w-full" data-testid="save-classi-knowledge-btn">
                {saving ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : null}
                Update Classi Knowledge
              </Button>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Audit Logs Tab */}
        <TabsContent value="audit" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Audit Logs</CardTitle>
              <CardDescription>Track all administrative actions</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="rounded-md border max-h-[500px] overflow-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Timestamp</TableHead>
                      <TableHead>Admin</TableHead>
                      <TableHead>Action</TableHead>
                      <TableHead>Description</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {auditLogs.map((log) => (
                      <TableRow key={log.id}>
                        <TableCell className="text-sm text-muted-foreground">{formatDate(log.timestamp)}</TableCell>
                        <TableCell className="font-medium">{log.admin_name}</TableCell>
                        <TableCell>
                          <Badge variant="outline">{log.action_type}</Badge>
                        </TableCell>
                        <TableCell className="text-sm max-w-[300px] truncate">{log.description}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Create User Dialog */}
      <Dialog open={createUserOpen} onOpenChange={setCreateUserOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Create New User</DialogTitle>
            <DialogDescription>Add a new user account to the system</DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Name *</Label>
                <Input 
                  value={newUser.name} 
                  onChange={(e) => setNewUser({ ...newUser, name: e.target.value })}
                  data-testid="new-user-name"
                />
              </div>
              <div className="space-y-2">
                <Label>Company</Label>
                <Input 
                  value={newUser.company} 
                  onChange={(e) => setNewUser({ ...newUser, company: e.target.value })}
                />
              </div>
            </div>
            <div className="space-y-2">
              <Label>Email *</Label>
              <Input 
                type="email"
                value={newUser.email} 
                onChange={(e) => setNewUser({ ...newUser, email: e.target.value })}
                data-testid="new-user-email"
              />
            </div>
            <div className="space-y-2">
              <Label>Password *</Label>
              <Input 
                type="password"
                value={newUser.password} 
                onChange={(e) => setNewUser({ ...newUser, password: e.target.value })}
                data-testid="new-user-password"
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Role</Label>
                <Select value={newUser.role} onValueChange={(v) => setNewUser({ ...newUser, role: v })}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="user">User</SelectItem>
                    <SelectItem value="admin">Admin</SelectItem>
                    <SelectItem value="super_admin">Super Admin</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              {newUser.role !== 'user' && (
                <div className="space-y-2">
                  <Label>Access Level</Label>
                  <Select value={newUser.admin_access_level} onValueChange={(v) => setNewUser({ ...newUser, admin_access_level: v })}>
                    <SelectTrigger>
                      <SelectValue placeholder="Select" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="full">Full Access</SelectItem>
                      <SelectItem value="broadcast_only">Broadcast Only</SelectItem>
                      <SelectItem value="view_only">View Only</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              )}
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setCreateUserOpen(false)}>Cancel</Button>
            <Button onClick={handleCreateUser} disabled={saving} data-testid="confirm-create-user">
              {saving ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <UserPlus className="h-4 w-4 mr-2" />}
              Create User
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Edit User Dialog */}
      <Dialog open={editUserOpen} onOpenChange={setEditUserOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Edit User</DialogTitle>
            <DialogDescription>Update user account details</DialogDescription>
          </DialogHeader>
          {selectedUser && (
            <div className="space-y-4 py-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Name</Label>
                  <Input 
                    value={selectedUser.name || ''} 
                    onChange={(e) => setSelectedUser({ ...selectedUser, name: e.target.value })}
                  />
                </div>
                <div className="space-y-2">
                  <Label>Company</Label>
                  <Input 
                    value={selectedUser.company || ''} 
                    onChange={(e) => setSelectedUser({ ...selectedUser, company: e.target.value })}
                  />
                </div>
              </div>
              <div className="space-y-2">
                <Label>Email</Label>
                <Input 
                  type="email"
                  value={selectedUser.email || ''} 
                  onChange={(e) => setSelectedUser({ ...selectedUser, email: e.target.value })}
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Role</Label>
                  <Select value={selectedUser.role} onValueChange={(v) => setSelectedUser({ ...selectedUser, role: v })}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="user">User</SelectItem>
                      <SelectItem value="admin">Admin</SelectItem>
                      <SelectItem value="super_admin">Super Admin</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Status</Label>
                  <Select value={selectedUser.account_status || 'active'} onValueChange={(v) => setSelectedUser({ ...selectedUser, account_status: v })}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="active">Active</SelectItem>
                      <SelectItem value="suspended">Suspended</SelectItem>
                      <SelectItem value="deactivated">Deactivated</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
            </div>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => setEditUserOpen(false)}>Cancel</Button>
            <Button onClick={handleUpdateUser} disabled={saving} data-testid="confirm-edit-user">
              {saving ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : null}
              Save Changes
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Broadcast Notification Dialog */}
      <Dialog open={broadcastOpen} onOpenChange={setBroadcastOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Broadcast Notification</DialogTitle>
            <DialogDescription>Send a notification to all users</DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label>Title</Label>
              <Input 
                value={notification.title} 
                onChange={(e) => setNotification({ ...notification, title: e.target.value })}
                placeholder="Notification title..."
                data-testid="notification-title"
              />
            </div>
            <div className="space-y-2">
              <Label>Message</Label>
              <Textarea 
                value={notification.message} 
                onChange={(e) => setNotification({ ...notification, message: e.target.value })}
                placeholder="Notification message..."
                rows={4}
                data-testid="notification-message"
              />
            </div>
            <div className="space-y-2">
              <Label>Type</Label>
              <Select value={notification.notification_type} onValueChange={(v) => setNotification({ ...notification, notification_type: v })}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="info">Info</SelectItem>
                  <SelectItem value="update">Update</SelectItem>
                  <SelectItem value="warning">Warning</SelectItem>
                  <SelectItem value="urgent">Urgent</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setBroadcastOpen(false)}>Cancel</Button>
            <Button onClick={handleBroadcast} disabled={saving} data-testid="send-broadcast">
              {saving ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <Send className="h-4 w-4 mr-2" />}
              Send Broadcast
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
