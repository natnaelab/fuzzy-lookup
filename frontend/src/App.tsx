import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import "./App.css";
import Register from "./pages/auth/register";
import Login from "./pages/auth/login";
import { Dashboard } from "./pages/dashboard";
import { FuzzyMatching } from "./pages/fuzzy";
import { SubscriptionPage } from "./pages/subscription";
import { AuthProvider } from "./context/AuthContext";
import { ProtectedRoute } from "./components/auth/ProtectedRoute";

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
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
          {/* Catch-all route */}
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
