import axios, { AxiosError } from 'axios';

// API Base URL
const API_BASE_URL = 'http://localhost:8000';

// Create axios instance
const api = axios.create({
    baseURL: API_BASE_URL,
    timeout: 30000,
});

// Types for API responses
export interface ApiResponse<T = any> {
    data: T;
    message?: string;
}

export interface ErrorResponse {
    detail: string;
    status_code: number;
}

export interface User {
    id: number;
    email: string;
    username: string;
    first_name?: string;
    last_name?: string;
    is_active: boolean;
    is_verified: boolean;
    created_at: string;
}

export interface LoginRequest {
    email: string;
    password: string;
}

export interface RegisterRequest {
    email: string;
    username: string;
    password: string;
    first_name?: string;
    last_name?: string;
}

export interface TokenResponse {
    access_token: string;
    token_type: string;
    expires_in: number;
}

export interface LicenseInfo {
    id: number;
    license_type: string;
    license_key?: string;
    is_active: boolean;
    max_file_size_mb: number;
    max_monthly_operations: number;
    current_month_operations: number;
    operations_remaining: number;
    is_expired: boolean;
    expires_at?: string;
    created_at: string;
}

export interface UserFile {
    id: number;
    original_filename: string;
    stored_filename: string;
    file_size_bytes: number;
    file_size_mb: number;
    file_type: string;
    upload_date: string;
    is_processed: boolean;
}

export interface FuzzyJob {
    id: number;
    job_type: string;
    status: string;
    created_at?: string;
    completed_at?: string;
    matches_count: number;
    threshold: number;
    output_filename?: string;
    error_message?: string;
}

// Token management
class TokenManager {
    private static TOKEN_KEY = 'auth_token';

    static getToken(): string | null {
        return localStorage.getItem(this.TOKEN_KEY);
    }

    static setToken(token: string): void {
        localStorage.setItem(this.TOKEN_KEY, token);
    }

    static removeToken(): void {
        localStorage.removeItem(this.TOKEN_KEY);
    }

    static isTokenExpired(token: string): boolean {
        try {
            const payload = JSON.parse(atob(token.split('.')[1]));
            return Date.now() >= payload.exp * 1000;
        } catch (error) {
            return true;
        }
    }
}

// Request interceptor to add auth token
api.interceptors.request.use(
    (config) => {
        const token = TokenManager.getToken();
        if (token && !TokenManager.isTokenExpired(token)) {
            config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
    },
    (error) => {
        return Promise.reject(error);
    }
);

// Response interceptor to handle token expiration
api.interceptors.response.use(
    (response) => {
        return response;
    },
    (error: AxiosError) => {
        if (error.response?.status === 401) {
            TokenManager.removeToken();
            window.location.href = '/login';
        }
        return Promise.reject(error);
    }
);

export class ApiService {
    static async login(credentials: LoginRequest): Promise<TokenResponse> {
        const response = await api.post<TokenResponse>('/auth/login', credentials);
        TokenManager.setToken(response.data.access_token);
        return response.data;
    }

    static async register(userData: RegisterRequest): Promise<User> {
        const response = await api.post<User>('/auth/register', userData);
        return response.data;
    }

    static async getCurrentUser(): Promise<User> {
        const response = await api.get<User>('/auth/me');
        return response.data;
    }

    static async refreshToken(): Promise<TokenResponse> {
        const response = await api.post<TokenResponse>('/auth/refresh');
        TokenManager.setToken(response.data.access_token);
        return response.data;
    }

    static logout(): void {
        TokenManager.removeToken();
        window.location.href = '/login';
    }

    static async uploadFile(file: File): Promise<UserFile> {
        const formData = new FormData();
        formData.append('file', file);

        const response = await api.post<UserFile>('/files/upload', formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
        });
        return response.data;
    }

    static async getUserFiles(limit = 50, offset = 0): Promise<{ files: UserFile[], total: number }> {
        const response = await api.get(`/files/list?limit=${limit}&offset=${offset}`);
        return response.data;
    }

    static async getFileInfo(fileId: number): Promise<UserFile> {
        const response = await api.get<UserFile>(`/files/${fileId}`);
        return response.data;
    }

    static async deleteFile(fileId: number): Promise<void> {
        await api.delete(`/files/${fileId}`);
    }

    static async getFileColumns(fileId: number): Promise<{ column_names: Record<string, string> }> {
        const response = await api.get(`/files/${fileId}/columns`);
        return response.data;
    }

    static async getStorageUsage(): Promise<any> {
        const response = await api.get('/files/storage/usage');
        return response.data;
    }

    static async getColumnNames(file: File): Promise<{ filename: string, column_names: Record<string, string> }> {
        const formData = new FormData();
        formData.append('file', file);

        const response = await api.post('/api/column_names', formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
        });
        return response.data;
    }

    static async fuzzyLookupSingleFile(request: {
        filename: string;
        column_1: string;
        column_2: string;
        threshold: number;
    }): Promise<Blob> {
        const response = await api.post('/api/lookup_single_file', request, {
            responseType: 'blob',
        });
        return response.data;
    }

    static async fuzzyLookupMultiFile(request: {
        file_name_1: string;
        file_name_2: string;
        file_1_column: string;
        file_2_column: string;
        threshold: number;
        delimiter?: string;
        output_type?: string;
    }): Promise<Blob> {
        const response = await api.post('/api/lookup_multi_file', request, {
            responseType: 'blob',
            headers: {
                'Content-Type': 'application/json'
            },
        });
        return response.data;
    }

    static async queryDataframe(
        file: File,
        queryColumn: string,
        searchTerm: string,
        threshold = 0.8
    ): Promise<any> {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('query_column', queryColumn);
        formData.append('search_term', searchTerm);
        formData.append('threshold', threshold.toString());

        const response = await api.post('/api/query_dataframe', formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
        });
        return response.data;
    }

    static async getFuzzyJobs(limit = 50, offset = 0): Promise<{ jobs: FuzzyJob[] }> {
        const response = await api.get(`/api/jobs?limit=${limit}&offset=${offset}`);
        return response.data;
    }

    static async downloadJobResult(jobId: number): Promise<Blob> {
        const response = await api.get(`/api/download/${jobId}`, {
            responseType: 'blob',
        });
        return response.data;
    }

    static async findDuplicates(
        file: File,
        columnName: string,
        threshold: number,
        outputType: string = 'csv'
    ): Promise<Blob> {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('column_name', columnName);
        formData.append('threshold', threshold.toString());
        formData.append('output_type', outputType);

        const response = await api.post('/api/find_duplicates', formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
            responseType: 'blob',
        });
        return response.data;
    }

    static async getLicenseInfo(): Promise<LicenseInfo | null> {
        try {
            const response = await api.get<LicenseInfo>('/license/info');
            return response.data;
        } catch (error) {
            if ((error as AxiosError).response?.status === 404) {
                return null;
            }
            throw error;
        }
    }

    static async getLicenseTypes(): Promise<any> {
        const response = await api.get('/license/types');
        return response.data;
    }

    static async upgradeLicense(licenseType: string, durationMonths = 12): Promise<LicenseInfo> {
        const response = await api.post<LicenseInfo>('/license/upgrade', {
            license_type: licenseType,
            duration_months: durationMonths,
        });
        return response.data;
    }

    static async getLicenseUsage(): Promise<any> {
        const response = await api.get('/license/usage');
        return response.data;
    }

    // Utility functions
    static downloadBlob(blob: Blob, filename: string): void {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        a.click();
        window.URL.revokeObjectURL(url);
    }
}

export default ApiService;
