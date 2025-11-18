import React from 'react';
import { useTranslation } from 'react-i18next';
import { User, LogOut } from 'lucide-react';
import { useAuthStore } from '@/stores/authStore';

const ProfileSettings: React.FC = () => {
  const { t } = useTranslation();
  const { user, isAuthenticated, logout } = useAuthStore();

  return (
    <div className="p-6">
      <div className="flex items-center gap-2 mb-4">
        <User className="w-5 h-5 text-gray-600" />
        <h2 className="text-lg font-medium text-gray-800">{t('settings.account.title', '账户信息')}</h2>
      </div>

      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 rounded-lg overflow-hidden bg-gray-100 border border-gray-200">
            {user?.avatar_url ? (
              <img src={user.avatar_url} alt="avatar" className="w-full h-full object-cover" />
            ) : (
              <div className="w-full h-full flex items-center justify-center text-gray-600 font-bold text-lg">
                {(user?.nickname || user?.username || 'U').slice(0,1).toUpperCase()}
              </div>
            )}
          </div>
          <div className="flex-1">
            <div className="text-base font-medium text-gray-800">
              {user?.nickname || user?.username || t('auth.notLoggedIn', '未登录')}
            </div>
            {isAuthenticated && (
              <div className="text-sm text-gray-500">
                {user?.role === 'agent' ? t('auth.agent', 'Agent') : t('auth.user', 'User')}
              </div>
            )}
          </div>
          {isAuthenticated && (
            <button
              onClick={async () => { try { await logout(); } catch (e) { console.error(e); } }}
              className="flex items-center gap-2 px-4 py-2 text-sm bg-red-50 text-red-600 border border-red-200 rounded-md hover:bg-red-100 transition-colors"
            >
              <LogOut className="w-4 h-4" />
              {t('auth.logout', '退出登录')}
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default ProfileSettings;

