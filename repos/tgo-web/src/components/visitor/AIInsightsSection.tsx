import React from 'react';
import { Star } from 'lucide-react';
import { useTranslation } from 'react-i18next';

interface AIInsightsSectionProps {
  satisfactionScore?: number | null; // 显示当 > 0
  emotionScore?: number | null; // 显示当 !== 0
  intent?: string | null; // 非空显示
  insightSummary?: string | null; // 非空显示
  className?: string;
}

/**
 * AI洞察模块组件（根据有效字段按需展示；若所有字段无效，则不渲染）
 */
const AIInsightsSection: React.FC<AIInsightsSectionProps> = ({
  satisfactionScore,
  emotionScore,
  intent,
  insightSummary,
  className = ''
}) => {
  const { t } = useTranslation();
  const hasSatisfaction = typeof satisfactionScore === 'number' && satisfactionScore > 0; // 0 表示未知
  const hasEmotion = typeof emotionScore === 'number' && emotionScore > 0; // 0 表示未知
  const hasIntent = typeof intent === 'string' && intent.trim().length > 0;
  const hasSummary = typeof insightSummary === 'string' && insightSummary.trim().length > 0;

  if (!hasSatisfaction && !hasEmotion && !hasIntent && !hasSummary) {
    return null;
  }

  const satisfactionStars = Math.max(0, Math.min(5, Math.round(satisfactionScore || 0)));
  const emotionStars = Math.max(0, Math.min(5, Math.round(emotionScore || 0)));

  return (
    <div className={`pt-4 space-y-3 ${className}`}>
      <h4 className="text-xs font-semibold text-gray-600 uppercase tracking-wider">{t('chat.visitor.sections.aiInsights', 'AI \u6d1e\u5bdf')}</h4>
      <div className="space-y-2.5 text-[13px] leading-5">
        {hasSatisfaction && (
          <div className="flex items-center justify-between">
            <span className="text-gray-500">{t('chat.visitor.aiInsights.satisfactionScore', '\u6ee1\u610f\u5ea6\u8bc4\u5206')}</span>
            <div className="flex items-center space-x-0.5">
              {[1, 2, 3, 4, 5].map((n) => (
                <Star
                  key={n}
                  className={`w-4 h-4 ${n <= satisfactionStars ? 'text-yellow-400 fill-current' : 'text-gray-300 fill-current'}`}
                />
              ))}
            </div>
          </div>
        )}

        {hasEmotion && (
          <div className="flex items-center justify-between">
            <span className="text-gray-500">{t('chat.visitor.aiInsights.emotionScore', '\u60c5\u7eea\u8bc4\u5206')}</span>
            <div className="flex items-center space-x-0.5">
              {[1, 2, 3, 4, 5].map((n) => (
                <Star
                  key={n}
                  className={`w-4 h-4 ${n <= emotionStars ? 'text-blue-400 fill-current' : 'text-gray-300 fill-current'}`}
                />
              ))}
            </div>
          </div>
        )}

        {hasIntent && (
          <div className="flex items-center justify-between">
            <span className="text-gray-500">{t('chat.visitor.aiInsights.intent', '\u610f\u56fe')}</span>
            <span className="text-gray-800 font-medium truncate max-w-[9rem]" title={intent || ''}>{intent}</span>
          </div>
        )}

        {hasSummary && (
          <div className="flex flex-col">
            <span className="text-gray-500 mb-1">{t('chat.visitor.aiInsights.insightSummary', '\u6d1e\u5bdf\u6458\u8981')}</span>
            <p className="text-gray-800 text-[13px] leading-5 whitespace-pre-wrap break-words">{insightSummary}</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default AIInsightsSection;
