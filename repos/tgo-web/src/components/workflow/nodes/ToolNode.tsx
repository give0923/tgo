/**
 * Tool Node Component
 * Executes an MCP tool in the workflow - Minimal Clean Redesign
 */

import React, { memo } from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import { Wrench } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import type { ToolNodeData } from '@/types/workflow';
import NodeExecutionOverlay from '../overlays/NodeExecutionOverlay';

const ToolNode: React.FC<NodeProps<ToolNodeData>> = ({ id, data, selected }) => {
  const { t } = useTranslation();
  const hasTool = Boolean(data.tool_id);
  const defaultLabel = t('workflow.node_types.tool.label', 'MCP工具');
  
  return (
    <div
      className={`
        px-5 py-4 rounded-2xl bg-white dark:bg-gray-800 shadow-sm border
        flex flex-col gap-3 min-w-[220px] transition-all duration-200 relative
        ${selected 
          ? 'border-orange-500 ring-4 ring-orange-500/10' 
          : 'border-gray-100 dark:border-gray-700 hover:shadow-md'
        }
      `}
    >
      <NodeExecutionOverlay nodeId={id} label={data.label || defaultLabel} />
      {/* Colored Side Bar */}
      <div className="absolute left-0 top-4 bottom-4 w-1 bg-orange-500 rounded-r-full" />

      <Handle
        type="target"
        position={Position.Top}
        className="!w-3 !h-3 !bg-orange-500 !border-2 !border-white dark:!border-gray-800 !shadow-sm"
      />
      
      <div className="flex items-center gap-4">
        <div className="p-2.5 rounded-xl bg-orange-50 dark:bg-orange-900/20 text-orange-600 dark:text-orange-400">
          <Wrench className="w-6 h-6" />
        </div>
        <div className="min-w-0 flex-1">
          <div className="text-sm font-bold text-gray-900 dark:text-gray-100 truncate">
            {data.label || defaultLabel}
          </div>
          <div className="text-xs text-gray-500 dark:text-gray-400 mt-0.5 truncate">
            {hasTool ? (data.tool_name || data.tool_id) : t('workflow.node_display.not_configured_tool', '未配置工具')}
          </div>
        </div>
      </div>

      <div className="pt-2 border-t border-gray-50 dark:border-gray-700/50 flex items-center justify-between">
        <span className="text-[10px] text-gray-400 uppercase font-medium tracking-wider">
          → result
        </span>
        {!hasTool && (
          <span className="text-[10px] bg-amber-50 dark:bg-amber-900/20 text-amber-600 px-1.5 py-0.5 rounded-md font-bold">
            {t('common.required', 'REQUIRED')}
          </span>
        )}
      </div>
      
      <Handle
        type="source"
        position={Position.Bottom}
        className="!w-3 !h-3 !bg-orange-500 !border-2 !border-white dark:!border-gray-800 !shadow-sm"
      />
    </div>
  );
};

export default memo(ToolNode);
