import React, { useCallback, useMemo } from 'react';
import type { Chat } from '@/types';
import { useChatStore, chatSelectors } from '@/stores';
import { ChatListHeader } from '@/components/chat/ChatListHeader';
import { ChatListEmpty } from '@/components/chat/ChatListEmpty';
import { ChatListItem } from '@/components/chat/ChatListItem';

// ============================================================================
// Sub-Components (extracted into separate files)
// ============================================================================






// ============================================================================
// Main Component
// ============================================================================

/**
 * Props for the ChatList component
 */
interface ChatListProps {
  /** Currently active chat */
  activeChat?: Chat;
  /** Callback when a chat is selected */
  onChatSelect: (chat: Chat) => void;
}

/**
 * Custom hook for managing chat list filtering
 */
const useChatFiltering = (chats: Chat[], searchQuery: string) => {
  return useMemo(() => {
    if (!searchQuery.trim()) return chats;
    const lowerQuery = searchQuery.toLowerCase();
    return chats.filter((chat: Chat) => {
      const baseId = chat.channelId || chat.id;
      const name = (chat.channelInfo?.name || `访客${String(baseId).slice(-4)}`).toLowerCase();
      return name.includes(lowerQuery) || chat.lastMessage.toLowerCase().includes(lowerQuery);
    });
  }, [chats, searchQuery]);
};

/**
 * Chat list sidebar component
 * Displays a list of conversations with search and sync functionality
 *
 * Features:
 * - Search filtering by visitor name or last message
 * - Real-time sync with WuKongIM
 * - Empty state when no conversations exist
 * - Optimized rendering with memoized sub-components
 */
const ChatListComponent: React.FC<ChatListProps> = ({ activeChat, onChatSelect }) => {
  // Store subscriptions with stable selectors
  const chats = useChatStore(chatSelectors.chats);
  const searchQuery = useChatStore(chatSelectors.searchQuery);
  const setSearchQuery = useChatStore(state => state.setSearchQuery);
  const isSyncing = useChatStore(state => state.isSyncing);

  // Use custom hook for filtering
  const filteredChats = useChatFiltering(chats, searchQuery);

  // Memoized callbacks to prevent unnecessary re-renders
  const handleSearchChange = useCallback((value: string) => {
    setSearchQuery(value);
  }, [setSearchQuery]);



  return (
    <div className="w-72 bg-white/90 backdrop-blur-lg border-r border-gray-200/60 flex flex-col">
      {/* Header with search */}
      <ChatListHeader
        searchQuery={searchQuery}
        onSearchChange={handleSearchChange}
      />



      {/* Chat list */}
      <div className="flex-grow overflow-y-auto p-2 space-y-1" style={{ height: 0 }}>
        {filteredChats.length === 0 ? (
          <ChatListEmpty isSyncing={isSyncing} />
        ) : (
          filteredChats.map((chat: Chat) => (
            <ChatListItem
              key={chat.id}
              chat={chat}
              isActive={activeChat?.id === chat.id}
              onClick={onChatSelect}
            />
          ))
        )}
      </div>
    </div>
  );
};

// Wrap with React.memo to prevent unnecessary re-renders
const ChatList = React.memo(ChatListComponent);
ChatList.displayName = 'ChatList';

export default ChatList;
