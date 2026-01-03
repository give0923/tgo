/**
 * LLM Node Component
 * Direct LLM call in the workflow - Minimal Clean Redesign
 */

import React, { memo } from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import { MessageSquare } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import type { LLMNodeData } from '@/types/workflow';
import NodeExecutionOverlay from '../overlays/NodeExecutionOverlay';

const LLMNode: React.FC<NodeProps<LLMNodeData>> = ({ id, data, selected }) => {
  const { t } = useTranslation();
  const hasPrompt = Boolean(data.user_prompt);
  const defaultLabel = t('workflow.node_types.llm.label', 'LLM调用');
  
  const getPromptPreview = () => {
    if (!data.user_prompt) return t('workflow.node_display.not_configured_prompt', '未配置提示词');
    return data.user_prompt.length > 40 
      ? `${data.user_prompt.slice(0, 40)}...` 
      : data.user_prompt;
  };
  
  return (
    <div
      className={`
        px-5 py-4 rounded-2xl bg-white dark:bg-gray-800 shadow-sm border
        flex flex-col gap-3 min-w-[260px] transition-all duration-200 relative
        ${selected 
          ? 'border-cyan-500 ring-4 ring-cyan-500/10' 
          : 'border-gray-100 dark:border-gray-700 hover:shadow-md'
        }
      `}
    >
      <NodeExecutionOverlay nodeId={id} label={data.label || defaultLabel} />
      {/* Colored Side Bar */}
      <div className="absolute left-0 top-4 bottom-4 w-1 bg-cyan-500 rounded-r-full" />

      <Handle
        type="target"
        position={Position.Top}
        className="!w-3 !h-3 !bg-cyan-500 !border-2 !border-white dark:!border-gray-800 !shadow-sm"
      />
      
      <div className="flex items-center gap-4">
        <div className="p-2.5 rounded-xl bg-cyan-50 dark:bg-cyan-900/20 text-cyan-600 dark:text-cyan-400">
          <MessageSquare className="w-6 h-6" />
        </div>
        <div className="min-w-0 flex-1">
          <div className="text-sm font-bold text-gray-900 dark:text-gray-100 truncate">
            {data.label || defaultLabel}
          </div>
          {data.model_name && (
            <div className="text-[10px] text-cyan-600 font-bold uppercase tracking-tighter mt-0.5">
              {data.model_name}
            </div>
          )}
        </div>
      </div>
      
      <div className="bg-gray-50 dark:bg-gray-900/50 p-3 rounded-xl border border-gray-100/50 dark:border-gray-700/50">
        <div className="text-[11px] text-gray-400 font-medium mb-1 uppercase tracking-wider">{t('workflow.node_display.prompt_preview', 'Prompt Preview')}</div>
        <p className="text-xs text-gray-600 dark:text-gray-300 line-clamp-2 leading-relaxed italic">
          "{getPromptPreview()}"
        </p>
      </div>
      
      <div className="pt-2 border-t border-gray-50 dark:border-gray-700/50 flex items-center justify-between">
        <span className="text-[10px] text-gray-400 uppercase font-medium tracking-wider">
          → text
        </span>
        {!hasPrompt && (
          <span className="text-[10px] bg-amber-50 dark:bg-amber-900/20 text-amber-600 px-1.5 py-0.5 rounded-md font-bold">
            {t('common.required', 'REQUIRED')}
          </span>
        )}
      </div>
      
      <Handle
        type="source"
        position={Position.Bottom}
        className="!w-3 !h-3 !bg-cyan-500 !border-2 !border-white dark:!border-gray-800 !shadow-sm"
      />
    </div>
  );
};

export default memo(LLMNode);
