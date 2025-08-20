import { createContext, useContext, useEffect, useState } from "react";
import { ApiService, User, LicenseInfo } from "@/lib/api";

interface AuthContextType {
    user: User | null;
    license: LicenseInfo | null;
    loading: boolean;
    login: (email: string, password: string) => Promise<void>;
    register: (userData: {
        email: string;
        username: string;
        password: string;
        first_name?: string;
        last_name?: string;
    }) => Promise<void>;
    logout: () => void;
    refreshUserData: () => Promise<void>;
    isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function useAuth() {
    const context = useContext(AuthContext);
    if (context === undefined) {
        throw new Error("useAuth must be used within an AuthProvider");
    }
    return context;
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
    const [user, setUser] = useState<User | null>(null);
    const [license, setLicense] = useState<LicenseInfo | null>(null);
    const [loading, setLoading] = useState(true);

    const refreshUserData = async () => {
        try {
            const userData = await ApiService.getCurrentUser();
            setUser(userData);

            const licenseData = await ApiService.getLicenseInfo();
            setLicense(licenseData);
        } catch (error) {
            console.error("Error refreshing user data:", error);
            setUser(null);
            setLicense(null);
        }
    };

    const login = async (email: string, password: string) => {
        setLoading(true);
        try {
            await ApiService.login({ email, password });
            await refreshUserData();
        } finally {
            setLoading(false);
        }
    };

    const register = async (userData: {
        email: string;
        username: string;
        password: string;
        first_name?: string;
        last_name?: string;
    }) => {
        setLoading(true);
        try {
            await ApiService.register(userData);
            // After registration, user needs to login
        } finally {
            setLoading(false);
        }
    };

    const logout = () => {
        ApiService.logout();
        setUser(null);
        setLicense(null);
    };

    // Check if user is authenticated on app load
    useEffect(() => {
        const checkAuth = async () => {
            const token = localStorage.getItem('auth_token');
            if (token) {
                try {
                    await refreshUserData();
                } catch (error) {
                    // Token might be expired, clear it
                    localStorage.removeItem('auth_token');
                }
            }
            setLoading(false);
        };

        checkAuth();
    }, []);

    const value: AuthContextType = {
        user,
        license,
        loading,
        login,
        register,
        logout,
        refreshUserData,
        isAuthenticated: !!user,
    };

    return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
