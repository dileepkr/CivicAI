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

export interface DebateMessage {
  id: string;
  sender: string;
  content: string;
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
  [key: string]: any;
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
        timeout: 10000, // 10 second timeout
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

  // Policy endpoints
  async getPolicies(): Promise<Policy[]> {
    return this.request('GET', '/policies');
  }

  async getPolicy(policyId: string): Promise<Policy> {
    return this.request('GET', `/policies/${policyId}`);
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
      content,
      timestamp: new Date().toISOString(),
    });
  }

  pauseDebate() {
    this.sendMessage({
      type: 'pause_debate',
    });
  }

  resumeDebate() {
    this.sendMessage({
      type: 'resume_debate',
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