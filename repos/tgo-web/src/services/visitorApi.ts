/**
 * Visitor API Service
 * Handles visitor-related API endpoints
 */

import { BaseApiService } from './base/BaseApiService';
import type { Visitor, ChannelAIInsights } from '@/types';

// API Request/Response Types based on OpenAPI specification

// Tag response structure from API
export interface TagResponse {
  id: string;
  name: string;
  category: string;
  weight: number;
  color?: string | null;
  description?: string | null;
  project_id: string;
  created_at: string;
  updated_at: string;
  deleted_at?: string | null;
}

// Extended tag response with visitor_tag_id for deletion
export interface VisitorTagWithAssociationId extends TagResponse {
  /** Visitor-tag association ID (UUID) - needed for deletion */
  visitor_tag_id?: string;
}

// Visitor attributes update request (PUT /v1/visitors/{visitor_id}/attributes)
export interface VisitorAttributesUpdateRequest {
  name?: string | null;
  nickname?: string | null;
  avatar_url?: string | null;
  phone_number?: string | null;
  email?: string | null;
  company?: string | null;
  job_title?: string | null;
  source?: string | null;
  note?: string | null;
  custom_attributes?: Record<string, string | null> | null;
}

// Complete visitor response structure from API (GET /v1/visitors/{visitor_id})
export interface VisitorResponse {
  id: string;
  project_id: string;
  platform_id: string;
  platform_open_id: string;
  name?: string | null;
  nickname?: string | null;
  avatar_url?: string | null;
  phone_number?: string | null;
  email?: string | null;
  company?: string | null;
  job_title?: string | null;
  source?: string | null;
  note?: string | null;
  custom_attributes: Record<string, string | null>;
  first_visit_time: string;
  last_visit_time: string;
  last_offline_time?: string | null;
  is_online: boolean;
  ai_disabled?: boolean; // True if AI is disabled for this visitor
  tags: TagResponse[];
  ai_profile?: any | null;
  ai_insights?: ChannelAIInsights | null;
  system_info?: any | null;
  recent_activities: any[];
  created_at: string;
  updated_at: string;
  deleted_at?: string | null;
}

// Request params for GET /v1/visitors/by-channel
export interface VisitorByChannelParams {
  channel_id: string;
  channel_type: number; // 1 for personal; 251 for customer service
}


/**
 * Visitor API Service Class
 */
class VisitorApiService extends BaseApiService {
  protected readonly endpoints = {
    visitors: '/v1/visitors',
    visitorById: (id: string) => `/v1/visitors/${id}`,
    visitorAttributes: (id: string) => `/v1/visitors/${id}/attributes`,
    visitorByChannel: '/v1/visitors/by-channel',
    enableAI: (id: string) => `/v1/visitors/${id}/enable-ai`,
    disableAI: (id: string) => `/v1/visitors/${id}/disable-ai`,
  };

  protected readonly apiVersion = 'v1';

  /**
   * Get visitor by ID
   */
  async getVisitor(visitorId: string): Promise<VisitorResponse> {
    const endpoint = this.endpoints.visitorById(visitorId);
    return this.get<VisitorResponse>(endpoint);
  }

  /**
   * Update visitor attributes using PUT /v1/visitors/{visitor_id}/attributes
   */
  async updateVisitorAttributes(
    visitorId: string,
    attributes: VisitorAttributesUpdateRequest
  ): Promise<VisitorResponse> {
    const endpoint = this.endpoints.visitorAttributes(visitorId);
    // The API expects the exact format as defined in VisitorAttributesUpdateRequest
    return this.put<VisitorResponse>(endpoint, attributes);
  }

  /**
   * Get visitor by channel using GET /v1/visitors/by-channel
   */
  async getVisitorByChannel(params: VisitorByChannelParams): Promise<VisitorResponse> {
    const endpoint = this.endpoints.visitorByChannel;
    const url = `${endpoint}?channel_id=${encodeURIComponent(params.channel_id)}&channel_type=${params.channel_type}`;
    return this.get<VisitorResponse>(url);
  }

  /**
   * Enable AI for a visitor using POST /v1/visitors/{visitor_id}/enable-ai
   */
  async enableAI(visitorId: string): Promise<VisitorResponse> {
    const endpoint = (this.endpoints.enableAI as (id: string) => string)(visitorId);
    return this.post<VisitorResponse>(endpoint, {});
  }

  /**
   * Disable AI for a visitor using POST /v1/visitors/{visitor_id}/disable-ai
   */
  async disableAI(visitorId: string): Promise<VisitorResponse> {
    const endpoint = (this.endpoints.disableAI as (id: string) => string)(visitorId);
    return this.post<VisitorResponse>(endpoint, {});
  }

  /**
   * Transform API response to internal Visitor type
   */
  transformToVisitor(apiResponse: VisitorResponse): Visitor {
    return {
      id: apiResponse.id,
      name: apiResponse.name || '',
      email: apiResponse.email || undefined,
      phone: apiResponse.phone_number || undefined,
      avatar: apiResponse.avatar_url || '',
      status: apiResponse.is_online ? 'online' : 'offline',
      tags: apiResponse.tags.map(tag => tag.name),
      notes: apiResponse.note || undefined,
      firstVisit: apiResponse.first_visit_time,
      lastVisit: apiResponse.last_visit_time,
      visitCount: undefined, // Not provided by API
      pageViews: undefined, // Not provided by API
      sessionDuration: undefined, // Not provided by API
    };
  }

  /**
   * Transform internal visitor data to API request format
   */
  transformToApiRequest(visitor: Partial<Visitor>): VisitorAttributesUpdateRequest {
    return {
      name: visitor.name,
      email: visitor.email,
      phone_number: visitor.phone,
      note: visitor.notes,
      // Transform any additional properties to custom_attributes
      custom_attributes: {}
    };
  }
}

// Create and export service instance
export const visitorApiService = new VisitorApiService();
