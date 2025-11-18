import React from 'react';
import MarkdownContent from '../MarkdownContent';
import type { Message } from '@/types';
import { MessagePayloadType } from '@/types';

/**
 * TextMessage renders plain text messages.
 */
export interface MessageComponentProps {
  message: Message;
  isStaff: boolean; // true for staff (right), false for visitor (left)
}

const TextMessage: React.FC<MessageComponentProps> = ({ message, isStaff }) => {
  const typedPayload = message.payload as any | undefined;
  // Prefer message.content for streaming updates; fall back to payload content
  const textContent: string =
    (typeof message.content === 'string' && message.content.length > 0)
      ? message.content
      : ((typedPayload?.type === MessagePayloadType.TEXT && typeof typedPayload?.content === 'string')
          ? typedPayload.content
          : '');

  // Render streamed markdown only when has_stream_data flag exists
  const hasStreamData = Boolean(message.metadata?.has_stream_data);
  const shouldRenderMarkdown = hasStreamData;

  const hasLink = (message as any).hasLink;

  if (isStaff) {
    return (
      <div className="bg-blue-500 text-white p-3 rounded-lg rounded-tr-none shadow-sm">
        {shouldRenderMarkdown ? (
          <MarkdownContent content={textContent} className="text-sm markdown-white" />
        ) : (
          <p className="text-sm">
            {hasLink ? (
              <>
                {textContent.split('耳机连接指南')[0]}
                <a href="#" className="underline">耳机连接指南</a>
              </>
            ) : (
              textContent
            )}
          </p>
        )}
      </div>
    );
  }

  return (
    <div className="bg-white p-3 rounded-lg rounded-tl-none shadow-sm border border-gray-100">
      {shouldRenderMarkdown ? (
        <MarkdownContent content={textContent} className="text-sm" />
      ) : (
        <p className="text-sm text-gray-800">{textContent}</p>
      )}
    </div>
  );
};

export default TextMessage;

