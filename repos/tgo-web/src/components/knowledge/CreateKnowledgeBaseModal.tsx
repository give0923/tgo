import React, { useState } from 'react';
import { X } from 'lucide-react';
import { IconPicker, DEFAULT_ICON } from './IconPicker';
import { TagInput } from '@/components/ui/TagInput';

import { useTranslation } from 'react-i18next';

interface CreateKnowledgeBaseModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: { name: string; description: string; icon: string; tags: string[] }) => Promise<void>;
  isLoading?: boolean;
}

export const CreateKnowledgeBaseModal: React.FC<CreateKnowledgeBaseModalProps> = ({
  isOpen,
  onClose,
  onSubmit,
  isLoading = false
}) => {
  const { t } = useTranslation();

  const [formData, setFormData] = useState({
    name: '',
    description: '',
    icon: DEFAULT_ICON,
    tags: [] as string[]
  });
  const [errors, setErrors] = useState({
    name: '',
    description: ''
  });

  // Reset form when modal opens/closes
  React.useEffect(() => {
    if (isOpen) {
      setFormData({ name: '', description: '', icon: DEFAULT_ICON, tags: [] });
      setErrors({ name: '', description: '' });
    }
  }, [isOpen]);

  const validateForm = (): boolean => {
    const newErrors = { name: '', description: '' };
    let isValid = true;

    // Validate name
    if (!formData.name.trim()) {
      newErrors.name = t('knowledge.validation.nameRequired', '知识库名称不能为空');
      isValid = false;
    } else if (formData.name.trim().length < 2) {
      newErrors.name = t('knowledge.validation.nameMin', '知识库名称至少需要2个字符');
      isValid = false;
    } else if (formData.name.trim().length > 50) {
      newErrors.name = t('knowledge.validation.nameMax', '知识库名称不能超过50个字符');
      isValid = false;
    }

    // Validate description
    if (!formData.description.trim()) {
      newErrors.description = t('knowledge.validation.descRequired', '知识库描述不能为空');
      isValid = false;
    } else if (formData.description.trim().length < 5) {
      newErrors.description = t('knowledge.validation.descMin', '知识库描述至少需要5个字符');
      isValid = false;
    } else if (formData.description.trim().length > 500) {
      newErrors.description = t('knowledge.validation.descMax', '知识库描述不能超过500个字符');
      isValid = false;
    }

    setErrors(newErrors);
    return isValid;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateForm()) {
      return;
    }

    try {
      await onSubmit({
        name: formData.name.trim(),
        description: formData.description.trim(),
        icon: formData.icon,
        tags: formData.tags
      });
      onClose();
    } catch (error) {
      // Error handling is done by the parent component
      console.error('Failed to create knowledge base:', error);
    }
  };

  const handleInputChange = (field: 'name' | 'description', value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));

    // Clear error when user starts typing
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: '' }));
    }
  };

  const handleIconChange = (iconName: string) => {
    setFormData(prev => ({ ...prev, icon: iconName }));
  };

  const handleTagsChange = (tags: string[]) => {
    setFormData(prev => ({ ...prev, tags }));
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-md mx-4">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-800">{t('knowledge.create', '创建知识库')}</h2>
          <button
            onClick={onClose}
            disabled={isLoading}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6">
          <div className="space-y-4">
            {/* Icon Field */}
            <div>
              <label htmlFor="kb-icon" className="block text-sm font-medium text-gray-700 mb-1">
                {t('knowledge.icon', '知识库图标')}
              </label>
              <IconPicker
                selectedIcon={formData.icon}
                onIconSelect={handleIconChange}
                disabled={isLoading}
              />
              <p className="mt-1 text-xs text-gray-500">
                {t('knowledge.iconHelper', '选择一个图标来标识您的知识库')}
              </p>
            </div>

            {/* Name Field */}
            <div>
              <label htmlFor="kb-name" className="block text-sm font-medium text-gray-700 mb-1">
                {t('knowledge.name', '知识库名称')} <span className="text-red-500">*</span>
              </label>
              <input
                id="kb-name"
                type="text"
                value={formData.name}
                onChange={(e) => handleInputChange('name', e.target.value)}
                placeholder={t('knowledge.namePlaceholder', '请输入知识库名称')}
                disabled={isLoading}
                className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors ${
                  errors.name ? 'border-red-300 bg-red-50' : 'border-gray-300'
                } ${isLoading ? 'bg-gray-100 cursor-not-allowed' : ''}`}
                maxLength={50}
              />
              {errors.name && (
                <p className="mt-1 text-sm text-red-600">{errors.name}</p>
              )}
              <p className="mt-1 text-xs text-gray-500">
                {formData.name.length}/50 {t('common.characters', '字符')}
              </p>
            </div>

            {/* Description Field */}
            <div>
              <label htmlFor="kb-description" className="block text-sm font-medium text-gray-700 mb-1">
                {t('knowledge.description', '知识库描述')} <span className="text-red-500">*</span>
              </label>
              <textarea
                id="kb-description"
                value={formData.description}
                onChange={(e) => handleInputChange('description', e.target.value)}
                placeholder={t('knowledge.descriptionPlaceholder', '请输入知识库描述，简要说明这个知识库的用途和内容')}
                disabled={isLoading}
                rows={3}
                className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors resize-none ${
                  errors.description ? 'border-red-300 bg-red-50' : 'border-gray-300'
                } ${isLoading ? 'bg-gray-100 cursor-not-allowed' : ''}`}
                maxLength={500}
              />
              {errors.description && (
                <p className="mt-1 text-sm text-red-600">{errors.description}</p>
              )}
              <p className="mt-1 text-xs text-gray-500">
                {formData.description.length}/500 {t('common.characters', '字符')}
              </p>
            </div>

            {/* Tags Field */}
            <div>
              <label htmlFor="kb-tags" className="block text-sm font-medium text-gray-700 mb-1">
                {t('knowledge.tags', '知识库标签')}
              </label>
              <TagInput
                tags={formData.tags}
                onTagsChange={handleTagsChange}
                placeholder={t('knowledge.tagsPlaceholder', '输入标签并按回车键添加')}
                maxTags={10}
                maxTagLength={20}
                disabled={isLoading}
              />
              <p className="mt-1 text-xs text-gray-500">
                {t('knowledge.tagsHelper', '添加标签可以帮助您更好地组织和查找知识库')}
              </p>
            </div>
          </div>

          {/* Footer */}
          <div className="flex justify-end space-x-3 mt-6 pt-4 border-t border-gray-200">
            <button
              type="button"
              onClick={onClose}
              disabled={isLoading}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 border border-gray-300 rounded-md hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {t('common.cancel', '取消')}
            </button>
            <button
              type="submit"
              disabled={isLoading}
              className="px-4 py-2 text-sm font-medium text-white bg-blue-500 border border-transparent rounded-md hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
            >
              {isLoading ? (
                <>
                  <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  {t('common.creating', '创建中...')}
                </>
              ) : (
                t('knowledge.create', '创建知识库')
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
