import React from 'react';
import { useTranslation } from 'react-i18next';
import { Bell } from 'lucide-react';

const NotificationSettings: React.FC = () => {
  const { t } = useTranslation();

  return (
    <div className="p-6 space-y-4">
      <div className="flex items-center gap-2">
        <Bell className="w-5 h-5 text-gray-600" />
        <h2 className="text-lg font-medium text-gray-800">{t('settings.notifications.title', '\u6d88\u606f\u901a\u77e5')}</h2>
      </div>

      <div className="bg-white rounded-lg border border-gray-200 p-6 text-sm text-gray-600">
        {t('settings.notifications.comingSoon', '更多通知设置，敬请期待…')}
      </div>
    </div>
  );
};

export default NotificationSettings;

