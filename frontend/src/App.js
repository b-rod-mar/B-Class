import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { Toaster } from './components/ui/sonner';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import DashboardPage from './pages/DashboardPage';
import UploadPage from './pages/UploadPage';
import ClassificationResultPage from './pages/ClassificationResultPage';
import HistoryPage from './pages/HistoryPage';
import HSLibraryPage from './pages/HSLibraryPage';
import AlcoholCalculatorPage from './pages/AlcoholCalculatorPage';
import CMASearchPage from './pages/CMASearchPage';
import CustomsFormsPage from './pages/CustomsFormsPage';
import CountryCodesPage from './pages/CountryCodesPage';
import NotationsPage from './pages/NotationsPage';
import TariffsDutiesPage from './pages/TariffsDutiesPage';
import VehicleCalculatorPage from './pages/VehicleCalculatorPage';
import Layout from './components/Layout';
import './App.css';

const ProtectedRoute = ({ children }) => {
  const { isAuthenticated, loading } = useAuth();
  
  if (loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="animate-pulse text-muted-foreground">Loading...</div>
      </div>
    );
  }
  
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }
  
  return children;
};

const PublicRoute = ({ children }) => {
  const { isAuthenticated, loading } = useAuth();
  
  if (loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="animate-pulse text-muted-foreground">Loading...</div>
      </div>
    );
  }
  
  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />;
  }
  
  return children;
};

function AppRoutes() {
  return (
    <Routes>
      <Route path="/login" element={<PublicRoute><LoginPage /></PublicRoute>} />
      <Route path="/register" element={<PublicRoute><RegisterPage /></PublicRoute>} />
      <Route path="/" element={<ProtectedRoute><Layout /></ProtectedRoute>}>
        <Route index element={<Navigate to="/dashboard" replace />} />
        <Route path="dashboard" element={<DashboardPage />} />
        <Route path="upload" element={<UploadPage />} />
        <Route path="classification/:id" element={<ClassificationResultPage />} />
        <Route path="history" element={<HistoryPage />} />
        <Route path="hs-library" element={<HSLibraryPage />} />
        <Route path="alcohol-calculator" element={<AlcoholCalculatorPage />} />
        <Route path="cma-guide" element={<CMASearchPage />} />
        <Route path="customs-forms" element={<CustomsFormsPage />} />
        <Route path="country-codes" element={<CountryCodesPage />} />
        <Route path="notations" element={<NotationsPage />} />
        <Route path="tariffs" element={<TariffsDutiesPage />} />
        <Route path="vehicle-calculator" element={<VehicleCalculatorPage />} />
      </Route>
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  );
}

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppRoutes />
        <Toaster position="top-right" richColors />
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
