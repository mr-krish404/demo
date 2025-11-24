const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8080';

export class ApiClient {
  private baseUrl: string;
  private token: string | null;

  constructor() {
    this.baseUrl = API_URL;
    this.token = localStorage.getItem('token');
  }

  private async request(endpoint: string, options: RequestInit = {}) {
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
      ...options.headers,
    };

    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }

    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      ...options,
      headers,
    });

    if (!response.ok) {
      throw new Error(`API Error: ${response.statusText}`);
    }

    return response.json();
  }

  async login(email: string, password: string) {
    const data = await this.request('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
    this.token = data.access_token;
    localStorage.setItem('token', data.access_token);
    return data;
  }

  async signup(email: string, password: string, name: string) {
    const data = await this.request('/api/auth/signup', {
      method: 'POST',
      body: JSON.stringify({ email, password, name }),
    });
    this.token = data.access_token;
    localStorage.setItem('token', data.access_token);
    return data;
  }

  async getProjects() {
    return this.request('/api/projects');
  }

  async createProject(name: string, description: string) {
    return this.request('/api/projects', {
      method: 'POST',
      body: JSON.stringify({ name, description, settings: {} }),
    });
  }

  async getProject(projectId: string) {
    return this.request(`/api/projects/${projectId}`);
  }

  async getFindings(projectId: string) {
    return this.request(`/api/findings?project_id=${projectId}`);
  }

  async getJobs(projectId: string) {
    return this.request(`/api/scans/${projectId}/jobs`);
  }

  async startScan(projectId: string) {
    return this.request(`/api/scans/${projectId}/start`, {
      method: 'POST',
      body: JSON.stringify({ test_cases: null, config: {} }),
    });
  }

  async addTarget(projectId: string, type: string, value: string) {
    return this.request('/api/targets', {
      method: 'POST',
      body: JSON.stringify({ project_id: projectId, type, value, scope_rules: {} }),
    });
  }

  async getTargets(projectId: string) {
    return this.request(`/api/targets?project_id=${projectId}`);
  }
}

export const apiClient = new ApiClient();
