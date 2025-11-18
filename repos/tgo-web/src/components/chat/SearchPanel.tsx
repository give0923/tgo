import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { createPortal } from 'react-dom';
import DOMPurify from 'dompurify';
import Icon from '@/components/ui/Icon';
import Pagination from '@/components/ui/Pagination';
import { useTranslation } from 'react-i18next';
import { searchApiService, type SearchRequestParams } from '@/services/searchApi';
import type {
  SearchScope,
  UnifiedSearchResponse,
  VisitorBasicResponse,
  MessageSearchResult,
  ChannelVisitorExtra,
  ChannelInfo,
  Chat,
} from '@/types';
import { PlatformType } from '@/types';
import { useToast } from '@/hooks/useToast';
import { showApiError } from '@/utils/toastHelpers';
import { useChatStore } from '@/stores/chatStore';
import { CHAT_PRIORITY, CHAT_STATUS, DEFAULT_CHANNEL_TYPE, VISITOR_STATUS } from '@/constants';
import { getChannelKey } from '@/utils/channelUtils';
import { ChatAvatar } from '@/components/chat/ChatAvatar';
import { ChatPlatformIcon } from '@/components/chat/ChatPlatformIcon';
import { toPlatformType } from '@/utils/platformUtils';

export interface SearchPanelProps {
  open: boolean;
  onClose: () => void;
}

// Tabs are defined inside component to access i18n translations

