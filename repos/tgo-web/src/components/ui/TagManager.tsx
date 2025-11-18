import React, { useState, useEffect, useRef, useMemo } from 'react';
import { useTranslation } from 'react-i18next';

import { X, Check, Edit3, RefreshCw } from 'lucide-react';
import type { VisitorTag } from '@/data/mockVisitor';

interface SuggestedTag {
  id: string;
  name: string;
  color: string;
  weight: number;
}

interface TagManagerProps {
  tags: VisitorTag[];
  onAddTag: (tag: Omit<VisitorTag, 'id'>) => void;
  onUpdateTag: (id: string, updates: Partial<VisitorTag>) => void;
  onRemoveTag: (id: string) => void;
  // New props for API-driven suggestions and association
  fetchCommonTags: () => Promise<SuggestedTag[]>;
  onAssociateExistingTag: (id: string) => void;
  maxTags?: number;
  className?: string;
}

// 颜色选项
const COLOR_OPTIONS = [
  { name: 'red', label: '红色', class: 'bg-red-100 text-red-700 border-red-200', hex: '#fecaca' },
  { name: 'orange', label: '橙色', class: 'bg-orange-100 text-orange-700 border-orange-200', hex: '#fed7aa' },
  { name: 'yellow', label: '黄色', class: 'bg-yellow-100 text-yellow-700 border-yellow-200', hex: '#fef3c7' },
  { name: 'green', label: '绿色', class: 'bg-green-100 text-green-700 border-green-200', hex: '#dcfce7' },
  { name: 'emerald', label: '翠绿', class: 'bg-emerald-100 text-emerald-700 border-emerald-200', hex: '#d1fae5' },
  { name: 'teal', label: '青色', class: 'bg-teal-100 text-teal-700 border-teal-200', hex: '#ccfbf1' },
  { name: 'blue', label: '蓝色', class: 'bg-blue-100 text-blue-700 border-blue-200', hex: '#dbeafe' },
  { name: 'indigo', label: '靛蓝', class: 'bg-indigo-100 text-indigo-700 border-indigo-200', hex: '#e0e7ff' },
  { name: 'purple', label: '紫色', class: 'bg-purple-100 text-purple-700 border-purple-200', hex: '#f3e8ff' },
  { name: 'pink', label: '粉色', class: 'bg-pink-100 text-pink-700 border-pink-200', hex: '#fce7f3' },
  { name: 'gray', label: '灰色', class: 'bg-gray-100 text-gray-700 border-gray-200', hex: '#f3f4f6' }
];

// 预设标签改为由父组件通过 API 获取并下发
// 建议标签（常用标签）在点击“+ 添加”时请求后端获取

// 获取标签颜色类
const getTagColorClass = (colorName: string): string => {
  const color = COLOR_OPTIONS.find(c => c.name === colorName);
  return color ? color.class : 'bg-gray-50 text-gray-700 border-gray-200';
};

// 获取权重样式
const getWeightStyle = (weight: number): string => {
  if (weight >= 9) return 'ring-2 ring-offset-1 font-bold'; // 高权重：双环边框 + 粗体
  if (weight >= 7) return 'border-2 font-semibold'; // 中高权重：粗边框 + 半粗体
  if (weight >= 4) return 'font-medium'; // 中权重：中等字体
  if (weight >= 1) return ''; // 低权重：默认样式
  return 'opacity-60'; // 权重为0：半透明显示
};

/**
 * Tag manager component for adding and removing tags
 */
