import React from 'react';
import { useTranslation } from 'react-i18next';

interface ReplySuggestionsProps {
  suggestions?: string[];
  onSuggestionClick?: (suggestion: string) => void;
}

/**
 * Reply suggestions component for AI-powered quick replies
 */
const ReplySuggestions: React.FC<ReplySuggestionsProps> = ({ suggestions, onSuggestionClick }) => {
  const { t } = useTranslation();
  if (!suggestions || suggestions.length === 0) return null;

  const handleSuggestionClick = (suggestion: string): void => {
    onSuggestionClick?.(suggestion);
  };

  return (
    <div className="mt-2 ml-10 pl-2 flex items-center gap-2 border-l border-dashed border-gray-300">
      <span className="text-xs text-gray-400">{t('chat.suggestions.label', '✨ Suggestions:')}</span>
      {suggestions.map((suggestion, index) => (
        <button
          key={index}
          className="text-xs bg-gray-100 hover:bg-gray-200 text-gray-700 px-2 py-1 rounded-full border border-gray-200 transition-colors"
          onClick={() => handleSuggestionClick(suggestion)}
        >
          {suggestion}
        </button>
      ))}
    </div>
  );
};

export default ReplySuggestions;
