/**
 * Node Palette Component
 * Sidebar for dragging new nodes into the workflow canvas
 */

import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import {
  Search,
  Play,
  Square,
  Bot,
  Wrench,
  GitBranch,
  MessageSquare,
  GitMerge,
  ChevronLeft,
  ChevronRight,
  Globe,
  LayoutGrid,
  Clock,
  Zap,
} from 'lucide-react';
import { NODE_TYPE_CONFIG, type WorkflowNodeType } from '@/types/workflow';

// Icon mapping
const iconMap: Record<string, React.ComponentType<{ className?: string }>> = {
  Play,
  Square,
  Bot,
  Wrench,
  GitBranch,
  MessageSquare,
  GitMerge,
  Globe,
  LayoutGrid,
  Clock,
  Zap,
};

interface NodePaletteProps {
  isCollapsed: boolean;
  onToggleCollapse: () => void;
}

const CATEGORIES = [
  { id: 'trigger', label: 'workflow.categories.trigger', defaultLabel: '触发节点' },
  { id: 'ai', label: 'workflow.categories.ai', defaultLabel: 'AI 能力' },
  { id: 'logic', label: 'workflow.categories.logic', defaultLabel: '逻辑控制' },
  { id: 'external', label: 'workflow.categories.external', defaultLabel: '外部集成' },
  { id: 'output', label: 'workflow.categories.output', defaultLabel: '输出' },
] as const;

const NodePalette: React.FC<NodePaletteProps> = ({ isCollapsed, onToggleCollapse }) => {
  const { t } = useTranslation();
  const [searchQuery, setSearchQuery] = useState('');

  const nodeTypes: WorkflowNodeType[] = [
    'input',
    'timer',
    'webhook',
    'event',
    'agent',
    'llm',
    'condition',
    'parallel',
    'classifier',
    'tool',
    'api',
    'answer',
  ];

  const filteredNodeTypes = nodeTypes.filter((type) => {
    const config = NODE_TYPE_CONFIG[type];
    const label = t(`workflow.node_types.${type}.label`, config.label);
    const description = t(`workflow.node_types.${type}.description`, config.description);
    return (
      label.toLowerCase().includes(searchQuery.toLowerCase()) ||
      description.toLowerCase().includes(searchQuery.toLowerCase())
    );
  });

  // Group filtered nodes by category
  const groupedNodes = CATEGORIES.map(cat => ({
    ...cat,
    nodes: filteredNodeTypes.filter(type => NODE_TYPE_CONFIG[type].category === cat.id)
  })).filter(cat => cat.nodes.length > 0);

  const handleDragStart = (event: React.DragEvent, nodeType: WorkflowNodeType) => {
    event.dataTransfer.setData('application/reactflow', nodeType);
    event.dataTransfer.setData('text/plain', nodeType); // Fallback
    event.dataTransfer.effectAllowed = 'move';
  };

  const renderNodeItem = (type: WorkflowNodeType) => {
    const config = NODE_TYPE_CONFIG[type];
    const label = t(`workflow.node_types.${type}.label`, config.label);
    const description = t(`workflow.node_types.${type}.description`, config.description);
    const Icon = iconMap[config.icon] || Play;
    
    const colorClasses: Record<string, string> = {
      green: 'text-green-500 bg-green-50 dark:bg-green-900/20',
      red: 'text-red-500 bg-red-50 dark:bg-red-900/20',
      blue: 'text-blue-500 bg-blue-50 dark:bg-blue-900/20',
      orange: 'text-orange-500 bg-orange-50 dark:bg-orange-900/20',
      purple: 'text-purple-500 bg-purple-50 dark:bg-purple-900/20',
      cyan: 'text-cyan-500 bg-cyan-50 dark:bg-cyan-900/20',
      indigo: 'text-indigo-500 bg-indigo-50 dark:bg-indigo-900/20',
    };

    return (
      <div
        key={type}
        draggable
        onDragStart={(e) => handleDragStart(e, type)}
        className={`
          group flex items-start gap-3 p-2 rounded-xl border border-transparent
          hover:border-gray-200 dark:hover:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700/50
          cursor-grab active:cursor-grabbing transition-all duration-200
          ${isCollapsed ? 'justify-center' : ''}
        `}
        title={isCollapsed ? label : ''}
      >
        <div className={`p-2 rounded-lg shrink-0 ${colorClasses[config.color] || colorClasses.blue}`}>
          <Icon className="w-5 h-5" />
        </div>
        
        {!isCollapsed && (
          <div className="min-w-0">
            <div className="text-sm font-medium text-gray-800 dark:text-gray-200 truncate">
              {label}
            </div>
            <div className="text-[10px] text-gray-400 dark:text-gray-500 line-clamp-1 mt-0.5 leading-relaxed">
              {description}
            </div>
          </div>
        )}
      </div>
    );
  };

  return (
    <div
      className={`
        bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 
        flex flex-col transition-all duration-300 relative
        ${isCollapsed ? 'w-16' : 'w-64'}
      `}
    >
      {/* Collapse Toggle Button */}
      <button
        onClick={onToggleCollapse}
        className="absolute -right-3 top-10 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-full p-1 shadow-sm z-10 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
      >
        {isCollapsed ? (
          <ChevronRight className="w-3 h-3 text-gray-500" />
        ) : (
          <ChevronLeft className="w-3 h-3 text-gray-500" />
        )}
      </button>

      {/* Header */}
      {!isCollapsed && (
        <div className="p-4 border-b border-gray-100 dark:border-gray-700">
          <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-100 mb-3">
            {t('workflow.palette.title', '组件库')}
          </h3>
          <div className="relative">
            <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder={t('workflow.palette.search', '搜索组件...')}
              className="w-full pl-9 pr-3 py-1.5 text-xs bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg focus:ring-2 focus:ring-blue-500 dark:text-gray-100 outline-none transition-all"
            />
          </div>
        </div>
      )}

      {/* Node List with Categories */}
      <div className="flex-1 overflow-y-auto p-3 space-y-6">
        {groupedNodes.map((cat) => (
          <div key={cat.id} className="space-y-2">
            {!isCollapsed && (
              <h4 className="px-2 text-[10px] font-bold text-gray-400 uppercase tracking-widest">
                {t(cat.label, cat.defaultLabel)}
              </h4>
            )}
            <div className="space-y-1">
              {cat.nodes.map(type => renderNodeItem(type))}
            </div>
          </div>
        ))}
        
        {groupedNodes.length === 0 && (
          <div className="text-center py-8">
            <p className="text-xs text-gray-400">{t('workflow.palette.noMatch', '未找到匹配组件')}</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default NodePalette;
