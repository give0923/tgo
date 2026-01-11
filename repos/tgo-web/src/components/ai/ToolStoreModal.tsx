import React, { useState, useMemo, useEffect } from 'react';
import { X, Search, Filter, Loader2, Sparkles, Brain, Wrench, Bot, Puzzle, Package, Grid3X3 } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import ToolStoreCard from './ToolStoreCard';
import ToolStoreDetail from './ToolStoreDetail';
import StoreLoginModal from './StoreLoginModal';
import { TOOL_STORE_CATEGORIES, searchTools } from '@/data/mockToolStore';
import { useProjectToolsStore } from '@/stores/projectToolsStore';
import { useAuthStore } from '@/stores/authStore';
import { useToast } from './ToolToastProvider';
import type { ToolStoreItem } from '@/types';

interface ToolStoreModalProps {
  isOpen: boolean;
  onClose: () => void;
}

const ToolStoreModal: React.FC<ToolStoreModalProps> = ({ isOpen, onClose }) => {
  const { t } = useTranslation();
  const { showToast } = useToast();
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [selectedTool, setSelectedTool] = useState<ToolStoreItem | null>(null);
  const [isDetailOpen, setIsDetailOpen] = useState(false);
  const [showLoginModal, setShowLoginModal] = useState(false);
  const [installingId, setInstallingId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const { aiTools, loadTools } = useProjectToolsStore();
  const { isAuthenticated, user } = useAuthStore();

  // Simulation of initial loading
  useEffect(() => {
    if (isOpen) {
      setLoading(true);
      const timer = setTimeout(() => {
        setLoading(false);
      }, 800);
      return () => clearTimeout(timer);
    }
    return undefined;
  }, [isOpen]);

  // Check if a tool is already installed in the project
  const installedToolNames = useMemo(() => {
    return new Set(aiTools.map(t => t.name.toLowerCase()));
  }, [aiTools]);

  const filteredTools = useMemo(() => {
    return searchTools(searchQuery, selectedCategory);
  }, [searchQuery, selectedCategory]);

  const handleToolClick = (tool: ToolStoreItem) => {
    setSelectedTool(tool);
    setIsDetailOpen(true);
  };

  const handleInstall = async (e: React.MouseEvent | ToolStoreItem, toolInput?: ToolStoreItem) => {
    // Handle both event-based and direct item-based calls
    const tool = toolInput || (e as ToolStoreItem);
    if (e && (e as React.MouseEvent).stopPropagation) {
      (e as React.MouseEvent).stopPropagation();
    }

    // AUTH CHECK: Must be logged in to install
    if (!isAuthenticated) {
      setShowLoginModal(true);
      return;
    }

    if (installedToolNames.has(tool.name.toLowerCase())) {
      showToast('info', t('tools.store.installed', '已安装'), t('tools.store.installSuccessMessage', { name: tool.name }));
      return;
    }

    setInstallingId(tool.id);
    
    try {
      // Simulate installation API call
      await new Promise(resolve => setTimeout(resolve, 1500));
      
      // In a real app, we would call an API like:
      // await apiClient.post(`/v1/tool-store/tools/${tool.id}/install`);
      
      showToast('success', t('tools.store.installSuccess', '安装成功'), t('tools.store.installSuccessMessage', { name: tool.name }));
      
      // Refresh installed tools list
      await loadTools(false);
    } catch (error) {
      showToast('error', t('common.error', '错误'), t('common.saveFailed', '保存失败'));
    } finally {
      setInstallingId(null);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6 md:p-10">
      {/* Backdrop */}
      <div 
        className="absolute inset-0 bg-gray-900/60 backdrop-blur-md animate-in fade-in duration-300"
        onClick={onClose}
      />

      {/* Modal Container */}
      <div className="relative w-full max-w-[1400px] h-full max-h-[900px] bg-[#f8fafc] dark:bg-gray-950 rounded-[2.5rem] shadow-2xl flex flex-col overflow-hidden border border-white/10 animate-in zoom-in-95 slide-in-from-bottom-10 duration-500 ease-out">
        
        {/* Sidebar + Main Content */}
        <div className="flex flex-1 overflow-hidden">
          
          {/* Sidebar - Categories */}
          <aside className="w-72 bg-white/50 dark:bg-gray-900/50 border-r border-gray-200/50 dark:border-gray-800/50 hidden lg:flex flex-col">
            <div className="p-8">
              <div className="flex items-center gap-2 mb-8">
                <div className="w-10 h-10 rounded-2xl bg-blue-600 flex items-center justify-center text-white shadow-lg shadow-blue-200 dark:shadow-none">
                  <Sparkles className="w-5 h-5" />
                </div>
                <h2 className="text-xl font-black text-gray-900 dark:text-gray-100 tracking-tight">
                  {t('tools.toolStore', '工具商店')}
                </h2>
              </div>

              <nav className="space-y-1">
                {TOOL_STORE_CATEGORIES.map(cat => {
                  const IconComponent = ({
                    Grid3X3,
                    Brain,
                    Wrench,
                    Bot,
                    Puzzle,
                    Package
                  } as any)[cat.icon] || Filter;

                  return (
                    <button
                      key={cat.id}
                      onClick={() => setSelectedCategory(cat.id)}
                      className={`w-full flex items-center gap-3 px-4 py-3 rounded-2xl text-sm font-bold transition-all ${
                        selectedCategory === cat.id
                          ? 'bg-blue-600 text-white shadow-lg shadow-blue-100 dark:shadow-none'
                          : 'text-gray-500 hover:bg-white dark:hover:bg-gray-800 hover:text-gray-900 dark:hover:text-gray-100'
                      }`}
                    >
                      <IconComponent className={`w-4 h-4 ${selectedCategory === cat.id ? 'opacity-100' : 'opacity-50'}`} />
                      {t(`tools.store.categories.${cat.id}`, cat.label)}
                    </button>
                  );
                })}
              </nav>
            </div>
          </aside>

          {/* Main Area */}
          <div className="flex-1 flex flex-col min-w-0">
            {/* Header */}
            <header className="px-8 py-6 flex items-center justify-between gap-6 border-b border-gray-100 dark:border-gray-800 bg-white/50 dark:bg-gray-900/50 backdrop-blur-xl">
              <div className="relative flex-1 max-w-2xl group">
                <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400 group-focus-within:text-blue-500 transition-colors" />
                <input 
                  type="text"
                  placeholder={t('tools.store.searchPlaceholder', '搜索工具、作者或标签...')}
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full pl-12 pr-4 py-3 bg-gray-100 dark:bg-gray-800 border-transparent focus:bg-white dark:focus:bg-gray-800 focus:ring-4 focus:ring-blue-500/10 focus:border-blue-500 rounded-2xl text-sm font-medium transition-all outline-none"
                />
              </div>

              <div className="flex items-center gap-4">
                {/* User Status */}
                {!isAuthenticated ? (
                  <button 
                    onClick={() => setShowLoginModal(true)}
                    className="hidden sm:flex items-center gap-2 px-4 py-2 text-sm font-bold text-blue-600 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded-xl transition-all"
                  >
                    {t('tools.store.loginNow', '立即登录')}
                  </button>
                ) : (
                  <div className="hidden sm:flex items-center gap-3 pl-4 border-l border-gray-200 dark:border-gray-800">
                    <div className="text-right">
                      <div className="text-xs font-black text-gray-900 dark:text-gray-100 truncate max-w-[100px]">
                        {user?.nickname || user?.username}
                      </div>
                      <div className="text-[10px] text-gray-400 font-bold uppercase tracking-tighter">Verified Account</div>
                    </div>
                    {user?.avatar_url ? (
                      <img src={user.avatar_url} alt="" className="w-9 h-9 rounded-xl object-cover border border-gray-100 dark:border-gray-800" />
                    ) : (
                      <div className="w-9 h-9 rounded-xl bg-blue-100 dark:bg-blue-900/40 text-blue-600 dark:text-blue-400 flex items-center justify-center font-bold text-sm">
                        {user?.nickname?.charAt(0).toUpperCase() || user?.username?.charAt(0).toUpperCase()}
                      </div>
                    )}
                  </div>
                )}

                <button 
                  onClick={onClose}
                  className="p-3 bg-white dark:bg-gray-800 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-2xl text-gray-400 hover:text-gray-600 transition-all shadow-sm active:scale-90"
                >
                  <X className="w-6 h-6" />
                </button>
              </div>
            </header>

            {/* Tool Grid */}
            <div className="flex-1 overflow-y-auto p-8 custom-scrollbar">
              <div className="max-w-[1200px] mx-auto">
                {loading ? (
                  <div className="flex flex-col items-center justify-center h-[500px] gap-4">
                    <Loader2 className="w-10 h-10 text-blue-600 animate-spin" />
                    <p className="text-sm font-bold text-gray-400 animate-pulse">{t('common.loading', '加载中...')}</p>
                  </div>
                ) : filteredTools.length === 0 ? (
                  <div className="flex flex-col items-center justify-center h-[500px] text-center">
                    <div className="w-20 h-20 rounded-3xl bg-gray-100 dark:bg-gray-800 flex items-center justify-center text-gray-300 dark:text-gray-700 mb-6">
                      <Search className="w-10 h-10" />
                    </div>
                    <h3 className="text-xl font-bold text-gray-900 dark:text-gray-100 mb-2">{t('tools.store.noResults', '未找到匹配的工具')}</h3>
                    <p className="text-gray-500 dark:text-gray-400">{t('tools.store.noResultsDesc', '试试搜索其他关键词或切换分类')}</p>
                  </div>
                ) : (
                  <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
                    {filteredTools.map(tool => (
                      <ToolStoreCard 
                        key={tool.id} 
                        tool={tool} 
                        onClick={handleToolClick}
                        onInstall={handleInstall}
                        isInstalled={installedToolNames.has(tool.name.toLowerCase())}
                      />
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Tool Detail Panel */}
      <ToolStoreDetail 
        tool={selectedTool}
        isOpen={isDetailOpen}
        onClose={() => setIsDetailOpen(false)}
        onInstall={(tool) => handleInstall(tool)}
        isInstalled={selectedTool ? installedToolNames.has(selectedTool.name.toLowerCase()) : false}
        installingId={installingId}
      />

      {/* Login Modal */}
      <StoreLoginModal 
        isOpen={showLoginModal}
        onClose={() => setShowLoginModal(false)}
      />
    </div>
  );
};

export default ToolStoreModal;
