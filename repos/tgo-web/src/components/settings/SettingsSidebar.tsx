import React from 'react';
import { NavLink } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Settings as SettingsIcon } from 'lucide-react';
import { FiSettings, FiCpu, FiInfo, FiLogOut } from 'react-icons/fi';
import { useAuthStore } from '@/stores/authStore';

interface SettingsSidebarProps {
  className?: string;
}

const SettingsSidebar: React.FC<SettingsSidebarProps> = ({ className = '' }) => {
  const { t } = useTranslation();
  const { logout, isAuthenticated } = useAuthStore();

  const items: Array<{ id: string; label: string }> = [
    { id: 'general', label: t('settings.menu.general', '通用') },
    { id: 'providers', label: t('settings.menu.providers', '模型提供商') },
  ];
  const iconMap: Record<string, React.ReactNode> = {
    general: <FiSettings className="w-4 h-4" />,
    providers: <FiCpu className="w-4 h-4" />,
  };

  return (
    <aside className={`hidden md:flex w-64 flex-col bg-white border-r border-gray-200 shrink-0 ${className}`}>
      <div className="px-4 py-3 border-b border-gray-200">
        <div className="flex items-center gap-2">
          <SettingsIcon className="w-4 h-4 text-gray-700" />
          <h2 className="text-base font-semibold text-gray-800">{t('settings.title', '设置')}</h2>
        </div>
      </div>
      <nav className="flex-1 overflow-y-auto p-2 space-y-1">
        {items.map((item) => (
          <NavLink
            key={item.id}
            to={`/settings/${item.id}`}
            className={({ isActive }) => `
              block px-3 py-2 rounded-md text-sm transition-colors
              ${isActive ? 'bg-blue-100 text-blue-600' : 'text-gray-700 hover:bg-gray-50'}
            `}
          >
            <span className="inline-flex items-center gap-2">
              {iconMap[item.id]}
              <span>{item.label}</span>
            </span>
          </NavLink>
        ))}
      </nav>
      <div className="p-2 border-t border-gray-200 space-y-1">
        <NavLink
          to="/settings/about"
          className={({ isActive }) => `
            block px-3 py-2 rounded-md text-sm transition-colors
            ${isActive ? 'bg-blue-100 text-blue-600' : 'text-gray-700 hover:bg-gray-50'}
          `}
        >
          <span className="inline-flex items-center gap-2">
            <FiInfo className="w-4 h-4" />
            <span>{t('settings.menu.about', '关于')}</span>
          </span>
        </NavLink>
        {isAuthenticated && (
          <button
            onClick={async () => {
              try {
                await logout();
              } catch (error) {
                console.error('Logout failed:', error);
              }
            }}
            className="w-full flex items-center gap-2 px-3 py-2 rounded-md text-sm text-red-600 hover:bg-red-50 transition-colors"
          >
            <FiLogOut className="w-4 h-4" />
            <span>{t('settings.menu.logout', '退出登录')}</span>
          </button>
        )}
      </div>
    </aside>
  );
};

export default SettingsSidebar;
