/**
 * Knowledge Base API Service
 * Handles RAG Collections and Files API endpoints
 */

import { apiClient } from './api';
import BaseApiService from './base/BaseApiService';


// Helper function to check if user is authenticated
export const isAuthenticated = (): boolean => {
  const token = apiClient.getToken();
  return token !== null && token.trim() !== '';
};

// Pagination types
export interface PaginationMetadata {
  total: number;
  limit: number;
  offset: number;
  has_next: boolean;
  has_previous: boolean;
}

export interface PaginatedResponse<T> {
  data: T[];
  pagination: PaginationMetadata;
}

// Error handling utility with Chinese messages
export const handleApiError = (error: unknown): string => {
  if (error instanceof Error) {
    const message = error.message.toLowerCase();

    // Network errors
    if (message.includes('network') || message.includes('fetch')) {
      return '网络连接失败，请检查网络连接后重试';
    }

    // Timeout errors
    if (message.includes('timeout')) {
      return '请求超时，请稍后重试';
    }

    // HTTP status errors
    if (message.includes('400')) {
      return '请求参数错误，请检查输入内容';
    }
    if (message.includes('401')) {
      return '身份验证失败，请重新登录';
    }
    if (message.includes('403')) {
      return '权限不足，无法执行此操作';
    }
    if (message.includes('404')) {
      return '请求的资源不存在';
    }
    if (message.includes('409')) {
      return '资源冲突，请刷新页面后重试';
    }
    if (message.includes('413')) {
      return '文件过大，请选择较小的文件';
    }
    if (message.includes('415')) {
      return '不支持的文件类型';
    }
    if (message.includes('429')) {
      return '请求过于频繁，请稍后重试';
    }
    if (message.includes('500')) {
      return '服务器内部错误，请稍后重试';
    }
    if (message.includes('502') || message.includes('503') || message.includes('504')) {
      return '服务暂时不可用，请稍后重试';
    }

    // Return original message if no specific pattern matches
    return error.message;
  }

  return '发生未知错误，请稍后重试';
};

// API Response Types based on OpenAPI specification
export interface CollectionResponse {
  id: string;
  display_name: string;
  description?: string | null;
  collection_metadata?: Record<string, any> | null;
  tags?: string[] | null;
  file_count: number;
  created_at: string;
  updated_at: string;
  deleted_at?: string | null;
}

export interface FileResponse {
  id: string;
  collection_id?: string | null;
  original_filename: string;
  file_size: number;
  content_type: string;
  status: 'pending' | 'processing' | 'completed' | 'failed' | 'archived';
  document_count: number;
  total_tokens: number;
  language?: string | null;
  description?: string | null;
  tags?: string[] | null;
  uploaded_by?: string | null;
  created_at: string;
  updated_at: string;
}

export interface CollectionListResponse extends PaginatedResponse<CollectionResponse> {}
export interface FileListResponse extends PaginatedResponse<FileResponse> {}

export interface CollectionCreateRequest {
  display_name: string;
  description?: string;
  collection_metadata?: Record<string, any>;
  tags?: string[];
}

export interface CollectionUpdateRequest {
  display_name?: string;
  description?: string;
  collection_metadata?: Record<string, any>;
  tags?: string[];
}

export interface FileUploadRequest {
  collection_id?: string;
  description?: string;
  tags?: string[];
  language?: string;
}

// API Endpoints - Use relative paths since the API client already includes the base URL
const API_VERSION = 'v1';

export const KNOWLEDGE_BASE_ENDPOINTS = {
  // Collections
  COLLECTIONS: `/${API_VERSION}/rag/collections`,
  COLLECTION_BY_ID: (id: string) => `/${API_VERSION}/rag/collections/${id}`,

  // Files
  FILES: `/${API_VERSION}/rag/files`,
  FILE_BY_ID: (id: string) => `/${API_VERSION}/rag/files/${id}`,
  FILES_BATCH: `/${API_VERSION}/rag/files/batch`,
} as const;

/**
 * Knowledge Base API Service Class
 */
export class KnowledgeBaseApiService extends BaseApiService {
  protected readonly apiVersion = 'v1';
  protected readonly endpoints = {
    COLLECTIONS: `/${this.apiVersion}/rag/collections`,
    COLLECTION_BY_ID: (id: string) => `/${this.apiVersion}/rag/collections/${id}`,
    FILES: `/${this.apiVersion}/rag/files`,
    FILE_BY_ID: (id: string) => `/${this.apiVersion}/rag/files/${id}`,
    FILES_BATCH: `/${this.apiVersion}/rag/files/batch`,
  } as const;
  
