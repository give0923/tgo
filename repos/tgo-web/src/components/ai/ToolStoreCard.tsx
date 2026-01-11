import React from 'react';
import { Star, Download, ShieldCheck } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import type { ToolStoreItem } from '@/types';

interface ToolStoreCardProps {
  tool: ToolStoreItem;
  onClick: (tool: ToolStoreItem) => void;
  onInstall: (e: React.MouseEvent, tool: ToolStoreItem) => void;
  isInstalled?: boolean;
}

const ToolStoreCard: React.FC<ToolStoreCardProps> = ({ tool, onClick, onInstall, isInstalled }) => {
  const { t } = useTranslation();

  return (
    <div 
      onClick={() => onClick(tool)}
      className="group relative bg-white dark:bg-gray-800 rounded-2xl p-5 border border-gray-100 dark:border-gray-700 hover:shadow-xl hover:-translate-y-1 transition-all duration-300 cursor-pointer overflow-hidden"
    >
      {/* Featured Badge */}
      {tool.featured && (
        <div className="absolute top-0 right-0">
          <div className="bg-blue-600 text-white text-[10px] font-bold px-3 py-1 rounded-bl-xl shadow-sm">
            {t('tools.store.featured', '精选')}
          </div>
        </div>
      )}

      <div className="flex items-start gap-4 mb-4">
        {/* Icon */}
        <div className="w-14 h-14 rounded-2xl bg-gray-50 dark:bg-gray-900 flex items-center justify-center text-3xl border border-gray-100 dark:border-gray-700 group-hover:scale-110 transition-transform duration-300">
          {tool.icon || '🛠️'}
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-1.5 mb-0.5">
            <h3 className="font-bold text-gray-900 dark:text-gray-100 truncate group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors">
              {tool.name}
            </h3>
            {tool.verified && (
              <ShieldCheck className="w-4 h-4 text-blue-500 flex-shrink-0" />
            )}
          </div>
          <p className="text-xs text-gray-500 dark:text-gray-400 font-medium">
            {tool.author}
          </p>
        </div>
      </div>

      {/* Description */}
      <p className="text-sm text-gray-600 dark:text-gray-400 line-clamp-2 h-10 mb-4 leading-relaxed">
        {tool.description}
      </p>

      {/* Stats */}
      <div className="flex items-center gap-4 text-[11px] text-gray-500 dark:text-gray-500 mb-5">
        <div className="flex items-center gap-1">
          <Star className="w-3.5 h-3.5 text-amber-400 fill-amber-400" />
          <span className="font-bold text-gray-700 dark:text-gray-300">{tool.rating}</span>
          <span className="opacity-70">({tool.ratingCount})</span>
        </div>
        <div className="flex items-center gap-1">
          <Download className="w-3.5 h-3.5" />
          <span>{tool.downloads > 1000 ? `${(tool.downloads / 1000).toFixed(1)}k` : tool.downloads}</span>
        </div>
      </div>

      {/* Footer / Actions */}
      <div className="flex items-center justify-between gap-3 pt-4 border-t border-gray-50 dark:border-gray-700/50">
        <div className="flex flex-wrap gap-1 items-center">
          {tool.tags.slice(0, 2).map(tag => (
            <span 
              key={tag} 
              className="px-1.5 py-0.5 bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 text-[10px] rounded-md font-medium"
            >
              {tag}
            </span>
          ))}
          {tool.tags.length > 2 && (
            <span className="text-[10px] text-gray-400 font-medium">+{tool.tags.length - 2}</span>
          )}
        </div>

        <button
          onClick={(e) => onInstall(e, tool)}
          disabled={isInstalled}
          className={`px-4 py-1.5 rounded-xl text-xs font-bold transition-all active:scale-95 ${
            isInstalled 
              ? 'bg-gray-100 dark:bg-gray-800 text-gray-400 cursor-not-allowed' 
              : 'bg-blue-600 hover:bg-blue-700 text-white shadow-lg shadow-blue-200 dark:shadow-none'
          }`}
        >
          {isInstalled ? t('tools.store.installed', '已安装') : t('tools.store.install', '安装')}
        </button>
      </div>
    </div>
  );
};

export default ToolStoreCard;
