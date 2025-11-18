import React from 'react';
import type { SystemInfo as ChannelSystemInfo } from '@/types';
import { useTranslation } from 'react-i18next';

interface SystemInfoSectionProps {
  systemInfo?: ChannelSystemInfo | null;
  className?: string;
}

/**
 * 系统信息模块组件
 */
const SystemInfoSection: React.FC<SystemInfoSectionProps> = ({
  systemInfo,
  className = ''
}) => {
  const { t } = useTranslation();
  const isUrl = (v?: string | null) => !!v && /^(https?:)\/\//i.test(v.trim());

  const parseAPITimestampToLocalDate = (iso?: string | null): Date | null => {
    if (!iso) return null;
    let s = iso.trim();
    s = s.replace(/(\.\d{3})\d+$/, '$1');
    const hasTZ = /[zZ]|[+-]\d{2}:\d{2}$/.test(s);
    if (!hasTZ) s += 'Z';
    const d = new Date(s);
    return Number.isFinite(d.getTime()) ? d : null;
  };

  const formatLocalDateTime = (iso?: string | null): string => {
    const d = parseAPITimestampToLocalDate(iso);
    if (!d) return '-';
    const y = d.getFullYear();
    const m = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    const hh = String(d.getHours()).padStart(2, '0');
    const mm = String(d.getMinutes()).padStart(2, '0');
    return `${y}/${m}/${day} ${hh}:${mm}`;
  };

  const valueOrDash = (v?: string | null) => (v && v.trim() !== '' ? v : '-');

  const platform = valueOrDash(systemInfo?.platform);
  const sourceDetail = valueOrDash(systemInfo?.source_detail);
  const browser = valueOrDash(systemInfo?.browser);
  const os = valueOrDash(systemInfo?.operating_system);
  const firstSeen = formatLocalDateTime(systemInfo?.first_seen_at);

  return (
    <div className={`pt-4 space-y-3 ${className}`}>
      <h4 className="text-xs font-semibold text-gray-600 uppercase tracking-wider">{t('chat.visitor.sections.systemInfo', '\u7cfb\u7edf\u4fe1\u606f')}</h4>
      {systemInfo ? (
        <div className="space-y-1.5 text-[13px] leading-5">
          <div className="flex justify-between items-start">
            <span className="text-gray-500 flex-shrink-0 pt-0.5">{t('chat.visitor.system.fields.platform', '\u5e73\u53f0')}</span>
            <span className="text-gray-800 font-medium flex-1 min-w-0 ml-2 text-right line-clamp-2" title={platform}>
              {platform}
            </span>
          </div>
          <div className="flex justify-between items-start">
            <span className="text-gray-500 flex-shrink-0 pt-0.5">{t('chat.visitor.system.fields.sourcePage', '\u6765\u6e90\u9875\u9762')}</span>
            <span className="text-gray-800 font-medium flex-1 min-w-0 ml-2 text-right line-clamp-2">
              {isUrl(systemInfo.source_detail) ? (
                <a
                  href={systemInfo.source_detail as string}
                  target="_blank"
                  rel="noreferrer"
                  className="text-blue-600 hover:underline underline-offset-2 break-all"
                  title={systemInfo.source_detail as string}
                >
                  {systemInfo.source_detail}
                </a>
              ) : (
                <span title={sourceDetail}>{sourceDetail}</span>
              )}
            </span>
          </div>
          <div className="flex justify-between items-start">
            <span className="text-gray-500 flex-shrink-0 pt-0.5">{t('chat.visitor.system.fields.browser', '\u6d4f\u89c8\u5668')}</span>
            <span className="text-gray-800 font-medium flex-1 min-w-0 ml-2 text-right line-clamp-2" title={browser}>
              {browser}
            </span>
          </div>
          <div className="flex justify-between items-start">
            <span className="text-gray-500 flex-shrink-0 pt-0.5">{t('chat.visitor.system.fields.os', '\u64cd\u4f5c\u7cfb\u7edf')}</span>
            <span className="text-gray-800 font-medium flex-1 min-w-0 ml-2 text-right line-clamp-2" title={os}>
              {os}
            </span>
          </div>
          <div className="flex justify-between items-start">
            <span className="text-gray-500 flex-shrink-0 pt-0.5">{t('chat.visitor.system.fields.firstSeen', '\u9996\u6b21\u8bbf\u95ee')}</span>
            <span className="text-gray-800 font-medium flex-1 min-w-0 ml-2 text-right line-clamp-2" title={firstSeen}>
              {firstSeen}
            </span>
          </div>
        </div>
      ) : (
        <div className="text-xs text-gray-400">{t('chat.visitor.system.empty', '\u6682\u65e0\u7cfb\u7edf\u4fe1\u606f')}</div>
      )}
    </div>
  );
};

export default SystemInfoSection;
