/**
 * URL utilities for building absolute API URLs
 */

/**
 * Convert a possibly relative API path to an absolute URL using VITE_API_BASE_URL.
 * - If input already has a scheme (e.g., https://), return as-is
 * - Otherwise, prefix with API base URL (default http://localhost:8000)
 */
export const toAbsoluteApiUrl = (maybeRelative: string | undefined | null): string => {
  const input = (maybeRelative || '').toString();
  if (!input) return '';
  // If already absolute (has a scheme), return as-is
  if (/^[a-zA-Z][a-zA-Z\d+\-.]*:\/\//.test(input)) {
    return input;
  }
  const base = (import.meta.env?.VITE_API_BASE_URL as string) || 'http://localhost:8000';
  const normalizedBase = base.replace(/\/+$/, '');
  const path = input.startsWith('/') ? input : `/${input}`;
  return `${normalizedBase}${path}`;
};

