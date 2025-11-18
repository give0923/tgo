import React from 'react';
import { useTranslation } from 'react-i18next';
import { Settings, User, Globe, Palette, LogOut } from 'lucide-react';
import LanguageSelector from '@/components/ui/LanguageSelector';
import { useAuthStore } from '@/stores/authStore';

const SettingsPage: React.FC = () => {
  const { t } = useTranslation();
  const { user, logout, isAuthenticated } = useAuthStore();

  return (
    <div className="flex-1 overflow-auto">
      <div className="max-w-4xl mx-auto p-6 space-y-6">
        {/* Header */}
        <div className="flex items-center gap-3">
          <Settings className="w-6 h-6 text-gray-600" />
          <div>
            <h1 className="text-2xl font-semibold text-gray-800">
              {t('settings.title', '设置')}
            </h1>
            <p className="text-sm text-gray-500 mt-1">
              {t('settings.subtitle', '个性化你的偏好和应用设置')}
            </p>
          </div>
        </div>

        {/* Account Section */}
        <section className="bg-white rounded-lg border border-gray-200 p-6">
          <div className="flex items-center gap-2 mb-4">
            <User className="w-5 h-5 text-gray-600" />
            <h2 className="text-lg font-medium text-gray-800">
              {t('settings.account.title', '账户信息')}
            </h2>
          </div>

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
                onClick={async () => {
                  try {
                    await logout();
                  } catch (error) {
                    console.error('Logout failed:', error);
                  }
                }}
                className="flex items-center gap-2 px-4 py-2 text-sm bg-red-50 text-red-600 border border-red-200 rounded-md hover:bg-red-100 transition-colors"
              >
                <LogOut className="w-4 h-4" />
                {t('auth.logout', '退出登录')}
              </button>
            )}
          </div>
        </section>

        {/* Language Section */}
        <section className="bg-white rounded-lg border border-gray-200 p-6">
          <div className="flex items-center gap-2 mb-4">
            <Globe className="w-5 h-5 text-gray-600" />
            <h2 className="text-lg font-medium text-gray-800">
              {t('settings.language.title', '语言设置')}
            </h2>
          </div>

          <div className="space-y-3">
            <p className="text-sm text-gray-600">
              {t('settings.language.description', '选择您偏好的界面语言，更改将立即生效。')}
            </p>
            <div className="flex items-center gap-4">
              <LanguageSelector variant="button" placement="bottom" usePortal={true} />
              <div className="text-xs text-gray-500">
                {t('settings.language.persistence', '语言偏好将自动保存到本地存储')}
              </div>
            </div>
          </div>
        </section>

        {/* Appearance Section */}
        <section className="bg-white rounded-lg border border-gray-200 p-6">
          <div className="flex items-center gap-2 mb-4">
            <Palette className="w-5 h-5 text-gray-600" />
            <h2 className="text-lg font-medium text-gray-800">
              {t('settings.appearance.title', '外观设置')}
            </h2>
          </div>

          <div className="text-sm text-gray-500">
            {t('settings.appearance.comingSoon', '更多外观与主题选项，敬请期待…')}
          </div>
        </section>
      </div>
    </div>
  );
};

export default SettingsPage;

