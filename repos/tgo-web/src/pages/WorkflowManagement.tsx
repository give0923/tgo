/**
 * Workflow Management Page
 * List and manage AI Agent workflows
 */

import React, { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import {
  Plus,
  Search,
  GitBranch,
  MoreVertical,
  Edit,
  Copy,
  Trash2,
  RefreshCw,
  Eye,
} from 'lucide-react';
import { useWorkflowStore } from '@/stores/workflowStore';
import { useToast } from '@/hooks/useToast';
import { useDebouncedValue } from '@/hooks/useDebouncedValue';
import ConfirmDialog from '@/components/ui/ConfirmDialog';
import type { WorkflowSummary, WorkflowStatus } from '@/types/workflow';

/**
 * Workflow Card Component
 */
interface WorkflowCardProps {
  workflow: WorkflowSummary;
  onEdit: (id: string) => void;
  onDuplicate: (id: string) => void;
  onDelete: (id: string) => void;
}

const WorkflowCard: React.FC<WorkflowCardProps> = ({
  workflow,
  onEdit,
  onDuplicate,
  onDelete,
}) => {
  const { t } = useTranslation();
  const [showMenu, setShowMenu] = useState(false);

  const getStatusBadge = (status: WorkflowStatus) => {
    const styles: Record<string, string> = {
      active: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300',
      draft: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-300',
      archived: 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400',
    };
    const labels: Record<string, string> = {
      active: t('workflow.status.active', '已启用'),
      draft: t('workflow.status.draft', '草稿'),
      archived: t('workflow.status.archived', '已归档'),
    };
    return (
      <span className={`px-2 py-0.5 text-xs rounded-full font-medium ${styles[status] || styles.draft}`}>
        {labels[status] || status}
      </span>
    );
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5 hover:shadow-lg transition-all duration-200 group">
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-purple-500 to-indigo-600 flex items-center justify-center text-white">
            <GitBranch className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-base font-semibold text-gray-900 dark:text-gray-100">
              {workflow.name}
            </h3>
            <div className="flex items-center gap-2 mt-0.5">
              {getStatusBadge(workflow.status)}
              <span className="text-xs text-gray-500 dark:text-gray-400">
                v{workflow.version}
              </span>
            </div>
          </div>
        </div>

        {/* Menu */}
        <div className="relative">
          <button
            onClick={() => setShowMenu(!showMenu)}
            className="p-1.5 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg opacity-0 group-hover:opacity-100 transition-all"
          >
            <MoreVertical className="w-4 h-4" />
          </button>

          {showMenu && (
            <>
              <div className="fixed inset-0 z-10" onClick={() => setShowMenu(false)} />
              <div className="absolute right-0 top-full mt-1 w-40 bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 py-1 z-20">
                <button
                  onClick={() => { onEdit(workflow.id); setShowMenu(false); }}
                  className="w-full flex items-center gap-2 px-3 py-2 text-sm text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700"
                >
                  <Edit className="w-4 h-4" />
                  {t('common.edit', '编辑')}
                </button>
                <button
                  onClick={() => { onDuplicate(workflow.id); setShowMenu(false); }}
                  className="w-full flex items-center gap-2 px-3 py-2 text-sm text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700"
                >
                  <Copy className="w-4 h-4" />
                  {t('common.duplicate', '复制')}
                </button>
                <button
                  onClick={() => { onDelete(workflow.id); setShowMenu(false); }}
                  className="w-full flex items-center gap-2 px-3 py-2 text-sm text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20"
                >
                  <Trash2 className="w-4 h-4" />
                  {t('common.delete', '删除')}
                </button>
              </div>
            </>
          )}
        </div>
      </div>

      {/* Description */}
      <p className="text-sm text-gray-600 dark:text-gray-400 line-clamp-2 mb-3">
        {workflow.description || t('workflow.noDescription', '暂无描述')}
      </p>

      {/* Tags */}
      {workflow.tags.length > 0 && (
        <div className="flex flex-wrap gap-1 mb-3">
          {workflow.tags.slice(0, 3).map((tag) => (
            <span
              key={tag}
              className="px-2 py-0.5 text-xs bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 rounded"
            >
              {tag}
            </span>
          ))}
          {workflow.tags.length > 3 && (
            <span className="text-xs text-gray-500 dark:text-gray-400">
              +{workflow.tags.length - 3}
            </span>
          )}
        </div>
      )}

      {/* Footer */}
      <div className="flex items-center justify-between pt-3 border-t border-gray-100 dark:border-gray-700">
        <span className="text-xs text-gray-500 dark:text-gray-400">
          {t('workflow.lastUpdated', '更新于')} {new Date(workflow.updated_at).toLocaleDateString()}
        </span>
        <button
          onClick={() => onEdit(workflow.id)}
          className="flex items-center gap-1 text-sm text-purple-600 dark:text-purple-400 hover:text-purple-700 dark:hover:text-purple-300"
        >
          <Eye className="w-4 h-4" />
          {t('common.view', '查看')}
        </button>
      </div>
    </div>
  );
};

/**
 * Workflow Management Page Component
 */
const WorkflowManagement: React.FC = () => {
  const { t } = useTranslation();
  const { showToast } = useToast();
  const navigate = useNavigate();
  
  const {
    workflows,
    isLoadingWorkflows,
    workflowsError,
    loadWorkflows,
    createWorkflow,
    deleteWorkflow,
    duplicateWorkflow,
  } = useWorkflowStore();

  const [searchQuery, setSearchQuery] = useState('');
  const debouncedSearch = useDebouncedValue(searchQuery, 300);
  const [statusFilter, setStatusFilter] = useState<WorkflowStatus | 'all'>('all');

  // Delete confirmation
  const [deleteTarget, setDeleteTarget] = useState<WorkflowSummary | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);

  // Load workflows on mount
  useEffect(() => {
    loadWorkflows();
  }, []);

  const [isCreating, setIsCreating] = useState(false);

  // Filter workflows
  const filteredWorkflows = React.useMemo(() => {
    let filtered = workflows;

    // Status filter
    if (statusFilter !== 'all') {
      filtered = filtered.filter(wf => wf.status === statusFilter);
    }

    // Search filter
    if (debouncedSearch.trim()) {
      const query = debouncedSearch.toLowerCase();
      filtered = filtered.filter(wf =>
        wf.name.toLowerCase().includes(query) ||
        (wf.description && wf.description.toLowerCase().includes(query))
      );
    }

    return filtered;
  }, [workflows, statusFilter, debouncedSearch]);

  // Handlers
  const handleCreate = async () => {
    if (isCreating) return;
    setIsCreating(true);
    try {
      const newWorkflow = await createWorkflow();
      navigate(`/ai/workflows/${newWorkflow.id}/edit`);
    } catch (error) {
      console.error('Failed to create workflow:', error);
      showToast('error', t('workflow.messages.createFailed', '创建失败'), '');
    } finally {
      setIsCreating(false);
    }
  };

  const handleEdit = (id: string) => {
    navigate(`/ai/workflows/${id}/edit`);
  };

  const handleDuplicate = async (id: string) => {
    try {
      await duplicateWorkflow(id);
      showToast('success', t('workflow.messages.duplicateSuccess', '复制成功'), '');
    } catch {
      showToast('error', t('workflow.messages.duplicateFailed', '复制失败'), '');
    }
  };

  const handleDeleteConfirm = async () => {
    if (!deleteTarget) return;

    setIsDeleting(true);
    try {
      await deleteWorkflow(deleteTarget.id);
      showToast('success', t('workflow.messages.deleteSuccess', '删除成功'), '');
      setDeleteTarget(null);
    } catch {
      showToast('error', t('workflow.messages.deleteFailed', '删除失败'), '');
    } finally {
      setIsDeleting(false);
    }
  };

  const handleRefresh = () => {
    loadWorkflows();
  };

  return (
    <main className="flex-grow flex flex-col bg-gradient-to-br from-gray-50 to-gray-100 dark:from-gray-900 dark:to-gray-800">
      {/* Header */}
      <header className="px-6 py-4 border-b border-gray-200/80 dark:border-gray-700 flex justify-between items-center bg-white/60 dark:bg-gray-800/60 backdrop-blur-lg sticky top-0 z-10">
        <div className="flex items-center space-x-4">
          <GitBranch className="w-6 h-6 text-purple-600 dark:text-purple-400" />
          <h2 className="text-lg font-semibold text-gray-800 dark:text-gray-100">
            {t('workflow.management.title', '工作流管理')}
          </h2>
        </div>
        <div className="flex items-center space-x-2">
          <button
            onClick={handleRefresh}
            className="flex items-center px-3 py-1.5 text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-md transition-colors"
            title={t('common.refresh', '刷新')}
          >
            <RefreshCw className={`w-4 h-4 ${isLoadingWorkflows ? 'animate-spin' : ''}`} />
          </button>
          <button
            onClick={handleCreate}
            disabled={isCreating}
            className="flex items-center px-3 py-1.5 bg-purple-600 dark:bg-purple-700 text-white text-sm rounded-md hover:bg-purple-700 dark:hover:bg-purple-800 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isCreating ? (
              <RefreshCw className="w-4 h-4 mr-1 animate-spin" />
            ) : (
              <Plus className="w-4 h-4 mr-1" />
            )}
            <span>{t('workflow.actions.create', '创建工作流')}</span>
          </button>
        </div>
      </header>

      {/* Filters */}
      <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 flex items-center gap-4">
        {/* Search */}
        <div className="flex-1 max-w-md relative">
          <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder={t('workflow.searchPlaceholder', '搜索工作流...')}
            className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-purple-500 dark:bg-gray-700 dark:text-gray-100"
          />
        </div>

        {/* Status Filter */}
        <div className="flex items-center gap-2">
          {(['all', 'active', 'draft', 'archived'] as const).map((status) => (
            <button
              key={status}
              onClick={() => setStatusFilter(status)}
              className={`px-3 py-1.5 text-sm rounded-md transition-colors ${
                statusFilter === status
                  ? 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-300'
                  : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700'
              }`}
            >
              {status === 'all' ? t('common.all', '全部') :
               status === 'active' ? t('workflow.status.active', '已启用') :
               status === 'draft' ? t('workflow.status.draft', '草稿') :
               t('workflow.status.archived', '已归档')}
            </button>
          ))}
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-6">
        {/* Loading State */}
        {isLoadingWorkflows && workflows.length === 0 && (
          <div className="flex items-center justify-center py-12">
            <RefreshCw className="w-6 h-6 animate-spin text-gray-400" />
          </div>
        )}

        {/* Error State */}
        {workflowsError && (
          <div className="text-center py-12">
            <p className="text-red-600 dark:text-red-400 mb-3">{workflowsError}</p>
            <button
              onClick={handleRefresh}
              className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700"
            >
              {t('common.retry', '重试')}
            </button>
          </div>
        )}

        {/* Empty State */}
        {!isLoadingWorkflows && !workflowsError && filteredWorkflows.length === 0 && (
          <div className="text-center py-16">
            <GitBranch className="w-12 h-12 text-gray-400 dark:text-gray-500 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-2">
              {searchQuery || statusFilter !== 'all'
                ? t('workflow.noMatch', '未找到匹配的工作流')
                : t('workflow.empty_state.title', '暂无工作流')}
            </h3>
            <p className="text-gray-500 dark:text-gray-400 mb-6">
              {searchQuery || statusFilter !== 'all'
                ? t('workflow.noMatch.description', '尝试调整搜索条件')
                : t('workflow.empty_state.description', '创建您的第一个AI工作流')}
            </p>
            {!searchQuery && statusFilter === 'all' && (
              <button
                onClick={handleCreate}
                disabled={isCreating}
                className="inline-flex items-center px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isCreating ? (
                  <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                ) : (
                  <Plus className="w-4 h-4 mr-2" />
                )}
                {t('workflow.actions.create', '创建工作流')}
              </button>
            )}
          </div>
        )}

        {/* Workflow Grid */}
        {!isLoadingWorkflows && !workflowsError && filteredWorkflows.length > 0 && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredWorkflows.map((workflow) => (
              <WorkflowCard
                key={workflow.id}
                workflow={workflow}
                onEdit={handleEdit}
                onDuplicate={handleDuplicate}
                onDelete={(id) => setDeleteTarget(workflows.find(w => w.id === id) || null)}
              />
            ))}
          </div>
        )}
      </div>

      {/* Delete Confirmation */}
      <ConfirmDialog
        isOpen={!!deleteTarget}
        title={t('workflow.modal.delete.title', '删除工作流')}
        message={t('workflow.modal.delete.message', `确定要删除工作流 "${deleteTarget?.name}" 吗？此操作不可撤销。`, { name: deleteTarget?.name })}
        confirmText={t('common.delete', '删除')}
        cancelText={t('common.cancel', '取消')}
        confirmVariant="danger"
        onConfirm={handleDeleteConfirm}
        onCancel={() => setDeleteTarget(null)}
        isLoading={isDeleting}
      />
    </main>
  );
};

export default WorkflowManagement;