const TagManager: React.FC<TagManagerProps> = ({
  tags,
  onAddTag,
  onUpdateTag,
  onRemoveTag,
  fetchCommonTags,
  onAssociateExistingTag,
  maxTags = 8,


  className = ''
}) => {
  const { t } = useTranslation();

  const [isAdding, setIsAdding] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [newTag, setNewTag] = useState('');
  const [newColor, setNewColor] = useState('blue');
  const [newWeight, setNewWeight] = useState(0);
  const [showPresets, setShowPresets] = useState(false);
  const [showColorPicker, setShowColorPicker] = useState(false);
  const [panelPosition, setPanelPosition] = useState({ top: 0, left: 16 });
  const [suggestions, setSuggestions] = useState<SuggestedTag[]>([]);
  const [suggestionsLoading, setSuggestionsLoading] = useState(false);
  const [suggestionsError, setSuggestionsError] = useState<string | null>(null);
  const editPanelRef = useRef<HTMLDivElement>(null);
  const tagRefs = useRef<{ [key: string]: HTMLDivElement | null }>({});

  // 点击外部关闭编辑面板
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (editingId && editPanelRef.current && !editPanelRef.current.contains(event.target as Node)) {
        setEditingId(null);
      }
    };

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape' && editingId) {
        setEditingId(null);
      }
    };

    if (editingId) {
      document.addEventListener('mousedown', handleClickOutside);
      document.addEventListener('keydown', handleKeyDown);
      return () => {
        document.removeEventListener('mousedown', handleClickOutside);
        document.removeEventListener('keydown', handleKeyDown);
      };
    }

    return undefined;
  }, [editingId]);

  // 计算编辑面板位置
  useEffect(() => {
    if (editingId && tagRefs.current[editingId]) {
      const tagElement = tagRefs.current[editingId];
      if (tagElement) {
        const rect = tagElement.getBoundingClientRect();
        const visitorPanelRect = tagElement.closest('aside')?.getBoundingClientRect();

        if (visitorPanelRect) {
          // 计算相对于访客面板的位置
          const relativeTop = rect.top - visitorPanelRect.top;
          setPanelPosition({
            top: Math.max(16, relativeTop + 32), // 确保不会超出顶部，标签下方32px
            left: 16 // 固定在访客面板左侧16px
          });
        }
      }
    }
  }, [editingId]);

  const handleStartAdd = async () => {
    setIsAdding(true);
    setNewTag('');
    setNewColor('blue');
    setNewWeight(0);
    setShowPresets(true);
    setShowColorPicker(false);

    // 获取常用标签（后端接口）
    try {
      setSuggestionsLoading(true);
      setSuggestionsError(null);
      const data = await fetchCommonTags();
      setSuggestions(data);
    } catch (e) {
      setSuggestionsError(t('chat.visitor.tags.common.loadFailed', '获取常用标签失败'));
    } finally {
      setSuggestionsLoading(false);
    }
  };

  const handleCancelAdd = () => {
    setIsAdding(false);
    setNewTag('');
    setShowPresets(false);
    setShowColorPicker(false);
  };

  const handleSaveAdd = () => {
    if (newTag.trim() && !tags.some(tag => tag.name === newTag.trim()) && tags.length < maxTags) {
      onAddTag({
        name: newTag.trim(),
        color: newColor,
        weight: newWeight
      });
      handleCancelAdd();
    }
  };

  const handlePresetSelect = (preset: SuggestedTag) => {
    if (!tags.some(tag => tag.name === preset.name) && tags.length < maxTags) {
      // 选择常用标签：直接建立关联
      onAssociateExistingTag(preset.id);
      handleCancelAdd();
    }
  };

  const handleStartEdit = (tag: VisitorTag) => {
    setEditingId(tag.id);
  };

  const handleUpdateWeight = (id: string, weight: number) => {
    onUpdateTag(id, { weight });
  };

  const handleUpdateColor = (id: string, color: string) => {
    onUpdateTag(id, { color });
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleSaveAdd();
    } else if (e.key === 'Escape') {
      e.preventDefault();
      handleCancelAdd();
    }
  };

  // 过滤出未使用的建议标签（来自后端）
  const availablePresets = suggestions
    .filter(preset => !tags.some(tag => tag.name === preset.name))
    .filter(preset => preset.name.toLowerCase().includes(newTag.toLowerCase()))
    .slice(0, 6);

  // 只在tags数据变化时重新计算排序，避免编辑状态切换时的不必要计算
  const sortedTags = useMemo(() => {
    return [...tags].sort((a, b) => b.weight - a.weight);
  }, [tags]);


  return (
    <div className={className}>
      {/* 现有标签 */}
      <div className="flex flex-wrap gap-1.5">
        {sortedTags.map((tag) => (
          <div
            key={tag.id}
            ref={(el) => { tagRefs.current[tag.id] = el; }}
            className="group relative"
          >
            <span
              className={`text-[11px] leading-tight px-2 py-1 rounded-full border ${getTagColorClass(tag.color)} ${getWeightStyle(tag.weight)}`}
            >
              {tag.name}
              {tag.weight >= 8 && (
                <span className="ml-1 text-[8px] opacity-70">★</span>
              )}
            </span>

            {/* 编辑和删除按钮 */}
            <div className="absolute -top-1 -right-1 flex space-x-0.5 opacity-0 group-hover:opacity-100 transition-opacity">
              <button
                onClick={() => handleStartEdit(tag)}
                className="w-3.5 h-3.5 bg-blue-500 text-white rounded-full flex items-center justify-center"
                title={t('chat.visitor.tags.editTagTitle', '编辑标签')}
              >
                <Edit3 className="w-2 h-2" />
              </button>
              <button
                onClick={() => onRemoveTag(tag.id)}
                className="w-3.5 h-3.5 bg-red-500 text-white rounded-full flex items-center justify-center"
                title={t('chat.visitor.tags.deleteTagTitle', '删除标签')}
              >
                <X className="w-2 h-2" />
              </button>
            </div>

            {/* 编辑面板 */}
            {editingId === tag.id && (
              <div
                ref={editPanelRef}
                className="fixed z-50 bg-white border border-gray-200 rounded-lg shadow-xl p-3 min-w-[200px] max-w-[240px]"
                style={{
                  top: `${panelPosition.top}px`,
                  left: `${panelPosition.left}px`,
                  boxShadow: '0 10px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)'
                }}
              >
                <div className="space-y-2">
                  <div>
                    <label className="text-[10px] text-gray-500 block mb-1">{t('chat.visitor.tags.editPanel.weightLabel', '权重 (0-10)')}</label>
                    <input
                      type="range"
                      min="0"
                      max="10"
                      value={tag.weight}
                      onChange={(e) => handleUpdateWeight(tag.id, parseInt(e.target.value))}
                      className="w-full h-1 bg-gray-200 rounded-lg appearance-none cursor-pointer"
                    />
                    <div className="text-[10px] text-gray-400 text-center">{tag.weight}</div>
                  </div>

                  <div>
                    <label className="text-[10px] text-gray-500 block mb-1">{t('chat.visitor.tags.editPanel.colorLabel', '颜色')}</label>
                    <div className="flex flex-wrap gap-1">
                      {COLOR_OPTIONS.slice(0, 6).map((color) => (
                        <button
                          key={color.name}
                          onClick={() => handleUpdateColor(tag.id, color.name)}
                          className={`w-4 h-4 rounded-full border-2 ${
                            tag.color === color.name ? 'border-gray-800' : 'border-gray-300'
                          }`}
                          style={{ backgroundColor: color.hex }}
                          title={t(`chat.visitor.tags.colors.${color.name}`, color.label)}
                        />
                      ))}
                    </div>
                  </div>

                  <button
                    onClick={() => setEditingId(null)}
                    className="w-full text-[10px] text-gray-500 hover:text-gray-700 py-1"
                  >
                    {t('common.done', '完成')}
                  </button>
                </div>
              </div>
            )}
          </div>
        ))}

        {/* 添加标签按钮/输入框 */}
        {isAdding ? (
          <div className="relative">
            <div className="flex items-center space-x-1 mb-2">
              <input
                type="text"
                value={newTag}
                onChange={(e) => setNewTag(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder={t('chat.visitor.tags.inputPlaceholder', '输入标签名称')}
                className="w-20 px-2 py-1 text-[11px] border border-gray-300 rounded-full focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
                autoFocus
              />
              <button
                onClick={() => setShowColorPicker(!showColorPicker)}
                className="p-1 border border-gray-300 rounded-full"
                title={t('chat.visitor.tags.colorPicker.title', '选择颜色')}
              >
                <div
                  className="w-3 h-3 rounded-full"
                  style={{ backgroundColor: COLOR_OPTIONS.find(c => c.name === newColor)?.hex || '#f3f4f6' }}
                />
              </button>
              <input
                type="range"
                min="0"
                max="10"
                value={newWeight}
                onChange={(e) => setNewWeight(parseInt(e.target.value))}
                className="w-8 h-1 bg-gray-200 rounded-lg appearance-none cursor-pointer"
                title={t('chat.visitor.tags.weightTitle', { weight: newWeight, defaultValue: '权重: {{weight}}' })}
              />
              <button
                onClick={handleSaveAdd}
                disabled={!newTag.trim() || tags.some(tag => tag.name === newTag.trim()) || tags.length >= maxTags}
                className="p-0.5 text-green-600 hover:bg-green-50 rounded transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                title={t('common.save', '保存')}
              >
                <Check className="w-3 h-3" />
              </button>
              <button
                onClick={handleCancelAdd}
                className="p-0.5 text-gray-500 hover:bg-gray-50 rounded transition-colors"
                title={t('common.cancel', '取消')}
              >
                <X className="w-3 h-3" />
              </button>
            </div>

            {/* 颜色选择器 */}
            {showColorPicker && (
              <div className="absolute top-8 left-0 z-10 bg-white border border-gray-200 rounded-lg shadow-lg p-2">
                <div className="grid grid-cols-4 gap-1">
                  {COLOR_OPTIONS.map((color) => (
                    <button
                      key={color.name}
                      onClick={() => {
                        setNewColor(color.name);
                        setShowColorPicker(false);
                      }}
                      className={`w-6 h-6 rounded-full border-2 ${
                        newColor === color.name ? 'border-gray-800' : 'border-gray-300'
                      }`}
                      style={{ backgroundColor: color.hex }}
                      title={t(`chat.visitor.tags.colors.${color.name}`, color.label)}
                    />
                  ))}
                </div>
              </div>
            )}
          </div>
        ) : (
          tags.length < maxTags && (
            <button
              onClick={handleStartAdd}
              className="text-xs text-blue-600 hover:text-blue-700 hover:bg-blue-50 px-2 py-1 rounded-full transition-colors font-medium"
            >
              + {t('chat.visitor.tags.addButton', '添加')}
            </button>
          )
        )}
      </div>

      {/* 预设标签选择 */}
      {isAdding && showPresets && (
        <div className="mt-2 space-y-1">
          <div className="flex items-center justify-between">
            <div className="text-[10px] text-gray-500 font-medium">{t('chat.visitor.tags.common.title', '常用标签:')}</div>
            {suggestionsLoading && (
              <div className="flex items-center text-[10px] text-gray-400">
                <RefreshCw className="w-3 h-3 mr-1 animate-spin" /> {t('chat.visitor.tags.common.loading', '加载中')}
              </div>
            )}
          </div>
          {suggestionsError && (
            <div className="text-[10px] text-red-500">{suggestionsError}</div>
          )}
          <div className="flex flex-wrap gap-1">
            {availablePresets.map((preset) => (
              <button
                key={preset.id}
                onClick={() => handlePresetSelect(preset)}
                className={`text-[10px] leading-tight px-1.5 py-0.5 rounded-full border transition-colors hover:opacity-80 ${getTagColorClass(preset.color)} ${getWeightStyle(preset.weight)}`}
              >
                {preset.name}
                {preset.weight >= 8 && (
                  <span className="ml-1 text-[8px] opacity-70">★</span>
                )}
              </button>
            ))}
            {!suggestionsLoading && availablePresets.length === 0 && (
              <div className="text-[10px] text-gray-400">{t('chat.visitor.tags.common.empty', '暂无可用标签')}</div>
            )}
          </div>
        </div>
      )}

      {/* 标签数量提示 */}
      {tags.length >= maxTags && (
        <div className="mt-1 text-[10px] text-gray-400">
          {t('chat.visitor.tags.limitReached', { max: maxTags, defaultValue: '已达到标签数量上限 ({{max}}个)' })}
        </div>
      )}
    </div>
  );
};

export default TagManager;
