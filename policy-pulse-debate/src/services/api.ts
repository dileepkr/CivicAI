/**
 * API Service for CivicAI Policy Debate System
 * 
 * This service handles all communication with the FastAPI backend,
 * including REST API calls and WebSocket connections for real-time debate streaming.
 */

import axios, { AxiosResponse } from 'axios';

// Configuration
const API_BASE_URL = 'http://localhost:8000';
const WS_BASE_URL = 'ws://localhost:8000';

// Types
export interface Policy {
  id: string;
  title: string;
  date: string;
  summary: string;
  relevance: 'high' | 'medium' | 'low';
  text: string;
}

// New types for policy discovery
export interface PolicyDiscoveryRequest {
  location: string;
  stakeholder_roles: string[];
  interests: string[];
  domains?: string[];
  government_levels?: string[];
  regulation_timing?: string;
  max_results?: number;
}

export interface PolicySearchRequest {
  prompt: string;
  max_results?: number;
}

export interface StakeholderImpact {
  group: string;
  severity: 'high' | 'medium' | 'low';
  description: string;
  affected_areas: string[];
}

export interface DiscoveredPolicy {
  id: string;
  title: string;
  url: string;
  government_level: 'federal' | 'state' | 'local';
  domain: string;
  summary: string;
  status: string;
  source_agency: string;
  last_updated: string;
  stakeholder_impacts: StakeholderImpact[];
  confidence_score: number;
  content_preview?: string;
}

export interface PolicyDiscoveryResponse {
  success: boolean;
  total_found: number;
  search_time: number;
  priority_policies: DiscoveredPolicy[];
  discovered_policies: DiscoveredPolicy[]; // Add this for backward compatibility
  policy_analysis?: {
    answer: string;
    citations: { title: string; url: string }[];
  };
  stakeholder_impact_map?: Record<string, DiscoveredPolicy[]>;
  error?: string;
}

export interface PolicyDomain {
  value: string;
  label: string;
}

export interface GovernmentLevel {
  value: string;
  label: string;
}

export interface DebateMessage {
  id: string;
  sender: string;
  stakeholder: string; // Add stakeholder field
  content: string;
  message: string; // Add message field for backward compatibility
  timestamp: string;
  message_type?: string;
  metadata?: Record<string, any>;
  round?: number;
  round_type?: string;
}

export interface DebateSession {
  session_id: string;
  status: string;
  policy_name: string;
  system_type: string;
  current_round: number;
  message_count: number;
  stakeholder_count: number;
}

export interface StartDebateRequest {
  policy_name: string;
  system_type: 'debug' | 'weave' | 'human';
}

export interface WebSocketMessage {
  type: string;
  data: any;
  timestamp: string;
  [key: string]: any;
}

// New types for agentic workflows
export interface AgenticPolicyAnalysisRequest {
  policy_name: string;
  user_location: string;
  stakeholder_roles: string[];
  interests: string[];
  analysis_type?: string;
}

export interface StakeholderInfo {
  name: string;
  type: string;
  description?: string;
  interests?: string[];
}

export interface AgenticDebateRequest {
  policy_id: string;
  policy_title: string;
  policy_content: string;
  stakeholder_groups: string[];
  debate_rounds?: number;
  debate_style?: string;
}

export interface CrewWorkflowRequest {
  workflow_type: string;
  policy_context: Record<string, any>;
  user_context: Record<string, any>;
  workflow_config?: Record<string, any>;
}

export interface AgenticWorkflowResponse {
  success: boolean;
  workflow_id: string;
  workflow_type: string;
  status: string;
  results: Record<string, any>;
  agents_involved: string[];
  execution_time: number;
  error?: string;
  debate_messages?: DebateMessage[];
  summary?: string;
}

export interface WorkflowDefinition {
  type: string;
  name: string;
  description: string;
  required_fields: string[];
}

export interface EmailGenerationRequest {
  policy_id: string;
  policy_title: string;
  policy_content: string;
  user_perspective: string;
  debate_context?: DebateMessage[];
}

export interface EmailGenerationResponse {
  success: boolean;
  email_content: string;
  recipients: string[];
  error?: string;
}

export interface CrewSystemStatus {
  status: string;
  components?: {
    policy_discovery_agent: boolean;
    llm_configured: boolean;
    tools_available: Record<string, boolean>;
  };
  message: string;
}

