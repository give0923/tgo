import React from 'react';
import { useTranslation } from 'react-i18next';
import { Outlet, NavLink } from 'react-router-dom';
import { Settings as SettingsIcon } from 'lucide-react';
import { FiSettings, FiCpu } from 'react-icons/fi';
import SettingsSidebar from '@/components/settings/SettingsSidebar';

const SettingsLayout: React.FC = () => {
  const { t } = useTranslation();

  const items: Array<{ id: string; label: string }> = [
    { id: 'general', label: t('settings.menu.general', '\u901a\u7528') },
    { id: 'providers', label: t('settings.menu.providers', '\u6a21\u578b\u63d0\u4f9b\u5546') },
  ];

  const iconMap: Record<string, React.ReactNode> = {
    general: <FiSettings className="w-4 h-4" />,
    providers: <FiCpu className="w-4 h-4" />,
  };

  return (
    <div className="flex-1 flex h-full w-full overflow-hidden">
      <SettingsSidebar />
      <div className="flex-1 overflow-auto">
        <div className="md:hidden bg-white border-b border-gray-200">
          <div className="px-4 py-3">
            <div className="flex items-center gap-2">
              <SettingsIcon className="w-5 h-5 text-gray-700" />
              <h1 className="text-xl font-semibold text-gray-800">{t('settings.title', '\u8bbe\u7f6e')}</h1>
            </div>
          </div>
          <div className="px-2 pb-2 flex gap-2 overflow-x-auto">
            {items.map((item) => (
              <NavLink
                key={item.id}
                to={`/settings/${item.id}`}
                className={({ isActive }) => `whitespace-nowrap px-3 py-1.5 rounded-md text-sm border ${isActive ? 'bg-blue-50 text-blue-600 border-blue-200' : 'bg-white text-gray-700 border-gray-200'}`}
              >
                <span className="inline-flex items-center gap-1.5">
                  {iconMap[item.id]}
                  <span>{item.label}</span>
                </span>
              </NavLink>
            ))}
          </div>
        </div>
        <Outlet />
      </div>
    </div>
  );
};

export default SettingsLayout;

