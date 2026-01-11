import React from 'react';
import { X, LogIn, Sparkles, ShieldCheck, Zap } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';

interface StoreLoginModalProps {
  isOpen: boolean;
  onClose: () => void;
}

const StoreLoginModal: React.FC<StoreLoginModalProps> = ({ isOpen, onClose }) => {
  const { t } = useTranslation();
  const navigate = useNavigate();

  if (!isOpen) return null;

  const handleLogin = () => {
    // Navigate to login with a redirect back to the current page (tools)
    navigate('/login', { state: { from: { pathname: '/ai/tools' } } });
    onClose();
  };

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 sm:p-6">
      {/* Backdrop */}
      <div 
        className="absolute inset-0 bg-gray-900/40 backdrop-blur-sm animate-in fade-in duration-300"
        onClick={onClose}
      />

      {/* Modal Content */}
      <div className="relative w-full max-w-md bg-white dark:bg-gray-900 rounded-[2.5rem] shadow-2xl overflow-hidden border border-gray-100 dark:border-gray-800 animate-in zoom-in-95 slide-in-from-bottom-8 duration-500">
        {/* Top Decorative Banner */}
        <div className="h-32 bg-gradient-to-br from-blue-600 to-indigo-700 relative overflow-hidden">
          <div className="absolute inset-0 bg-[url('https://www.transparenttextures.com/patterns/cubes.png')] opacity-20"></div>
          <div className="absolute -bottom-6 -right-6 w-32 h-32 bg-white/10 rounded-full blur-3xl"></div>
          <div className="absolute -top-10 -left-10 w-40 h-40 bg-blue-400/20 rounded-full blur-3xl"></div>
          
          <button 
            onClick={onClose}
            className="absolute top-4 right-4 p-2 bg-black/10 hover:bg-black/20 text-white rounded-full transition-colors z-10"
          >
            <X className="w-4 h-4" />
          </button>

          <div className="absolute inset-0 flex items-center justify-center">
            <div className="w-16 h-16 bg-white dark:bg-gray-800 rounded-2xl shadow-xl flex items-center justify-center text-blue-600 animate-bounce-subtle">
              <LogIn className="w-8 h-8" />
            </div>
          </div>
        </div>

        <div className="p-8 text-center space-y-6">
          <div className="space-y-2">
            <h2 className="text-2xl font-black text-gray-900 dark:text-gray-100 tracking-tight">
              {t('tools.store.loginRequired', '请先登录')}
            </h2>
            <p className="text-sm text-gray-500 dark:text-gray-400 leading-relaxed px-2">
              {t('tools.store.loginRequiredDesc', '安装工具需要登录您的 TGO 账号。登录后即可一键安装、同步配置并管理您的 AI 工具集。')}
            </p>
          </div>

          {/* Value Props */}
          <div className="grid grid-cols-1 gap-3 text-left">
            <div className="flex items-center gap-3 p-3 rounded-2xl bg-gray-50 dark:bg-gray-800/50 border border-gray-100 dark:border-gray-700/50">
              <div className="w-8 h-8 rounded-xl bg-blue-50 dark:bg-blue-900/20 flex items-center justify-center text-blue-600 dark:text-blue-400">
                <Sparkles className="w-4 h-4" />
              </div>
              <span className="text-xs font-bold text-gray-700 dark:text-gray-300">一键快速安装工具</span>
            </div>
            <div className="flex items-center gap-3 p-3 rounded-2xl bg-gray-50 dark:bg-gray-800/50 border border-gray-100 dark:border-gray-700/50">
              <div className="w-8 h-8 rounded-xl bg-indigo-50 dark:bg-indigo-900/20 flex items-center justify-center text-indigo-600 dark:text-indigo-400">
                <ShieldCheck className="w-4 h-4" />
              </div>
              <span className="text-xs font-bold text-gray-700 dark:text-gray-300">安全的配置同步与管理</span>
            </div>
            <div className="flex items-center gap-3 p-3 rounded-2xl bg-gray-50 dark:bg-gray-800/50 border border-gray-100 dark:border-gray-700/50">
              <div className="w-8 h-8 rounded-xl bg-amber-50 dark:bg-amber-900/20 flex items-center justify-center text-amber-600 dark:text-amber-400">
                <Zap className="w-4 h-4" />
              </div>
              <span className="text-xs font-bold text-gray-700 dark:text-gray-300">即刻增强 AI 员工能力</span>
            </div>
          </div>

          <div className="space-y-3 pt-2">
            <button
              onClick={handleLogin}
              className="w-full py-4 bg-blue-600 hover:bg-blue-700 text-white font-black rounded-2xl shadow-xl shadow-blue-200 dark:shadow-none transition-all active:scale-[0.98] flex items-center justify-center gap-2"
            >
              {t('tools.store.loginNow', '立即登录')}
            </button>
            <button
              onClick={onClose}
              className="w-full py-3 text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 text-sm font-bold transition-colors"
            >
              {t('tools.store.cancelInstall', '稍后再说')}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default StoreLoginModal;