// API Client
class ApiClient {
  private baseURL: string;
  
  constructor(baseURL: string = API_BASE_URL) {
    this.baseURL = baseURL;
  }

  private async request<T>(
    method: 'GET' | 'POST' | 'PUT' | 'DELETE',
    endpoint: string,
    data?: any
  ): Promise<T> {
    try {
      const response: AxiosResponse<T> = await axios({
        method,
        url: `${this.baseURL}${endpoint}`,
        data,
        headers: {
          'Content-Type': 'application/json',
        },
        timeout: 30000, // 30 second timeout
      });
      return response.data;
    } catch (error: any) {
      console.error(`API Error (${method} ${endpoint}):`, error);
      
      // Provide more detailed error information
      if (error.response) {
        // Server responded with error status
        const errorMessage = error.response.data?.detail || error.response.data?.message || 'Server error';
        throw new Error(`${errorMessage} (${error.response.status})`);
      } else if (error.request) {
        // Request made but no response received
        throw new Error('Unable to connect to the server. Please check if the backend is running.');
      } else {
        // Something else happened
        throw new Error(`Request failed: ${error.message}`);
      }
    }
  }

  // Health check
  async healthCheck(): Promise<{ status: string; timestamp: string }> {
    return this.request('GET', '/health');
  }

  // Legacy policy endpoints
  async getPolicies(): Promise<Policy[]> {
    return this.request('GET', '/policies');
  }

  async getPolicy(policyId: string): Promise<Policy> {
    return this.request('GET', `/policies/${policyId}`);
  }

  // New policy discovery endpoints
  async discoverPolicies(request: PolicyDiscoveryRequest): Promise<PolicyDiscoveryResponse> {
    const response = await this.request<PolicyDiscoveryResponse>('POST', '/policies/discover', request);
    // Ensure backward compatibility by copying priority_policies to discovered_policies
    if (response.priority_policies && !response.discovered_policies) {
      response.discovered_policies = response.priority_policies;
    }
    return response;
  }

  async searchPolicies(request: PolicySearchRequest): Promise<PolicyDiscoveryResponse> {
    const response = await this.request<PolicyDiscoveryResponse>('POST', '/policies/search', request);
    // Ensure backward compatibility by copying priority_policies to discovered_policies
    if (response.priority_policies && !response.discovered_policies) {
      response.discovered_policies = response.priority_policies;
    }
    return response;
  }

  async getPolicyDomains(): Promise<{ domains: PolicyDomain[] }> {
    return this.request('GET', '/policies/domains');
  }

  async getGovernmentLevels(): Promise<{ levels: GovernmentLevel[] }> {
    return this.request('GET', '/policies/government-levels');
  }

  async analyzePolicyQuestion(question: string): Promise<{ analysis: any }> {
    return this.request('POST', '/policies/analyze', { question });
  }

  // Debate endpoints
  async startDebate(request: StartDebateRequest): Promise<DebateSession> {
    return this.request('POST', '/debates/start', request);
  }

  async getDebateStatus(sessionId: string): Promise<DebateSession> {
    return this.request('GET', `/debates/${sessionId}/status`);
  }

  async getDebateMessages(sessionId: string): Promise<{
    session_id: string;
    messages: DebateMessage[];
    total_count: number;
  }> {
    return this.request('GET', `/debates/${sessionId}/messages`);
  }

  // Agentic workflow endpoints
  async runPolicyAnalysis(request: AgenticPolicyAnalysisRequest): Promise<AgenticWorkflowResponse> {
    return this.request('POST', '/crew/policy-analysis', request);
  }

  async runStakeholderDebate(request: AgenticDebateRequest): Promise<AgenticWorkflowResponse> {
    return this.request('POST', '/crew/stakeholder-debate', request);
  }

  async runCustomWorkflow(request: CrewWorkflowRequest): Promise<AgenticWorkflowResponse> {
    return this.request('POST', '/crew/workflow', request);
  }

  async getAvailableWorkflows(): Promise<{ workflows: WorkflowDefinition[] }> {
    return this.request('GET', '/crew/workflows');
  }

  async getCrewSystemStatus(): Promise<CrewSystemStatus> {
    return this.request('GET', '/crew/status');
  }

