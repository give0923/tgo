import React from 'react';
import { useTranslation } from 'react-i18next';
import { Info } from 'lucide-react';

const AboutSettings: React.FC = () => {
  const { t } = useTranslation();

  const version = import.meta.env?.VITE_APP_VERSION || '1.0.0';
  const env = import.meta.env?.MODE || 'development';
  const apiBase = import.meta.env?.VITE_API_BASE_URL || window.location.origin;

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center gap-2">
        <Info className="w-5 h-5 text-gray-600" />
        <h2 className="text-lg font-medium text-gray-800">{t('common.about', '关于')}</h2>
      </div>

      <div className="bg-white rounded-lg border border-gray-200 p-6 space-y-4">
        <div className="flex items-center justify-between">
          <span className="text-sm text-gray-600">{t('about.version', '版本')}</span>
          <span className="text-sm font-mono text-gray-800">{version}</span>
        </div>
        <div className="flex items-center justify-between">
          <span className="text-sm text-gray-600">{t('about.environment', '环境')}</span>
          <span className="text-sm font-mono text-gray-800">{env}</span>
        </div>
        <div className="space-y-2">
          <div className="text-sm text-gray-600">{t('about.apiEndpoint', '接口地址')}</div>
          <div className="font-mono text-xs text-gray-800 bg-gray-50 p-2 rounded border break-all">{apiBase}</div>
        </div>
        <div className="text-xs text-gray-500 pt-2 border-t border-gray-100">
          © {new Date().getFullYear()} TGO Web. {t('about.copyright', 'All rights reserved.')}
        </div>
      </div>
    </div>
  );
};

export default AboutSettings;

