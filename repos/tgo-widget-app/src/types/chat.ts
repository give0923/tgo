import type { ReasonCode } from 'easyjssdk'

// Status is now used for transient states like uploading and sending.
export type MessageStatus = 'uploading' | 'sending'


// Message payload types (discriminated union)
export type TextMessagePayload = {
  type: 1
  content: string
}

export type ImageMessagePayload = {
  type: 2
  url: string
  width: number
  height: number
}

export type FileMessagePayload = {
  type: 3
  content: string
  url: string
  name: string
  size: number
}


export type MixedMessagePayload = {
  type: 12
  content: string
  images: Array<{
    url: string
    width: number
    height: number
  }>
  file?: {
    url: string
    name: string
    size: number
  }
}


export type CommandMessagePayload = {
  type: 99
  cmd: string
  param: Record<string, any>
}

export type MessagePayload = TextMessagePayload | ImageMessagePayload | FileMessagePayload | MixedMessagePayload | CommandMessagePayload

export type ChatMessage = {
  id: string
  role: 'agent' | 'user'
  payload: MessagePayload
  time: Date
  // Align with RecvMessage
  messageSeq?: number
  clientMsgNo?: string
  fromUid?: string
  channelId?: string
  channelType?: number
  // Incremental streaming data (if present, prefer displaying this)
  streamData?: string
  // Transient state while uploading/sending
  status?: MessageStatus
  // Upload progress & error (for attachments)
  uploadProgress?: number
  uploadError?: string
  // Final send result detail from SDK; Success/Failure codes
  reasonCode?: ReasonCode
}
