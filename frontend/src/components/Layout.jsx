import { Outlet, NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { 
  LayoutDashboard, 
  Upload, 
  History, 
  BookOpen, 
  LogOut, 
  Menu,
  X,
  ChevronRight,
  Anchor,
  Wine,
  Scale,
  FileText,
  Globe,
  StickyNote,
  Calculator,
  Car,
  User,
  Settings,
  ChevronDown
} from 'lucide-react';
import { Button } from './ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from './ui/dropdown-menu';
import { useState } from 'react';
import { cn } from '../lib/utils';
import ClassiChat from './ClassiChat';
import FeedbackDialog from './FeedbackDialog';
import DisclaimerBanner from './DisclaimerBanner';

const navItems = [
  { path: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { path: '/upload', label: 'Upload & Classify', icon: Upload },
  { path: '/alcohol-calculator', label: 'Alcohol Calculator', icon: Wine },
  { path: '/vehicle-calculator', label: 'Vehicle Calculator', icon: Car },
  { path: '/tariffs', label: 'Tariffs & Duties', icon: Calculator },
  { path: '/history', label: 'Classification History', icon: History },
  { path: '/hs-library', label: 'HS Code Library', icon: BookOpen },
  { path: '/cma-guide', label: 'CMA Reference', icon: Scale },
  { path: '/customs-forms', label: 'Customs Forms', icon: FileText },
  { path: '/country-codes', label: 'Country Codes', icon: Globe },
  { path: '/notations', label: 'My Notations', icon: StickyNote },
];

export default function Layout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <div className="min-h-screen bg-background">
      {/* Mobile header */}
      <header className="lg:hidden fixed top-0 left-0 right-0 z-50 bg-card border-b border-border px-4 py-3 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Anchor className="h-6 w-6 text-primary" />
          <span className="font-bold text-lg font-['Chivo']">Class-B Agent</span>
        </div>
        <Button 
          variant="ghost" 
          size="icon" 
          onClick={() => setSidebarOpen(!sidebarOpen)}
          data-testid="mobile-menu-toggle"
        >
          {sidebarOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
        </Button>
      </header>

      {/* Sidebar */}
      <aside 
        className={cn(
          "fixed inset-y-0 left-0 z-40 w-64 bg-card border-r border-border transform transition-transform duration-200 ease-in-out lg:translate-x-0",
          sidebarOpen ? "translate-x-0" : "-translate-x-full"
        )}
      >
        <div className="flex flex-col h-full">
          {/* Logo */}
          <div className="p-6 border-b border-border hidden lg:block">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
                <Anchor className="h-6 w-6 text-primary" />
              </div>
              <div>
                <h1 className="font-bold text-lg font-['Chivo'] tracking-tight">Class-B Agent</h1>
                <p className="text-xs text-muted-foreground">Bahamas HS Classification</p>
              </div>
            </div>
          </div>

          {/* Navigation */}
          <nav className="flex-1 p-4 pt-20 lg:pt-4 space-y-1 overflow-y-auto">
            {navItems.map((item) => (
              <NavLink
                key={item.path}
                to={item.path}
                onClick={() => setSidebarOpen(false)}
                className={({ isActive }) => cn(
                  "nav-item group",
                  isActive && "active"
                )}
                data-testid={`nav-${item.path.slice(1)}`}
              >
                <item.icon className="h-5 w-5" />
                <span className="flex-1">{item.label}</span>
                <ChevronRight className="h-4 w-4 opacity-0 group-hover:opacity-100 transition-opacity" />
              </NavLink>
            ))}
          </nav>

          {/* User section - fixed at bottom */}
          <div className="flex-shrink-0 p-4 border-t border-border">
            <div className="flex items-center gap-3 mb-3">
              <div className="w-10 h-10 rounded-full bg-secondary flex items-center justify-center">
                <span className="text-sm font-medium">
                  {user?.name?.charAt(0).toUpperCase() || 'U'}
                </span>
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium truncate">{user?.name || 'User'}</p>
                <p className="text-xs text-muted-foreground truncate">{user?.email}</p>
              </div>
            </div>
            <div className="space-y-2">
              <FeedbackDialog />
              <Button 
                variant="ghost" 
                className="w-full justify-start text-muted-foreground hover:text-destructive"
                onClick={handleLogout}
                data-testid="logout-btn"
              >
                <LogOut className="h-4 w-4 mr-2" />
                Sign Out
              </Button>
            </div>
          </div>
          
          {/* Disclaimer - fixed at very bottom */}
          <DisclaimerBanner />
        </div>
      </aside>

      {/* Mobile overlay */}
      {sidebarOpen && (
        <div 
          className="fixed inset-0 bg-black/50 z-30 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Main content */}
      <main className="lg:ml-64 min-h-screen pt-16 lg:pt-0">
        <div className="p-6 lg:p-8">
          <Outlet />
        </div>
      </main>

      {/* Noise overlay */}
      <div className="fixed inset-0 noise-overlay z-40 pointer-events-none" />

      {/* Classi Chat Widget */}
      <ClassiChat />
    </div>
  );
}
