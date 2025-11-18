import React from 'react';
import { NavLink } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { AI_MENU_ITEMS } from '@/utils/constants';
import type { NavigationItem } from '@/types';

interface AIMenuItemProps {
  item: NavigationItem;
}

// Icon mapping for AI menu items
const ICON_MAP: Record<string, string> = {
  'Bot': 'https://unpkg.com/lucide-static@latest/icons/bot.svg',
  'Wrench': 'https://unpkg.com/lucide-static@latest/icons/wrench.svg'
};

/**
 * AI menu navigation item component using React Router NavLink
 */
const AIMenuItem: React.FC<AIMenuItemProps> = ({ item }) => {
  const { t } = useTranslation();
  return (
    <NavLink
      to={item.path}
      className={({ isActive }) => `
        flex items-center px-3 py-2 rounded-md text-sm transition-colors w-full text-left
        ${isActive
          ? 'bg-blue-50 text-blue-700 font-medium'
          : 'text-gray-600 hover:bg-gray-100/70 hover:text-gray-800'
        }
      `}
    >
      <img src={ICON_MAP[item.icon]} alt="" className="w-4 h-4 mr-2" />
      {t(item.title)}
    </NavLink>
  );
};

/**
 * AI feature menu component
 */
const AIMenu: React.FC = () => {
  const { t } = useTranslation();
  return (
    <aside className="w-64 bg-white/90 backdrop-blur-lg border-r border-gray-200/60 flex flex-col shrink-0">
      {/* Header */}
      <div className="p-4 border-b border-gray-200/60 sticky top-0 bg-white/90 backdrop-blur-lg z-10">
        <h3 className="text-md font-semibold text-gray-800 px-1">{t('ai.menu.title', 'AI 功能')}</h3>
      </div>

      {/* Menu Navigation */}
      <nav className="flex-grow overflow-y-auto p-3 space-y-1">
        {AI_MENU_ITEMS.map((item) => (
          <AIMenuItem
            key={item.id}
            item={item}
          />
        ))}
      </nav>
    </aside>
  );
};

export default AIMenu;
