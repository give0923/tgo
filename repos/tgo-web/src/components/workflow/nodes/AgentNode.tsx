/**
 * Agent Node Component
 * Calls another AI Agent in the workflow - Minimal Clean Redesign
 */

import React, { memo } from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import { Bot } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import type { AgentNodeData } from '@/types/workflow';
import NodeExecutionOverlay from '../overlays/NodeExecutionOverlay';

const AgentNode: React.FC<NodeProps<AgentNodeData>> = ({ id, data, selected }) => {
  const { t } = useTranslation();
  const hasAgent = Boolean(data.agent_id);
  const defaultLabel = t('workflow.node_types.agent.label', 'AI Agent');
  
  return (
    <div
      className={`
        px-5 py-4 rounded-2xl bg-white dark:bg-gray-800 shadow-sm border
        flex flex-col gap-3 min-w-[220px] transition-all duration-200 relative
        ${selected 
          ? 'border-blue-500 ring-4 ring-blue-500/10' 
          : 'border-gray-100 dark:border-gray-700 hover:shadow-md'
        }
      `}
    >
      <NodeExecutionOverlay nodeId={id} label={data.label || defaultLabel} />
      {/* Colored Side Bar */}
      <div className="absolute left-0 top-4 bottom-4 w-1 bg-blue-500 rounded-r-full" />

      <Handle
        type="target"
        position={Position.Top}
        className="!w-3 !h-3 !bg-blue-500 !border-2 !border-white dark:!border-gray-800 !shadow-sm"
      />
      
      <div className="flex items-center gap-4">
        <div className="p-2.5 rounded-xl bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400">
          <Bot className="w-6 h-6" />
        </div>
        <div className="min-w-0 flex-1">
          <div className="text-sm font-bold text-gray-900 dark:text-gray-100 truncate">
            {data.label || defaultLabel}
          </div>
          <div className="text-xs text-gray-500 dark:text-gray-400 mt-0.5 truncate">
            {hasAgent ? (data.agent_name || data.agent_id) : t('workflow.node_display.not_configured_agent', '未配置员工')}
          </div>
        </div>
      </div>

      <div className="pt-2 border-t border-gray-50 dark:border-gray-700/50 flex items-center justify-between">
        <span className="text-[10px] text-gray-400 uppercase font-medium tracking-wider">
          → text
        </span>
        {!hasAgent && (
          <span className="text-[10px] bg-amber-50 dark:bg-amber-900/20 text-amber-600 px-1.5 py-0.5 rounded-md font-bold">
            {t('common.required', 'REQUIRED')}
          </span>
        )}
      </div>
      
      <Handle
        type="source"
        position={Position.Bottom}
        className="!w-3 !h-3 !bg-blue-500 !border-2 !border-white dark:!border-gray-800 !shadow-sm"
      />
    </div>
  );
};

export default memo(AgentNode);
