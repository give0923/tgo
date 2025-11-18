import React from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import Icon from '../ui/Icon';
import { NAVIGATION_ITEMS } from '@/utils/constants';
import type { NavigationItem } from '@/types';

interface NavItemProps {
  item: NavigationItem;
}

/**
 * Navigation item component using React Router NavLink
 */
const NavItem: React.FC<NavItemProps> = ({ item }) => {
  const location = useLocation();
  const { t } = useTranslation();
  const isAIRoute = item.path.startsWith('/ai');

  return (
    <NavLink
      to={item.path}
      className={({ isActive }) => `
        p-2 rounded-lg transition-colors duration-200 block
        ${isActive || (isAIRoute && location.pathname.startsWith('/ai'))
          ? 'bg-blue-100 text-blue-600'
          : 'text-gray-500 hover:bg-gray-200/50 hover:text-gray-700'
        }
      `}
      title={t(item.title)}
    >
      <Icon name={item.icon} size={24} />
    </NavLink>
  );
};



/**
 * Sidebar component with navigation and logo
 */
const Sidebar: React.FC = () => {
  return (
    <aside className="w-16 flex flex-col items-center bg-white/70 backdrop-blur-lg border-r border-gray-200/50 py-4 space-y-4 shrink-0 relative z-20">
      {/* System Logo */}
      <div className="mb-2">
          <img src="/logo.svg" alt="Logo" className="w-full h-full object-contain object-center select-none" />
      </div>

      {/* Navigation */}
      <nav className="flex flex-col items-center space-y-3">
        {NAVIGATION_ITEMS.map((item) => (
          <NavItem key={item.id} item={item} />
        ))}
      </nav>

      {/* Footer spacer */}
      <div className="mt-auto" />
    </aside>
  );
};

export default Sidebar;
