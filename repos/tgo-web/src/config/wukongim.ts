/**
 * WuKongIM WebSocket Configuration
 */

export interface WuKongIMConfig {
  /** WebSocket server URL (env fallback only; primary comes from dynamic route) */
  wsUrl: string;
  /** Connection timeout in milliseconds */
  connectionTimeout: number;
  /** Maximum reconnection attempts */
  maxReconnectAttempts: number;
  /** Initial reconnection delay in milliseconds */
  reconnectDelay: number;
  /** Maximum reconnection delay in milliseconds */
  maxReconnectDelay: number;
}

/**
 * Default WuKongIM configuration
 */
export const defaultWuKongIMConfig: WuKongIMConfig = {
  wsUrl: import.meta.env.VITE_WUKONGIM_WS_URL || 'ws://localhost:5200',
  connectionTimeout: 10000, // 10 seconds
  maxReconnectAttempts: 5,
  reconnectDelay: 1000, // 1 second
  maxReconnectDelay: 30000, // 30 seconds
};

/**
 * Get WuKongIM configuration with environment variable overrides
 */
export const getWuKongIMConfig = (): WuKongIMConfig => {
  return {
    ...defaultWuKongIMConfig,
    wsUrl: import.meta.env.VITE_WUKONGIM_WS_URL || defaultWuKongIMConfig.wsUrl,
  };
};
