import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import "./App.css";
import Register from "./pages/auth/register";
import Login from "./pages/auth/login";
import ForgotPassword from "./pages/auth/forgot-password";
import ResetPassword from "./pages/auth/reset-password";
import { Dashboard } from "./pages/dashboard";
import { FuzzyMatching } from "./pages/fuzzy";
import { SubscriptionPage } from "./pages/subscription";
import { AuthProvider } from "./context/AuthContext";
import { ProtectedRoute } from "./components/auth/ProtectedRoute";
import AdminSubscriptionPlansPage from "./pages/admin/subscription-plans";

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/forgot-password" element={<ForgotPassword />} />
          <Route path="/reset-password" element={<ResetPassword />} />
          <Route path="/dashboard" element={
            <ProtectedRoute>
              <Dashboard />
            </ProtectedRoute>
          } />
          <Route path="/fuzzy" element={
            <ProtectedRoute>
              <FuzzyMatching />
            </ProtectedRoute>
          } />
          <Route path="/subscription" element={
            <ProtectedRoute>
              <SubscriptionPage />
            </ProtectedRoute>
          } />
          <Route path="/admin/plans" element={
            <ProtectedRoute requireAdmin>
              <AdminSubscriptionPlansPage />
            </ProtectedRoute>
          } />
          {/* Catch-all route */}
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
