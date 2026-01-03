/**
 * Workflow Toolbar Component
 * Contains simplified workflow actions for the top bar
 */

import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import {
  Save,
  Undo2,
  Redo2,
  CheckCircle,
  Loader2,
  Bug,
} from 'lucide-react';
import { useWorkflowStore } from '@/stores/workflowStore';
import { useToast } from '@/hooks/useToast';

/**
 * Workflow Toolbar Component
 */
const WorkflowToolbar: React.FC = () => {
  const { t } = useTranslation();
  const { showToast } = useToast();
  const [isSaving, setIsSaving] = useState(false);
  const [isValidating, setIsValidating] = useState(false);

  const {
    currentWorkflow,
    isDirty,
    history,
    historyIndex,
    saveWorkflow,
    undo,
    redo,
    validate,
    isDebugPanelOpen,
    setDebugPanelOpen,
    isExecuting,
  } = useWorkflowStore();

  const canUndo = historyIndex > 0;
  const canRedo = historyIndex < history.length - 1;

  const handleSave = async () => {
    if (!currentWorkflow || isSaving) return;

    setIsSaving(true);
    try {
      await saveWorkflow();
      showToast('success', t('workflow.messages.saveSuccess', '保存成功'), t('workflow.messages.saveSuccessDesc', '工作流已保存'));
    } catch (error) {
      showToast('error', t('workflow.messages.saveFailed', '保存失败'), t('workflow.messages.saveFailedDesc', '保存工作流时发生错误'));
    } finally {
      setIsSaving(false);
    }
  };

  const handleValidate = async () => {
    if (!currentWorkflow || isValidating) return;

    setIsValidating(true);
    try {
      const isValid = await validate();
      if (isValid) {
        showToast('success', t('workflow.messages.validateSuccess', '验证通过'), t('workflow.messages.validateSuccessDesc', '工作流配置正确'));
      } else {
        showToast('warning', t('workflow.messages.validateFailed', '验证失败'), t('workflow.messages.validateFailedDesc', '请检查工作流配置'));
      }
    } finally {
      setIsValidating(false);
    }
  };

  if (!currentWorkflow) return null;

  return (
    <div className="flex items-center gap-2">
      {/* Undo/Redo */}
      <div className="flex items-center bg-gray-50 dark:bg-gray-900 rounded-lg p-0.5 border border-gray-200 dark:border-gray-700 mr-2">
        <button
          onClick={undo}
          disabled={!canUndo}
          className="p-1.5 text-gray-500 hover:text-gray-900 dark:hover:text-gray-100 hover:bg-white dark:hover:bg-gray-800 rounded-md disabled:opacity-30 disabled:cursor-not-allowed transition-all"
          title={t('workflow.actions.undo', '撤销')}
        >
          <Undo2 className="w-4 h-4" />
        </button>
        <div className="w-[1px] h-4 bg-gray-200 dark:bg-gray-700 mx-0.5" />
        <button
          onClick={redo}
          disabled={!canRedo}
          className="p-1.5 text-gray-500 hover:text-gray-900 dark:hover:text-gray-100 hover:bg-white dark:hover:bg-gray-800 rounded-md disabled:opacity-30 disabled:cursor-not-allowed transition-all"
          title={t('workflow.actions.redo', '重做')}
        >
          <Redo2 className="w-4 h-4" />
        </button>
      </div>

      {/* Debug */}
      <button
        onClick={() => setDebugPanelOpen(!isDebugPanelOpen)}
        className={`flex items-center gap-1.5 px-3 h-8 text-xs font-semibold rounded-lg transition-all shadow-sm border ${
          isDebugPanelOpen 
            ? 'bg-orange-50 dark:bg-orange-900/20 text-orange-600 dark:text-orange-400 border-orange-200 dark:border-orange-800' 
            : 'bg-white dark:bg-gray-800 text-gray-600 dark:text-gray-300 border-gray-200 dark:border-gray-700 hover:border-orange-500 hover:text-orange-600 dark:hover:text-orange-400'
        }`}
      >
        {isExecuting ? (
          <Loader2 className="w-3.5 h-3.5 animate-spin text-orange-500" />
        ) : (
          <Bug className="w-3.5 h-3.5" />
        )}
        <span>{t('workflow.actions.debug', '调试')}</span>
      </button>

      {/* Validate */}
      <button
        onClick={handleValidate}
        disabled={isValidating}
        className="flex items-center gap-1.5 px-3 h-8 text-xs font-semibold text-gray-600 dark:text-gray-300 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 hover:border-blue-500 hover:text-blue-600 dark:hover:text-blue-400 rounded-lg transition-all disabled:opacity-50 shadow-sm"
      >
        {isValidating ? (
          <Loader2 className="w-3.5 h-3.5 animate-spin" />
        ) : (
          <CheckCircle className="w-3.5 h-3.5" />
        )}
        <span>{t('workflow.actions.validate', '验证')}</span>
      </button>

      {/* Save */}
      <button
        onClick={handleSave}
        disabled={!isDirty || isSaving}
        className="flex items-center gap-1.5 px-4 h-8 text-xs font-bold text-white bg-blue-600 hover:bg-blue-700 dark:bg-blue-700 dark:hover:bg-blue-800 rounded-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-sm shadow-blue-200 dark:shadow-none"
      >
        {isSaving ? (
          <Loader2 className="w-3.5 h-3.5 animate-spin" />
        ) : (
          <Save className="w-3.5 h-3.5" />
        )}
        <span>{t('workflow.actions.save', '保存')}</span>
        {isDirty && <div className="w-1.5 h-1.5 bg-white rounded-full animate-pulse ml-0.5" />}
      </button>
    </div>
  );
};

export default WorkflowToolbar;
