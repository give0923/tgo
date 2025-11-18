import React, { useEffect } from 'react';
import ChatList from '../components/layout/ChatList';
import ChatWindow from '../components/layout/ChatWindow';
import VisitorPanel from '../components/layout/VisitorPanel';
import { useChatStore, chatSelectors } from '@/stores';
import { getChannelKey } from '@/utils/channelUtils';

/**
 * Chat page component - contains the original chat interface
 */
const ChatPage: React.FC = () => {
  const activeChat = useChatStore(chatSelectors.activeChat);
  const setActiveChat = useChatStore(state => state.setActiveChat);
  const chats = useChatStore(state => state.chats);
  const syncConversations = useChatStore(state => state.syncConversations);
  const loadHistoricalMessages = useChatStore(state => state.loadHistoricalMessages);
  const clearConversationUnread = useChatStore(state => state.clearConversationUnread);

  // 页面加载时同步对话
  useEffect(() => {
    syncConversations();
  }, [syncConversations]);

  // 设置默认活跃聊天
  useEffect(() => {
    if (!activeChat && chats.length > 0) {
      setActiveChat(chats[0]);
    }
  }, [activeChat, chats.length, setActiveChat]);

  const handleChatSelect = (chat: any): void => {
    const prev = activeChat;

    // Clear unread for the conversation we're leaving (if different)
    if (prev && !(prev.channelId === chat.channelId && prev.channelType === chat.channelType)) {
      const prevInList = chats.find(c => c.channelId === prev.channelId && c.channelType === prev.channelType);
      if ((prevInList?.unreadCount || 0) > 0) {
        clearConversationUnread(prev.channelId, prev.channelType);
      }
    }

    // Clear unread for the clicked/active conversation
    const clickedInList = chats.find(c => c.channelId === chat.channelId && c.channelType === chat.channelType);
    if ((clickedInList?.unreadCount || 0) > 0) {
      clearConversationUnread(chat.channelId, chat.channelType);
    }

    setActiveChat(chat);
    // 加载历史消息（使用扁平化的 Chat 字段）
    if (chat.channelId && chat.channelType != null) {
      loadHistoricalMessages(chat.channelId, chat.channelType);
    }
  };


  // When returning focus to the tab/window, clear unread for the currently open conversation
  useEffect(() => {
    const onFocus = () => {
      const { activeChat: cur, chats: curChats, clearConversationUnread: clearFn } = useChatStore.getState() as any;
      if (cur?.channelId && cur.channelType != null) {
        const found = curChats.find((c: any) => c.channelId === cur.channelId && c.channelType === cur.channelType);
        if ((found?.unreadCount || 0) > 0) {
          clearFn(cur.channelId, cur.channelType);
        }
      }
    };
    window.addEventListener('focus', onFocus);
    return () => window.removeEventListener('focus', onFocus);
  }, []);

  return (
    <div className="flex h-full w-full">
      {/* Chat List */}
      <ChatList
        activeChat={activeChat}
        onChatSelect={handleChatSelect}
      />

      {/* Main Chat Window */}
      <ChatWindow
        key={activeChat ? getChannelKey(activeChat.channelId, activeChat.channelType) : 'no-active'}
        activeChat={activeChat}
      />



      {/* Visitor Info Panel */}
      <VisitorPanel activeChat={activeChat} />
    </div>
  );
};

export default ChatPage;
