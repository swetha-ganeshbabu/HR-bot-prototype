import axios, { AxiosInstance } from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || '';

interface LoginCredentials {
  username: string;
  password: string;
}

interface LoginResponse {
  access_token: string;
  token_type: string;
}

interface ChatMessage {
  message: string;
}

interface ChatResponse {
  response: string;
  message_id?: number;
}

interface ConversationHistory {
  id: number;
  message: string;
  response: string;
  timestamp: string;
}

class ApiService {
  private api: AxiosInstance;
  private token: string | null = null;

  constructor() {
    this.api = axios.create({
      baseURL: API_BASE_URL,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Load token from localStorage
    const storedToken = localStorage.getItem('access_token');
    if (storedToken) {
      this.setAuthToken(storedToken);
    }

    // Add response interceptor for auth errors
    this.api.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 401) {
          this.logout();
          window.location.href = '/login';
        }
        return Promise.reject(error);
      }
    );
  }

  private setAuthToken(token: string) {
    this.token = token;
    this.api.defaults.headers.common['Authorization'] = `Bearer ${token}`;
    localStorage.setItem('access_token', token);
  }

  async login(credentials: LoginCredentials): Promise<LoginResponse> {
    const response = await this.api.post<LoginResponse>('/api/auth/login', credentials);
    this.setAuthToken(response.data.access_token);
    return response.data;
  }

  // Registration is disabled for security
  // async register(credentials: LoginCredentials): Promise<LoginResponse> {
  //   const response = await this.api.post<LoginResponse>('/api/auth/register', credentials);
  //   this.setAuthToken(response.data.access_token);
  //   return response.data;
  // }

  logout() {
    this.token = null;
    delete this.api.defaults.headers.common['Authorization'];
    localStorage.removeItem('access_token');
  }

  isAuthenticated(): boolean {
    return this.token !== null;
  }

  async sendMessage(message: string): Promise<ChatResponse> {
    const response = await this.api.post<ChatResponse>('/api/chat', { message });
    return response.data;
  }

  async getConversationHistory(limit: number = 50): Promise<ConversationHistory[]> {
    const response = await this.api.get<ConversationHistory[]>('/api/conversations', {
      params: { limit },
    });
    return response.data;
  }

  async checkHealth(): Promise<{ status: string; version: string }> {
    const response = await this.api.get('/health');
    return response.data;
  }
}

export default new ApiService();
export type { LoginCredentials, ChatResponse, ConversationHistory };