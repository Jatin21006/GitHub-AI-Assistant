// Types
export interface CloneRequest {
  github_url: string;
}

export interface RepositoryIngestResponse {
  repository_name: string;
  local_path: string;
  is_duplicate: boolean;
  message: string;
}

export interface IndexRequest {
  repository_name: string;
}

export interface IndexResult {
  repository_name: string;
  total_documents: number;
  total_chunks: number;
  total_vectors: number;
  vector_store_path: string;
}

export interface RepositoryQueryRequest {
  repository_name: string;
  question: string;
}

export interface Citation {
  file_path: string;
  start_line: number;
  end_line: number;
  snippet: string;
}

export interface QueryResponse {
  answer: string;
  citations: Citation[];
}

export interface RepositoryStatusResponse {
  repository_name: string;
  is_cloned: boolean;
  is_indexed: boolean;
}

// Ensure vite proxies /api to http://127.0.0.1:8000
const API_BASE = '/api';

export const apiService = {
  /**
   * Clone a GitHub repository
   */
  cloneRepository: async (github_url: string): Promise<RepositoryIngestResponse> => {
    const response = await fetch(`${API_BASE}/repositories/clone`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ github_url }),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.detail || 'Failed to clone repository');
    }

    return response.json();
  },

  /**
   * Index a cloned repository
   */
  indexRepository: async (repository_name: string): Promise<IndexResult> => {
    const response = await fetch(`${API_BASE}/repositories/index`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ repository_name }),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.detail || 'Failed to index repository');
    }

    return response.json();
  },

  /**
   * Query the repository using RAG
   */
  queryRepository: async (repository_name: string, question: string): Promise<QueryResponse> => {
    const response = await fetch(`${API_BASE}/repositories/query`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ repository_name, question }),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.detail || 'Failed to query repository');
    }

    return response.json();
  },

  /**
   * Get repository clone/index status
   */
  getRepositoryStatus: async (owner: string, repo: string): Promise<RepositoryStatusResponse> => {
    const response = await fetch(`${API_BASE}/repositories/${owner}/${repo}`);
    
    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.detail || 'Failed to fetch repository status');
    }

    return response.json();
  }
};
