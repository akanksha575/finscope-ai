/**
 * WebSocket service for real-time research updates
 */
import type { ProgressUpdate, ResearchRequest } from '../types';

// Use relative WebSocket URL (same origin) if VITE_WS_URL is not set (for Docker)
// Otherwise use the provided URL or default to localhost:8000 for development
const getWebSocketURL = (): string => {
  if (import.meta.env.VITE_WS_URL && import.meta.env.VITE_WS_URL.trim() !== '') {
    return import.meta.env.VITE_WS_URL;
  }
  // In development mode (manual setup), default to localhost:8000
  if (import.meta.env.DEV) {
    return 'ws://localhost:8000';
  }
  // In production (Docker), use same origin, convert http/https to ws/wss
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  return `${protocol}//${window.location.host}`;
};

const WS_BASE_URL = getWebSocketURL();

export class ResearchWebSocket {
  private ws: WebSocket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 3000;
  private listeners: Map<string, Set<(data: any) => void>> = new Map();
  private isManualClose = false;

  constructor() {
    this.setupEventListeners();
  }

  private setupEventListeners() {
    // Handle page visibility changes
    document.addEventListener('visibilitychange', () => {
      if (document.visibilityState === 'visible' && !this.ws && !this.isManualClose) {
        this.reconnect();
      }
    });
  }

  /**
   * Connect to WebSocket and start research
   */
  connect(request: ResearchRequest): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        const wsUrl = `${WS_BASE_URL}/api/research/stream`;
        this.ws = new WebSocket(wsUrl);
        this.isManualClose = false;

        this.ws.onopen = () => {
          console.log('WebSocket connected');
          this.reconnectAttempts = 0;
          
          // Send research request
          this.ws?.send(JSON.stringify(request));
          resolve();
        };

        this.ws.onmessage = (event) => {
          try {
            const data: ProgressUpdate = JSON.parse(event.data);
            this.emit('message', data);
            
            // Emit specific event types
            if (data.type) {
              this.emit(data.type, data);
            }
          } catch (error) {
            console.error('Error parsing WebSocket message:', error);
          }
        };

        this.ws.onerror = (error) => {
          console.error('WebSocket error:', error);
          this.emit('error', error);
          reject(error);
        };

        this.ws.onclose = () => {
          console.log('WebSocket closed');
          this.emit('close', null);
          
          // Auto-reconnect if not manually closed
          if (!this.isManualClose && this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnect();
          }
        };
      } catch (error) {
        reject(error);
      }
    });
  }

  /**
   * Reconnect to WebSocket
   */
  private reconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('Max reconnection attempts reached');
      this.emit('max_reconnect', null);
      return;
    }

    this.reconnectAttempts++;
    const delay = this.reconnectDelay * this.reconnectAttempts;
    
    console.log(`Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})`);
    
    setTimeout(() => {
      if (!this.isManualClose) {
        this.emit('reconnecting', { attempt: this.reconnectAttempts });
        // Note: Reconnection requires the original request, which should be stored
        // For now, we'll just emit the reconnecting event
      }
    }, delay);
  }

  /**
   * Disconnect from WebSocket
   */
  disconnect() {
    this.isManualClose = true;
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  /**
   * Subscribe to events
   */
  on(event: string, callback: (data: any) => void) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, new Set());
    }
    this.listeners.get(event)?.add(callback);
  }

  /**
   * Unsubscribe from events
   */
  off(event: string, callback: (data: any) => void) {
    this.listeners.get(event)?.delete(callback);
  }

  /**
   * Emit event to listeners
   */
  private emit(event: string, data: any) {
    this.listeners.get(event)?.forEach(callback => {
      try {
        callback(data);
      } catch (error) {
        console.error(`Error in event listener for ${event}:`, error);
      }
    });
  }

  /**
   * Get connection status
   */
  get isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }
}

// Export singleton instance
export const researchWebSocket = new ResearchWebSocket();