  // Collections API
  static async getCollections(params?: {
    limit?: number;
    offset?: number;
    search?: string;
    tags?: string[];
  }): Promise<CollectionListResponse> {
    const service = new KnowledgeBaseApiService();
    try {
      const queryParams = new URLSearchParams();
      if (params?.limit) queryParams.append('limit', params.limit.toString());
      if (params?.offset !== undefined) queryParams.append('offset', params.offset.toString());
      if (params?.search) queryParams.append('search', params.search);
      if (params?.tags?.length) queryParams.append('tags', params.tags.join(','));

      const url = queryParams.toString()
        ? `${service.endpoints.COLLECTIONS}?${queryParams.toString()}`
        : service.endpoints.COLLECTIONS;

      return await service.get<CollectionListResponse>(url);
    } catch (error) {
      throw new Error(service['handleApiError'](error));
    }
  }

  static async getCollection(id: string): Promise<CollectionResponse> {
    const service = new KnowledgeBaseApiService();
    try {
      const endpoint = service.endpoints.COLLECTION_BY_ID(id);
      return await service.get<CollectionResponse>(endpoint);
    } catch (error) {
      throw new Error(service['handleApiError'](error));
    }
  }

  static async createCollection(data: CollectionCreateRequest): Promise<CollectionResponse> {
    const service = new KnowledgeBaseApiService();
    try {
      return await service.post<CollectionResponse>(
        service.endpoints.COLLECTIONS,
        data
      );
    } catch (error) {
      throw new Error(service['handleApiError'](error));
    }
  }

  static async updateCollection(id: string, data: CollectionUpdateRequest): Promise<CollectionResponse> {
    const service = new KnowledgeBaseApiService();
    try {
      return await service.patch<CollectionResponse>(
        service.endpoints.COLLECTION_BY_ID(id),
        data
      );
    } catch (error) {
      throw new Error(service['handleApiError'](error));
    }
  }

  static async deleteCollection(id: string): Promise<void> {
    const service = new KnowledgeBaseApiService();
    try {
      await service.delete<void>(
        service.endpoints.COLLECTION_BY_ID(id)
      );
    } catch (error) {
      throw new Error(service['handleApiError'](error));
    }
  }



  // Files API
  static async getFiles(params?: {
    limit?: number;
    offset?: number;
    collection_id?: string;
    status?: string;
    search?: string;
    tags?: string[];
  }): Promise<FileListResponse> {
    const service = new KnowledgeBaseApiService();
    try {
      const queryParams = new URLSearchParams();
      if (params?.limit) queryParams.append('limit', params.limit.toString());
      if (params?.offset !== undefined) queryParams.append('offset', params.offset.toString());
      if (params?.collection_id) queryParams.append('collection_id', params.collection_id);
      if (params?.status) queryParams.append('status', params.status);
      if (params?.search) queryParams.append('search', params.search);
      if (params?.tags?.length) queryParams.append('tags', params.tags.join(','));

      const url = queryParams.toString()
        ? `${service.endpoints.FILES}?${queryParams.toString()}`
        : service.endpoints.FILES;

      return await service.get<FileListResponse>(url);
    } catch (error) {
      throw new Error(service['handleApiError'](error));
    }
  }

  static async getFile(id: string): Promise<FileResponse> {
    const service = new KnowledgeBaseApiService();
    try {
      const endpoint = service.endpoints.FILE_BY_ID(id);
      return await service.get<FileResponse>(endpoint);
    } catch (error) {
      throw new Error(service['handleApiError'](error));
    }
  }

  static async uploadFile(
    file: File,
    metadata?: FileUploadRequest
  ): Promise<FileResponse> {
    const service = new KnowledgeBaseApiService();
    try {
      const formData = new FormData();
      formData.append('file', file);
      if (metadata?.collection_id) formData.append('collection_id', metadata.collection_id);
      if (metadata?.description) formData.append('description', metadata.description);
      if (metadata?.language) formData.append('language', metadata.language);
      if (metadata?.tags?.length) formData.append('tags', JSON.stringify(metadata.tags));
      return await apiClient.postFormData<FileResponse>(service.endpoints.FILES, formData);
    } catch (error) {
      throw new Error(handleApiError(error));
    }
  }

  static async deleteFile(id: string): Promise<void> {
    const service = new KnowledgeBaseApiService();
    try {
      await service.delete<void>(
        service.endpoints.FILE_BY_ID(id)
      );
    } catch (error) {
      throw new Error(service['handleApiError'](error));
    }
  }

  static async downloadFile(id: string): Promise<Response> {
    const service = new KnowledgeBaseApiService();
    try {
      const endpoint = `${service.endpoints.FILE_BY_ID(id)}/download`;
      return await apiClient.getResponse(endpoint);
    } catch (error) {
      throw new Error(handleApiError(error));
    }
  }

  // Batch operations
  static async deleteFiles(fileIds: string[]): Promise<void> {
    const service = new KnowledgeBaseApiService();
    try {
      await service.post<void>(
        `${service.endpoints.FILES_BATCH}/delete`,
        { file_ids: fileIds }
      );
    } catch (error) {
      throw new Error(service['handleApiError'](error));
    }
  }
}

// Export default service instance
export default KnowledgeBaseApiService;
