import React, { useEffect, useContext } from 'react';
import { useTranslation } from 'react-i18next';
import { RouterProvider } from 'react-router-dom';
import { router } from './router';
import ToastContainer, { ToastContext } from './components/ui/ToastContainer';
import { WebSocketManager } from './components/WebSocketManager';
import { useStoreInitialization } from './hooks/useStoreInitialization';
import { setUnauthorizedHandler } from '@/services/api';
import { useAuthStore } from '@/stores/authStore';

/**
 * Main App component with React Router and centralized WebSocket management
 */
const App: React.FC = () => {
  // Initialize stores (platforms, chats, etc.) once at app start
  useStoreInitialization();
  const toast = useContext(ToastContext);
  const { t } = useTranslation();
  useEffect(() => {
    let isLoggingOut = false;
    setUnauthorizedHandler(() => {
      const { isAuthenticated, logout } = useAuthStore.getState();
      if (isLoggingOut) return;
      if (isAuthenticated) {
        isLoggingOut = true;
        try { toast?.showToast('warning', t('auth.sessionExpiredTitle', '会话已过期'), t('auth.sessionExpiredMessage', '请重新登录')); } catch {}
        // Persist a flash message for the login page to display after redirect
        try {
          localStorage.setItem('auth-flash', JSON.stringify({ message: t('auth.sessionExpiredMessage', '登录已过期，请重新登录') }));
        } catch {}
        logout();
      }
    });
  }, [toast]);

  return (
    <ToastContainer>
      {/* Centralized WebSocket connection management */}
      <WebSocketManager />
      <RouterProvider router={router} />
    </ToastContainer>
  );
};

export default App;