  async generateEmail(request: EmailGenerationRequest): Promise<EmailGenerationResponse> {
    return this.request('POST', '/email/generate', request);
  }
}

// WebSocket Client
export class DebateWebSocketClient {
  private ws: WebSocket | null = null;
  private sessionId: string;
  private messageHandlers: Map<string, (message: WebSocketMessage) => void> = new Map();
  private reconnectAttempts: number = 0;
  private maxReconnectAttempts: number = 5;
  private reconnectDelay: number = 1000;

  constructor(sessionId: string) {
    this.sessionId = sessionId;
  }

  connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        this.ws = new WebSocket(`${WS_BASE_URL}/debates/${this.sessionId}/stream`);
        
        this.ws.onopen = () => {
          console.log('WebSocket connected');
          this.reconnectAttempts = 0;
          resolve();
        };

        this.ws.onmessage = (event) => {
          try {
            const message: WebSocketMessage = JSON.parse(event.data);
            this.handleMessage(message);
          } catch (error) {
            console.error('Error parsing WebSocket message:', error);
          }
        };

        this.ws.onclose = (event) => {
          console.log('WebSocket disconnected:', event.code, event.reason);
          this.handleDisconnect();
        };

        this.ws.onerror = (error) => {
          console.error('WebSocket error:', error);
          reject(error);
        };
      } catch (error) {
        reject(error);
      }
    });
  }

  private handleMessage(message: WebSocketMessage) {
    // Handle different message types
    const handler = this.messageHandlers.get(message.type);
    if (handler) {
      handler(message);
    }

    // Handle global message handler
    const globalHandler = this.messageHandlers.get('*');
    if (globalHandler) {
      globalHandler(message);
    }
  }

  private handleDisconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      console.log(`Attempting to reconnect... (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
      
      setTimeout(() => {
        this.connect().catch(console.error);
      }, this.reconnectDelay * this.reconnectAttempts);
    } else {
      console.error('Max reconnect attempts reached');
    }
  }

  onMessage(type: string, handler: (message: WebSocketMessage) => void) {
    this.messageHandlers.set(type, handler);
  }

  onAnyMessage(handler: (message: WebSocketMessage) => void) {
    this.messageHandlers.set('*', handler);
  }

  sendMessage(message: WebSocketMessage) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    } else {
      console.error('WebSocket not connected');
    }
  }

  sendUserMessage(content: string) {
    this.sendMessage({
      type: 'user_message',
      data: { content },
      timestamp: new Date().toISOString()
    });
  }

  pauseDebate() {
    this.sendMessage({
      type: 'pause_debate',
      data: {},
      timestamp: new Date().toISOString()
    });
  }

  resumeDebate() {
    this.sendMessage({
      type: 'resume_debate',
      data: {},
      timestamp: new Date().toISOString()
    });
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    this.messageHandlers.clear();
  }

  isConnected(): boolean {
    return this.ws !== null && this.ws.readyState === WebSocket.OPEN;
  }
}

// Export API client instance
export const apiClient = new ApiClient();

// Utility functions
export const createDebateWebSocket = (sessionId: string): DebateWebSocketClient => {
  return new DebateWebSocketClient(sessionId);
};

export const formatTimestamp = (timestamp: string): string => {
  const date = new Date(timestamp);
  return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
};

export const getMessageTypeColor = (messageType: string): string => {
  switch (messageType) {
    case 'debate_message':
      return 'text-blue-600';
    case 'status_update':
      return 'text-green-600';
    case 'error':
      return 'text-red-600';
    case 'debate_step':
      return 'text-purple-600';
    default:
      return 'text-gray-600';
  }
};

export const getSenderColor = (sender: string): string => {
  // Create consistent colors for different senders
  const colors = [
    'bg-blue-100 text-blue-800',
    'bg-green-100 text-green-800',
    'bg-purple-100 text-purple-800',
    'bg-orange-100 text-orange-800',
    'bg-pink-100 text-pink-800',
    'bg-indigo-100 text-indigo-800',
  ];
  
  // Simple hash function to assign consistent colors
  let hash = 0;
  for (let i = 0; i < sender.length; i++) {
    hash = sender.charCodeAt(i) + ((hash << 5) - hash);
  }
  
  return colors[Math.abs(hash) % colors.length];
};

export default apiClient;