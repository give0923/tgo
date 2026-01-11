import React from 'react';
import { X, Star, Download, ShieldCheck, Calendar, Info, History, Code, Check } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import MarkdownContent from '../chat/MarkdownContent';
import type { ToolStoreItem } from '@/types';

interface ToolStoreDetailProps {
  tool: ToolStoreItem | null;
  isOpen: boolean;
  onClose: () => void;
  onInstall: (tool: ToolStoreItem) => void;
  isInstalled?: boolean;
  installingId?: string | null;
}

const ToolStoreDetail: React.FC<ToolStoreDetailProps> = ({ 
  tool, 
  isOpen, 
  onClose, 
  onInstall, 
  isInstalled,
  installingId
}) => {
  const { t } = useTranslation();

  if (!tool) return null;

  const isInstalling = installingId === tool.id;

  return (
    <>
      {/* Backdrop */}
      {isOpen && (
        <div 
          className="fixed inset-0 bg-black/20 backdrop-blur-sm z-[60] animate-in fade-in duration-300"
          onClick={onClose}
        />
      )}

      {/* Side Panel */}
      <div className={`fixed top-0 right-0 h-full w-full max-w-2xl bg-white dark:bg-gray-900 shadow-2xl z-[70] transform transition-transform duration-500 ease-out flex flex-col ${isOpen ? 'translate-x-0' : 'translate-x-full'}`}>
        {/* Header */}
        <div className="px-8 py-6 border-b border-gray-100 dark:border-gray-800 flex items-center justify-between sticky top-0 bg-white/80 dark:bg-gray-900/80 backdrop-blur-xl z-10">
          <div className="flex items-center gap-4">
            <button 
              onClick={onClose}
              className="p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-xl text-gray-400 hover:text-gray-600 transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
            <h2 className="text-xl font-bold text-gray-900 dark:text-gray-100">{t('tools.store.details', '工具详情')}</h2>
          </div>

          <button
            onClick={() => onInstall(tool)}
            disabled={isInstalled || isInstalling}
            className={`flex items-center gap-2 px-6 py-2.5 rounded-xl text-sm font-bold transition-all active:scale-95 ${
              isInstalled 
                ? 'bg-green-50 dark:bg-green-900/20 text-green-600 dark:text-green-400 border border-green-200 dark:border-green-800' 
                : isInstalling
                  ? 'bg-blue-100 dark:bg-blue-900/40 text-blue-400 cursor-not-allowed'
                  : 'bg-blue-600 hover:bg-blue-700 text-white shadow-xl shadow-blue-200 dark:shadow-none'
            }`}
          >
            {isInstalled ? (
              <><Check className="w-4 h-4" /> {t('tools.store.installed', '已安装')}</>
            ) : isInstalling ? (
              <>{t('tools.store.installing', '安装中...')}</>
            ) : (
              t('tools.store.install', '安装')
            )}
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-8 custom-scrollbar">
          <div className="max-w-3xl mx-auto space-y-10">
            {/* Top Info */}
            <div className="flex flex-col md:flex-row gap-8 items-start">
              <div className="w-24 h-24 rounded-3xl bg-gray-50 dark:bg-gray-800 flex items-center justify-center text-5xl border border-gray-100 dark:border-gray-700 shadow-sm flex-shrink-0">
                {tool.icon || '🛠️'}
              </div>
              
              <div className="flex-1 space-y-4">
                <div>
                  <div className="flex items-center gap-2">
                    <h1 className="text-3xl font-black text-gray-900 dark:text-gray-100 tracking-tight">
                      {tool.name}
                    </h1>
                    {tool.verified && (
                      <div className="flex items-center gap-1 px-2 py-0.5 bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400 text-[10px] font-bold rounded-lg border border-blue-100 dark:border-blue-800">
                        <ShieldCheck className="w-3 h-3" />
                        {t('tools.store.verified', '官方认证')}
                      </div>
                    )}
                  </div>
                  <p className="text-gray-500 dark:text-gray-400 font-medium text-lg mt-1">
                    {tool.author} <span className="text-gray-300 dark:text-gray-600 mx-2">@</span>{tool.authorHandle}
                  </p>
                </div>

                <div className="flex flex-wrap gap-6 items-center">
                  <div className="flex items-center gap-1.5">
                    <Star className="w-5 h-5 text-amber-400 fill-amber-400" />
                    <span className="font-black text-gray-900 dark:text-gray-100">{tool.rating}</span>
                    <span className="text-sm text-gray-400">({tool.ratingCount} {t('tools.store.rating', '评分')})</span>
                  </div>
                  <div className="h-4 w-px bg-gray-200 dark:bg-gray-800"></div>
                  <div className="flex items-center gap-1.5">
                    <Download className="w-5 h-5 text-gray-400" />
                    <span className="font-black text-gray-900 dark:text-gray-100">{tool.downloads.toLocaleString()}</span>
                    <span className="text-sm text-gray-400">{t('tools.store.downloads', '下载量')}</span>
                  </div>
                </div>

                <div className="flex flex-wrap gap-2">
                  {tool.tags.map(tag => (
                    <span key={tag} className="px-3 py-1 bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 text-xs rounded-xl font-bold border border-gray-200/50 dark:border-gray-700/50">
                      {tag}
                    </span>
                  ))}
                </div>
              </div>
            </div>

            {/* Meta Grid */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="bg-gray-50 dark:bg-gray-800/50 p-4 rounded-2xl border border-gray-100 dark:border-gray-700/50">
                <div className="text-[10px] font-bold uppercase tracking-widest text-gray-400 mb-1 flex items-center gap-1.5">
                  <Info className="w-3 h-3" />
                  {t('tools.store.version', '版本')}
                </div>
                <div className="text-sm font-bold text-gray-900 dark:text-gray-100">v{tool.version}</div>
              </div>
              <div className="bg-gray-50 dark:bg-gray-800/50 p-4 rounded-2xl border border-gray-100 dark:border-gray-700/50">
                <div className="text-[10px] font-bold uppercase tracking-widest text-gray-400 mb-1 flex items-center gap-1.5">
                  <Calendar className="w-3 h-3" />
                  {t('tools.store.lastUpdated', '最后更新')}
                </div>
                <div className="text-sm font-bold text-gray-900 dark:text-gray-100">{tool.lastUpdated}</div>
              </div>
              <div className="bg-gray-50 dark:bg-gray-800/50 p-4 rounded-2xl border border-gray-100 dark:border-gray-700/50">
                <div className="text-[10px] font-bold uppercase tracking-widest text-gray-400 mb-1 flex items-center gap-1.5">
                  <Code className="w-3 h-3" />
                  {t('tools.store.requirements', '运行环境')}
                </div>
                <div className="text-xs font-bold text-gray-900 dark:text-gray-100 truncate">{tool.requirements.join(', ') || 'None'}</div>
              </div>
              <div className="bg-gray-50 dark:bg-gray-800/50 p-4 rounded-2xl border border-gray-100 dark:border-gray-700/50">
                <div className="text-[10px] font-bold uppercase tracking-widest text-gray-400 mb-1 flex items-center gap-1.5">
                  <History className="w-3 h-3" />
                  {t('tools.store.changelog', '更新日志')}
                </div>
                <div className="text-xs font-bold text-gray-900 dark:text-gray-100 truncate">{tool.changelog}</div>
              </div>
            </div>

            {/* Long Description */}
            <div className="max-w-none">
              <h3 className="text-lg font-bold text-gray-900 dark:text-gray-100 mb-4 pb-2 border-b border-gray-100 dark:border-gray-800">
                描述
              </h3>
              <div className="text-gray-600 dark:text-gray-400 leading-relaxed">
                {tool.longDescription ? (
                  <MarkdownContent content={tool.longDescription} className="!max-w-none" />
                ) : (
                  tool.description
                )}
              </div>
            </div>

            {/* Methods / API Section */}
            {tool.methods && tool.methods.length > 0 && (
              <div className="space-y-6">
                <h3 className="text-lg font-bold text-gray-900 dark:text-gray-100 mb-4 pb-2 border-b border-gray-100 dark:border-gray-800">
                  可用方法 (Methods)
                </h3>
                <div className="space-y-4">
                  {tool.methods.map(method => (
                    <div key={method.id} className="bg-white dark:bg-gray-800 border border-gray-100 dark:border-gray-700 rounded-2xl overflow-hidden">
                      <div className="px-5 py-3 bg-gray-50 dark:bg-gray-800/80 border-b border-gray-100 dark:border-gray-700 flex items-center justify-between">
                        <code className="text-blue-600 dark:text-blue-400 font-mono font-bold">{method.name}()</code>
                        <span className="text-[10px] font-bold text-gray-400 uppercase tracking-wider">{method.returnType}</span>
                      </div>
                      <div className="p-5 space-y-4">
                        <p className="text-sm text-gray-600 dark:text-gray-400">{method.description}</p>
                        
                        {method.parameters.length > 0 && (
                          <div className="space-y-2">
                            <div className="text-[10px] font-bold text-gray-400 uppercase tracking-widest">参数 (Parameters)</div>
                            <div className="space-y-2">
                              {method.parameters.map(param => (
                                <div key={param.name} className="flex gap-4 text-xs">
                                  <div className="w-24 flex-shrink-0">
                                    <code className="text-gray-900 dark:text-gray-100 font-mono font-bold">{param.name}</code>
                                    <div className="text-[10px] text-gray-400">{param.type}{param.required && <span className="text-red-500 ml-1">*</span>}</div>
                                  </div>
                                  <div className="flex-1 text-gray-500 dark:text-gray-400">{param.description}</div>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}

                        {method.example && (
                          <div className="space-y-2 pt-2">
                            <div className="text-[10px] font-bold text-gray-400 uppercase tracking-widest">示例 (Example)</div>
                            <pre className="p-3 bg-gray-900 rounded-xl text-xs text-blue-300 font-mono overflow-x-auto">
                              {method.example}
                            </pre>
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </>
  );
};

export default ToolStoreDetail;
