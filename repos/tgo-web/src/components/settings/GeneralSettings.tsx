import React from 'react';
import { useTranslation } from 'react-i18next';
import { Settings } from 'lucide-react';

import LanguageSelector from '@/components/ui/LanguageSelector';

const GeneralSettings: React.FC = () => {
  const { t } = useTranslation();



  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center gap-2">
        <Settings className="w-5 h-5 text-gray-600" />
        <h2 className="text-lg font-medium text-gray-800">{t('settings.general.title', '\u901a\u7528')}</h2>
      </div>

      <div className="bg-white rounded-lg border border-gray-200 p-6 space-y-6">
        {/* 语言设置 */}
        <div>
          <div className="text-sm font-medium text-gray-800 mb-3">{t('settings.language.title', '\u8bed\u8a00\u8bbe\u7f6e')}</div>
          <div className="flex items-center gap-4">
            <LanguageSelector variant="button" placement="bottom" usePortal />
            <div className="text-xs text-gray-500">{t('settings.language.persistence', '\u8bed\u8a00\u504f\u597d\u5c06\u81ea\u52a8\u4fdd\u5b58\u5230\u672c\u5730')}</div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default GeneralSettings;

