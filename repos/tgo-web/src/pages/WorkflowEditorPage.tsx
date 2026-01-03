/**
 * Workflow Editor Page
 * Standalone page for editing workflows via route - Minimal Clean Redesign
 */

import React, { useEffect, useState, useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import { useParams, useNavigate } from 'react-router-dom';
import {
  ChevronLeft,
  Settings,
  Loader2,
  ChevronRight,
  Info,
} from 'lucide-react';
import { useWorkflowStore } from '@/stores/workflowStore';
import { useToast } from '@/hooks/useToast';
import { WorkflowEditor, WorkflowToolbar } from '@/components/workflow';
import NodePalette from '@/components/workflow/NodePalette';
import NodeConfigPanel from '@/components/workflow/panels/NodeConfigPanel';
import DebugPanel from '@/components/workflow/panels/DebugPanel';

const WorkflowEditorPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { t } = useTranslation();
  const { showToast } = useToast();
  const [showSettings, setShowSettings] = useState(false);
  const [paletteCollapsed, setPaletteCollapsed] = useState(false);

  const {
    currentWorkflow,
    isLoadingCurrentWorkflow,
    isDirty,
    loadWorkflow,
    createWorkflow,
    updateWorkflowMeta,
    resetEditor,
    selectedNodeId,
    setSelectedNode,
    isDebugPanelOpen,
    setDebugPanelOpen,
  } = useWorkflowStore();

  const selectedNode = useMemo(() => {
    if (!selectedNodeId) return null;
    return currentWorkflow?.definition.nodes.find(n => n.id === selectedNodeId) || null;
  }, [currentWorkflow, selectedNodeId]);

  const creatingRef = React.useRef(false);

  // Load or create workflow based on ID
  useEffect(() => {
    if (id && id !== 'new') {
      loadWorkflow(id);
    } else if (id === 'new' && !creatingRef.current) {
      creatingRef.current = true;
      createWorkflow().then(newWorkflow => {
        // Once created, navigate to the edit route with the real ID
        // to prevent re-creation on refresh/remount
        navigate(`/ai/workflows/${newWorkflow.id}/edit`, { replace: true });
      }).catch(error => {
        creatingRef.current = false;
        console.error('Failed to create workflow:', error);
        showToast('error', t('workflow.messages.createFailed', '创建失败'), '');
      });
    }
    
    return () => {
      resetEditor();
      creatingRef.current = false;
    };
  }, [id, navigate, loadWorkflow, createWorkflow, resetEditor, showToast, t]);

  const handleBack = () => {
    if (isDirty) {
      const confirmed = window.confirm(t('workflow.messages.unsavedChanges', '有未保存的更改，确定要离开吗？'));
      if (!confirmed) return;
    }
    navigate('/ai/workflows');
  };

  return (
    <div className="flex-1 flex flex-col h-full bg-white dark:bg-gray-950 overflow-hidden">
      {/* Header */}
      <header className="flex items-center justify-between px-6 h-14 bg-white/80 dark:bg-gray-900/80 backdrop-blur-md border-b border-gray-100 dark:border-gray-800 flex-shrink-0 z-20">
        <div className="flex items-center gap-6">
          <button
            onClick={handleBack}
            className="flex items-center gap-2 text-gray-500 hover:text-gray-900 dark:hover:text-gray-100 transition-all group"
          >
            <div className="p-1 rounded-full group-hover:bg-gray-100 dark:group-hover:bg-gray-800 transition-colors">
              <ChevronLeft className="w-5 h-5" />
            </div>
            <span className="text-sm font-medium">{t('common.back', '返回')}</span>
          </button>

          <div className="h-6 w-[1px] bg-gray-200 dark:bg-gray-700" />

          {isLoadingCurrentWorkflow ? (
            <div className="flex items-center gap-2 text-gray-400">
              <Loader2 className="w-4 h-4 animate-spin" />
              <span className="text-sm font-medium">{t('common.loading', '加载中...')}</span>
            </div>
          ) : currentWorkflow ? (
            <div className="flex items-center gap-3">
              <div className="flex flex-col">
                <input
                  type="text"
                  value={currentWorkflow.name}
                  onChange={(e) => updateWorkflowMeta({ name: e.target.value })}
                  className="text-base font-bold text-gray-900 dark:text-gray-100 bg-transparent border-none focus:outline-none focus:ring-0 p-0 h-6 min-w-[200px]"
                  placeholder={t('workflow.namePlaceholder', '工作流名称')}
                />
                <div className="flex items-center gap-2">
                  <span className={`text-[10px] uppercase font-bold tracking-widest ${
                    currentWorkflow.status === 'active' ? 'text-green-500' : 'text-amber-500'
                  }`}>
                    {currentWorkflow.status}
                  </span>
                  {isDirty && (
                    <>
                      <span className="text-gray-300 dark:text-gray-600">·</span>
                      <span className="text-[10px] text-amber-500 font-bold uppercase tracking-widest animate-pulse">
                        {t('common.unsaved_changes', 'Unsaved Changes')}
                      </span>
                    </>
                  )}
                </div>
              </div>
            </div>
          ) : null}
        </div>

        <div className="flex items-center gap-4">
          {/* Action Toolbar (Undo, Redo, Validate, Save) */}
          <WorkflowToolbar />

          <div className="h-6 w-[1px] bg-gray-200 dark:bg-gray-700" />

          {/* Settings Toggle */}
          <button
            onClick={() => {
              if (!showSettings) {
                setDebugPanelOpen(false);
                setSelectedNode(null);
              }
              setShowSettings(!showSettings);
            }}
            className={`flex items-center gap-2 px-3 h-8 rounded-lg transition-all border ${
              showSettings
                ? 'bg-gray-100 dark:bg-gray-800 text-gray-900 dark:text-gray-100 border-gray-200 dark:border-gray-700'
                : 'text-gray-500 hover:text-gray-900 dark:hover:text-gray-100 border-transparent hover:bg-gray-50 dark:hover:bg-gray-800'
            }`}
            title={t('workflow.settings', '设置')}
          >
            <Settings className="w-4 h-4" />
            <span className="text-xs font-semibold">{t('common.settings', '设置')}</span>
          </button>
        </div>
      </header>

      {/* Main Content Area */}
      <div className="flex-1 flex overflow-hidden bg-gray-50/50 dark:bg-gray-950/50">
        {/* Left Side: Node Palette */}
        <NodePalette 
          isCollapsed={paletteCollapsed} 
          onToggleCollapse={() => setPaletteCollapsed(!paletteCollapsed)} 
        />

        {/* Center: Editor */}
        <div className="flex-1 relative overflow-hidden">
          {isLoadingCurrentWorkflow ? (
            <div className="absolute inset-0 flex items-center justify-center bg-white/50 dark:bg-gray-900/50 backdrop-blur-sm z-10">
              <div className="text-center">
                <Loader2 className="w-8 h-8 animate-spin text-blue-500 mx-auto mb-3" />
                <p className="text-gray-500 dark:text-gray-400 text-sm font-medium">
                  {t('workflow.loading', '加载工作流...')}
                </p>
              </div>
            </div>
          ) : (
            <WorkflowEditor />
          )}
        </div>

        {/* Right Side: Panels (Overlay or Fixed) */}
        {isDebugPanelOpen ? (
          <DebugPanel />
        ) : selectedNode ? (
          <NodeConfigPanel node={selectedNode} />
        ) : showSettings && currentWorkflow ? (
          <div className="w-80 bg-white dark:bg-gray-900 border-l border-gray-100 dark:border-gray-800 flex flex-col shadow-2xl z-30 transition-all animate-in slide-in-from-right duration-300">
            <div className="p-6 border-b border-gray-50 dark:border-gray-800 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="p-1.5 bg-gray-100 dark:bg-gray-800 rounded-lg">
                  <Settings className="w-4 h-4 text-gray-600 dark:text-gray-400" />
                </div>
                <h3 className="font-bold text-gray-900 dark:text-gray-100 text-sm">
                  {t('workflow.settings', '工作流设置')}
                </h3>
              </div>
              <button 
                onClick={() => setShowSettings(false)}
                className="p-1 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-md transition-colors"
              >
                <ChevronRight className="w-4 h-4 text-gray-400" />
              </button>
            </div>
            
            <div className="flex-1 overflow-y-auto p-6 space-y-6">
              {/* Name */}
              <div className="space-y-2">
                <label className="text-[11px] uppercase font-bold text-gray-400 tracking-wider">
                  {t('workflow.fields.name', '名称')}
                </label>
                <input
                  type="text"
                  value={currentWorkflow.name}
                  onChange={(e) => updateWorkflowMeta({ name: e.target.value })}
                  className="w-full px-4 py-2 bg-gray-50 dark:bg-gray-800/50 border border-gray-100 dark:border-gray-700 rounded-xl focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 outline-none transition-all text-sm dark:text-gray-100"
                />
              </div>

              {/* Description */}
              <div className="space-y-2">
                <label className="text-[11px] uppercase font-bold text-gray-400 tracking-wider">
                  {t('workflow.fields.description', '描述')}
                </label>
                <textarea
                  value={currentWorkflow.description || ''}
                  onChange={(e) => updateWorkflowMeta({ description: e.target.value })}
                  rows={4}
                  className="w-full px-4 py-2 bg-gray-50 dark:bg-gray-800/50 border border-gray-100 dark:border-gray-700 rounded-xl focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 outline-none transition-all text-sm dark:text-gray-100 resize-none leading-relaxed"
                  placeholder={t('workflow.fields.description_placeholder', 'Describe what this workflow does...')}
                />
              </div>

              {/* Status */}
              <div className="space-y-2">
                <label className="text-[11px] uppercase font-bold text-gray-400 tracking-wider">
                  {t('workflow.fields.status', '状态')}
                </label>
                <div className="grid grid-cols-3 gap-2">
                  {(['draft', 'active', 'archived'] as const).map((status) => (
                    <button
                      key={status}
                      onClick={() => updateWorkflowMeta({ status })}
                      className={`
                        py-2 text-[10px] font-bold uppercase tracking-widest rounded-lg border transition-all
                        ${currentWorkflow.status === status
                          ? 'bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800 text-blue-600 dark:text-blue-400'
                          : 'bg-white dark:bg-gray-800 border-gray-100 dark:border-gray-700 text-gray-400 hover:border-gray-200 dark:hover:border-gray-600'
                        }
                      `}
                    >
                      {status}
                    </button>
                  ))}
                </div>
              </div>

              {/* Tags */}
              <div className="space-y-2">
                <label className="text-[11px] uppercase font-bold text-gray-400 tracking-wider">
                  {t('workflow.fields.tags', '标签')}
                </label>
                <input
                  type="text"
                  value={currentWorkflow.tags.join(', ')}
                  onChange={(e) => updateWorkflowMeta({ 
                    tags: e.target.value.split(',').map(t => t.trim()).filter(Boolean)
                  })}
                  placeholder={t('workflow.tagsPlaceholder', '用逗号分隔')}
                  className="w-full px-4 py-2 bg-gray-50 dark:bg-gray-800/50 border border-gray-100 dark:border-gray-700 rounded-xl focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 outline-none transition-all text-sm dark:text-gray-100"
                />
              </div>

              {/* Info Box */}
              <div className="p-4 bg-blue-50/50 dark:bg-blue-900/10 rounded-2xl border border-blue-100/50 dark:border-blue-800/30">
                <div className="flex items-center gap-2 mb-3">
                  <Info className="w-3.5 h-3.5 text-blue-500" />
                  <span className="text-[10px] font-bold text-blue-600 uppercase tracking-widest">{t('workflow.fields.workflow_info', 'Workflow Info')}</span>
                </div>
                <div className="space-y-2">
                  <div className="flex justify-between items-center">
                    <span className="text-[10px] text-gray-400 font-medium uppercase">{t('workflow.fields.version', 'Version')}</span>
                    <span className="text-[10px] font-bold text-gray-600 dark:text-gray-300">v{currentWorkflow.version}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-[10px] text-gray-400 font-medium uppercase">{t('workflow.fields.total_nodes', 'Total Nodes')}</span>
                    <span className="text-[10px] font-bold text-gray-600 dark:text-gray-300">{currentWorkflow.definition.nodes.length}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-[10px] text-gray-400 font-medium uppercase">{t('common.tableCreated', 'Created')}</span>
                    <span className="text-[10px] font-bold text-gray-600 dark:text-gray-300">{new Date(currentWorkflow.created_at).toLocaleDateString()}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        ) : null}
      </div>
    </div>
  );
};

export default WorkflowEditorPage;