const SearchPanel: React.FC<SearchPanelProps> = ({ open, onClose }) => {
  const { showToast } = useToast();
  const [query, setQuery] = useState('');
  const [activeTab, setActiveTab] = useState<SearchScope>('all');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<UnifiedSearchResponse | null>(null);

  const [visitorPage, setVisitorPage] = useState(1);
  const [messagePage, setMessagePage] = useState(1);

  const inputRef = useRef<HTMLInputElement>(null);
  const panelRef = useRef<HTMLDivElement>(null);
  const debounceTimerRef = useRef<any>(null);
  const { t, i18n } = useTranslation();

  const tabs = useMemo(() => (
    [
      { key: 'all' as SearchScope, label: t('search.tabs.all', '所有'), icon: 'Grid' },
      { key: 'visitors' as SearchScope, label: t('search.tabs.visitors', '访客'), icon: 'Users' },
      { key: 'messages' as SearchScope, label: t('search.tabs.messages', '消息'), icon: 'MessageSquareText' },
    ]
  ), [t]);

  // Autofocus when open
  useEffect(() => {
    if (open) {
      // reset state when opening
      setError(null);
      setLoading(false);
      // Focus input
      setTimeout(() => inputRef.current?.focus(), 0);
    } else {
      setData(null);
      setQuery('');
      setVisitorPage(1);
      setMessagePage(1);
      setActiveTab('all');
    }
  }, [open]);

  // Close on ESC
  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [open, onClose]);

  // Click outside to close
  const handleBackdropClick = useCallback((e: React.MouseEvent) => {
    if (e.target === e.currentTarget) onClose();
  }, [onClose]);

  const doSearch = useCallback(async (params: SearchRequestParams) => {
    setLoading(true);
    setError(null);
    try {
      const resp = await searchApiService.unifiedSearch(params);
      setData(resp);
    } catch (err) {
      const msg = err instanceof Error ? err.message : t('search.errorGeneric', '\u641c\u7d22\u5931\u8d25\uff0c\u8bf7\u7a0d\u540e\u91cd\u8bd5');
      setError(msg);
      showApiError(showToast, err);
    } finally {
      setLoading(false);
    }
  }, [showToast]);

  // Debounced search on query or tab/page change
  useEffect(() => {
    if (!open) return;
    if (!query || query.trim().length === 0) {
      setData(null);
      return;
    }

    // Reset page when tab changes or query changes
    setVisitorPage(p => (activeTab !== 'messages' ? p : 1));
    setMessagePage(p => (activeTab !== 'visitors' ? p : 1));

    const params: SearchRequestParams = {
      q: query.trim(),
      scope: activeTab,
      visitor_page: visitorPage,
      message_page: messagePage,
    };

    if (debounceTimerRef.current) clearTimeout(debounceTimerRef.current);
    debounceTimerRef.current = setTimeout(() => doSearch(params), 300);

    return () => {
      if (debounceTimerRef.current) clearTimeout(debounceTimerRef.current);
    };
  }, [open, query, activeTab, visitorPage, messagePage, doSearch]);

  const handleChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    setQuery(e.target.value);
  }, []);

  const handleClear = useCallback(() => {
    setQuery('');
    setData(null);
    setError(null);
    inputRef.current?.focus();
  }, []);

  const chatsStore = useChatStore.getState();

  // 打开既有会话（按 channelId/channelType 查找）
  const openConversation = useCallback((channelId?: string | null, channelType?: number | null) => {
    if (!channelId) {
      showToast('info', t('search.toasts.notFoundTitle', '未找到会话'), t('search.toasts.noConversationInfo', '该结果缺少会话信息'));
      return;
    }
    const type = channelType ?? DEFAULT_CHANNEL_TYPE;
    const chat = chatsStore.chats.find(c => c.channelId === channelId && c.channelType === type);
    if (chat) {
      chatsStore.setActiveChat(chat);
      onClose();
    } else {
      showToast('info', t('search.toasts.notFoundTitle', '未找到会话'), t('search.toasts.notInRecent', '该会话不在最近列表中，请尝试刷新'));
    }
  }, [onClose, showToast]);

  // 打开访客最近会话（若不存在则创建）
  const openVisitorConversation = useCallback((v: VisitorBasicResponse) => {
    try {
      const visitorId = v?.id;
      if (!visitorId) {
        showToast('warning', t('search.toasts.incompleteVisitorInfo', '访客信息不完整'), t('search.toasts.missingVisitorId', '缺少 visitor_id'));
        return;
      }
      const channelId = `${visitorId}-vtr`;
      const channelType = 251; // 访客会话类型

      // 1) 已存在则直接切换
      const exist = chatsStore.chats.find(c => c.channelId === channelId && c.channelType === channelType);
      if (exist) {
        chatsStore.setActiveChat(exist);
        onClose();
        return;
      }

      // 2) 不存在则新建 Chat 对象并插入到顶部
      const fallbackName = t('visitor.fallbackName', '\u8bbf\u5ba2 {{suffix}}').replace('{{suffix}}', v.platform_open_id.slice(-4));
      const rawName = (v.name || v.nickname || fallbackName) as string;
      const plainName = (rawName || '').replace(/<[^>]*>/g, '') || fallbackName;

      const key = getChannelKey(channelId, channelType);
      const nowIso = new Date().toISOString();
      const nowSec = Math.floor(Date.now() / 1000);

      const extra: ChannelVisitorExtra = {
        id: v.id,
        platform_id: v.platform_id,
        platform_type: (v.platform_type ?? PlatformType.WEBSITE),
        platform_open_id: v.platform_open_id,
        name: v.name || undefined,
        nickname: v.nickname || undefined,
        avatar_url: v.avatar_url || undefined,
        is_online: v.is_online,
        created_at: v.created_at,
        updated_at: v.updated_at,
        ai_disabled: v.ai_disabled ?? undefined,
      } as any;

      const channelInfo: ChannelInfo = {
        name: plainName,
        avatar: v.avatar_url || '',
        channel_id: channelId,
        channel_type: channelType,
        extra,
      };

      const newChat: Chat = {
        id: key,
        platform: (v.platform_type ?? PlatformType.WEBSITE) as unknown as string,
        lastMessage: '',
        timestamp: nowIso,
        lastTimestampSec: nowSec,
        status: CHAT_STATUS.ACTIVE,
        unreadCount: 0,
        channelId,
        channelType,
        lastMsgSeq: 0,
        channelInfo,
        tags: [],
        priority: CHAT_PRIORITY.NORMAL,
        visitorStatus: v.is_online ? VISITOR_STATUS.ONLINE : VISITOR_STATUS.OFFLINE,
      } as any;

      chatsStore.setChats([newChat, ...chatsStore.chats]);
      chatsStore.setActiveChat(newChat);
      onClose();
    } catch (e) {
      console.error('打开访客会话失败', e);
      showApiError(showToast, e);
    }
  }, [onClose, showToast]);

  const renderVisitorItem = useCallback((v: VisitorBasicResponse) => {
    const fallbackName = t('visitor.fallbackName', '\u8bbf\u5ba2 {{suffix}}').replace('{{suffix}}', v.platform_open_id.slice(-4));
    const rawName = (v.name || v.nickname || fallbackName) as string;
    const plainName = (rawName || '').replace(/<[^>]*>/g, '') || fallbackName;
    const nameHtml = DOMPurify.sanitize(rawName || '');
    const platformType: PlatformType = v.platform_type ?? PlatformType.WEBSITE;

    return (
      <button
        key={v.id}
        className="w-full flex items-center p-2 rounded-md hover:bg-gray-50 text-left"
        onClick={() => openVisitorConversation(v)}
      >
        {/* Avatar - use same logic as ChatList */}
        <ChatAvatar displayName={plainName} displayAvatar={v.avatar_url || ''} visitorStatus={v.is_online ? 'online' : 'offline'} />

        <div className="flex-1 min-w-0">
          <div className="flex items-center min-w-0">
            <div className="text-sm font-medium text-gray-900 truncate search-html" dangerouslySetInnerHTML={{ __html: nameHtml }} />
            <ChatPlatformIcon platformType={platformType} />
          </div>
        </div>
        <Icon name="ChevronRight" size={16} className="text-gray-300" />
      </button>
    );
  }, [openConversation]);

  const renderMessageItem = useCallback((m: MessageSearchResult) => {
    const rawPreview = (m.preview_text || m.stream_data || (typeof m.payload === 'object' ? (m.payload as any).content : '') || '').toString();
    const time = m.timestamp ? new Date(m.timestamp * 1000).toLocaleString(i18n.language || undefined) : '';
    const hasPreview = rawPreview && rawPreview.trim().length > 0;
    const previewHtml = hasPreview ? DOMPurify.sanitize(rawPreview) : '';

    const channelId = m.channel_id || undefined;
    const channelType = m.channel_type ?? DEFAULT_CHANNEL_TYPE;
    const chat = channelId ? chatsStore.chats.find(c => c.channelId === channelId && c.channelType === channelType) : undefined;

    const displayName = chat?.channelInfo?.name || (channelId ? t('visitor.fallbackName', '\u8bbf\u5ba2 {{suffix}}').replace('{{suffix}}', String(channelId).slice(-4)) : t('search.channel', '\u4f1a\u8bdd'));
    const displayAvatar = chat?.channelInfo?.avatar || '';
    const platformType: PlatformType | undefined = chat ? (() => {
      const extra: any = chat.channelInfo?.extra;
      const fromExtra = (extra && typeof extra === 'object' && 'platform_type' in extra) ? (extra.platform_type as PlatformType) : undefined;
      return fromExtra ?? toPlatformType(chat.platform);
    })() : undefined;

    return (
      <button
        key={m.message_id_str}
        className="w-full flex items-start p-2 rounded-md hover:bg-gray-50 text-left"
        onClick={() => {
          if (channelId && typeof m.message_seq === 'number') {
            useChatStore.getState().setTargetMessageLocation({ channelId, channelType, messageSeq: m.message_seq });
          }
          openConversation(channelId || undefined, channelType || undefined);
        }}
      >
        {/* Avatar - consistent with ChatList */}
        <ChatAvatar displayName={displayName} displayAvatar={displayAvatar} />
        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between">
            <div className="flex items-center min-w-0">
              <div className="text-sm font-medium text-gray-900 truncate mr-1">{displayName}</div>
              {platformType ? <ChatPlatformIcon platformType={platformType} /> : null}
            </div>
            <div className="text-xs text-gray-500 flex-shrink-0 ml-2">{time}</div>
          </div>
          {hasPreview ? (
            <div className="text-sm text-gray-900 line-clamp-2 whitespace-pre-wrap break-words search-html mt-0.5" dangerouslySetInnerHTML={{ __html: previewHtml }} />
          ) : (
            <div className="text-sm text-gray-400 mt-0.5">{t('search.noPreview', '\uff08\u65e0\u9884\u89c8\u5185\u5bb9\uff09')}</div>
          )}
        </div>
        <Icon name="ChevronRight" size={16} className="text-gray-300 ml-2" />
      </button>
    );
  }, [openConversation]);

  const visitorTotalPages = useMemo(() => {
    const p = data?.visitor_pagination;
    return p ? Math.max(1, Math.ceil((p.total || 0) / (p.page_size || 10))) : 1;
  }, [data]);
  const messageTotalPages = useMemo(() => {
    const p = data?.message_pagination;
    return p ? Math.max(1, Math.ceil((p.total || 0) / (p.page_size || 20))) : 1;
  }, [data]);

  if (!open) return null;

  return createPortal(
    <div className="fixed inset-0 z-[9999] bg-black/20 backdrop-blur-sm flex items-start justify-center pt-8 md:pt-16 px-2 md:px-6" onClick={handleBackdropClick}>
      <div ref={panelRef} className="w-full md:max-w-3xl max-h-[80vh] md:max-h-[70vh] bg-white/90 backdrop-blur-lg border border-gray-200/60 rounded-xl shadow-2xl ring-1 ring-black/5 flex flex-col overflow-hidden" onClick={(e) => e.stopPropagation()}>
        {/* Header search input */}
        <div className="px-4 py-3 border-b border-gray-200/60 bg-white/60 backdrop-blur sticky top-0 z-10 flex items-center gap-2">
          <div className="relative flex-1">
            <Icon name="Search" size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
            <input
              ref={inputRef}
              value={query}
              onChange={handleChange}
              placeholder={t('search.placeholder', '\u641c\u7d22\u8bbf\u5ba2\u6216\u6d88\u606f')}
              className="w-full pl-9 pr-9 py-2.5 text-sm border border-gray-200/70 rounded-full bg-gray-50/80 focus:outline-none focus:ring-2 focus:ring-blue-500/70 focus:border-blue-500"
            />
            {query && (
              <button className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600" onClick={handleClear} aria-label={t('common.clear', '\u6e05\u7a7a')} title={t('common.clear', '\u6e05\u7a7a')}>
                <Icon name="X" size={16} />
              </button>
            )}
          </div>
          <button className="p-2 rounded-md hover:bg-gray-100" onClick={onClose} aria-label={t('common.close', '\u5173\u95ed')} title={t('common.close', '\u5173\u95ed')}>
            <Icon name="X" size={18} />
          </button>
        </div>

        {/* Local highlight styles for sanitized HTML */}
        <style>{`
          .search-html mark {
            background-color: #FEF08A; /* Tailwind yellow-200 */
            color: #111827; /* Tailwind gray-900 */
            padding: 0 2px;
            border-radius: 4px;
            box-shadow: inset 0 0 0 1px rgba(0,0,0,0.04);
          }
        `}</style>

        {/* Tabs */}
        <div className="px-4 pt-2 border-b border-gray-100/80 bg-white/40 backdrop-blur">
          <div className="flex items-center justify-between">
            <div className="inline-flex items-center gap-1 rounded-md bg-gray-100/60 p-1 ring-1 ring-inset ring-gray-200/60" role="tablist" aria-label={t('search.aria.tablist', '\u641c\u7d22\u5206\u7c7b')}>
              {tabs.map(tab => {
                const isActive = activeTab === tab.key;
                return (
                  <button
                    key={tab.key}
                    role="tab"
                    aria-selected={isActive}
                    onClick={() => setActiveTab(tab.key)}
                    className={`inline-flex items-center px-2.5 py-1.5 text-sm rounded-md transition-all focus:outline-none ${isActive ? 'bg-white text-gray-900 shadow-sm ring-1 ring-gray-200/70' : 'text-gray-600 hover:text-gray-900 hover:bg-white/70'}`}
                  >
                    <Icon name={tab.icon} size={14} className={isActive ? 'text-blue-600' : 'text-gray-500'} />
                    <span className="ml-1.5">{tab.label}</span>
                  </button>
                );
              })}
            </div>
          </div>
        </div>

        {/* Body */}
        <div className="flex-1 overflow-auto px-4 py-3 bg-white/30">
          {!query ? (
            <div className="h-full flex items-center justify-center text-gray-400 text-sm">
              {t('search.emptyQueryHint', '\u8f93\u5165\u5173\u952e\u8bcd\u5f00\u59cb\u641c\u7d22')}
            </div>
          ) : loading ? (
            <div className="h-full flex items-center justify-center text-gray-500 text-sm">
              <Icon name="Loader2" className="animate-spin mr-2" size={16} /> {t('search.searching', '\u6b63\u5728\u641c\u7d22...')}
            </div>
          ) : error ? (
            <div className="h-full flex items-center justify-center text-red-500 text-sm">
              <Icon name="AlertCircle" size={16} className="mr-2" /> {error}
            </div>
          ) : data ? (
            activeTab === 'all' ? (
              <div className="space-y-6">
                {/* Visitors section */}
                <div>
                  <div className="text-xs font-medium text-gray-500 mb-2">{t('search.sections.visitors', '访客')}（{data.visitor_count ?? data.visitors.length}）</div>
                  {data.visitors.length === 0 ? (
                    <div className="text-sm text-gray-400">{t('search.empty.visitors', '\u672a\u627e\u5230\u76f8\u5173\u8bbf\u5ba2')}</div>
                  ) : (
                    <div className="divide-y divide-gray-100 bg-white rounded-md border border-gray-100">
                      {data.visitors.map(v => (
                        <div key={v.id} className="p-1">{renderVisitorItem(v)}</div>
                      ))}
                    </div>
                  )}
                  {data.visitor_pagination && data.visitor_pagination.total > data.visitors.length && (
                    <div className="mt-2">
                      <Pagination
                        currentPage={data.visitor_pagination.page}
                        totalPages={visitorTotalPages}
                        onPageChange={(p) => setVisitorPage(p)}
                      />
                    </div>
                  )}
                </div>

                {/* Messages section */}
                <div>
                  <div className="text-xs font-medium text-gray-500 mb-2">{t('search.sections.messages', '\u6d88\u606f')}（{data.message_count ?? data.messages.length}）</div>
                  {data.messages.length === 0 ? (
                    <div className="text-sm text-gray-400">{t('search.empty.messages', '\u672a\u627e\u5230\u76f8\u5173\u6d88\u606f')}</div>
                  ) : (
                    <div className="divide-y divide-gray-100 bg-white rounded-md border border-gray-100">
                      {data.messages.map(m => (
                        <div key={m.message_id_str} className="p-1">{renderMessageItem(m)}</div>
                      ))}
                    </div>
                  )}
                  {data.message_pagination && data.message_pagination.total > data.messages.length && (
                    <div className="mt-2">
                      <Pagination
                        currentPage={data.message_pagination.page}
                        totalPages={messageTotalPages}
                        onPageChange={(p) => setMessagePage(p)}
                      />
                    </div>
                  )}
                </div>
              </div>
            ) : activeTab === 'visitors' ? (
              <div>
                {data.visitors.length === 0 ? (
                  <div className="text-sm text-gray-400">{t('search.empty.visitors', '\u672a\u627e\u5230\u76f8\u5173\u8bbf\u5ba2')}</div>
                ) : (
                  <div className="divide-y divide-gray-100 bg-white rounded-md border border-gray-100">
                    {data.visitors.map(v => (
                      <div key={v.id} className="p-1">{renderVisitorItem(v)}</div>
                    ))}
                  </div>
                )}
                {data.visitor_pagination && data.visitor_pagination.total > data.visitors.length && (
                  <div className="mt-2">
                    <Pagination
                      currentPage={data.visitor_pagination.page}
                      totalPages={visitorTotalPages}
                      onPageChange={(p) => setVisitorPage(p)}
                    />
                  </div>
                )}
              </div>
            ) : (
              <div>
                {data.messages.length === 0 ? (
                  <div className="text-sm text-gray-400">{t('search.empty.messages', '\u672a\u627e\u5230\u76f8\u5173\u6d88\u606f')}</div>
                ) : (
                  <div className="divide-y divide-gray-100 bg-white rounded-md border border-gray-100">
                    {data.messages.map(m => (
                      <div key={m.message_id_str} className="p-1">{renderMessageItem(m)}</div>
                    ))}
                  </div>
                )}
                {data.message_pagination && data.message_pagination.total > data.messages.length && (
                  <div className="mt-2">
                    <Pagination
                      currentPage={data.message_pagination.page}
                      totalPages={messageTotalPages}
                      onPageChange={(p) => setMessagePage(p)}
                    />
                  </div>
                )}
              </div>
            )
          ) : (
            <div className="h-full flex items-center justify-center text-gray-400 text-sm">{t('search.emptyQueryHint', '输入关键词开始搜索')}</div>
          )}
        </div>
        <div className="px-4 py-2 border-t border-gray-100 text-xs text-gray-500 bg-white/60 backdrop-blur flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="hidden md:inline">{t('search.footer.tip', '小提示：')}</span>
            <span>{t('search.footer.escClose', 'Esc 关闭')}</span>
            <span>{t('search.footer.enterOpen', 'Enter 打开')}</span>
          </div>
          <div className="text-gray-400">{t('search.footer.summary', '搜索访客和消息')}</div>
        </div>
      </div>
    </div>,
    document.body
  );
};

export default SearchPanel;

