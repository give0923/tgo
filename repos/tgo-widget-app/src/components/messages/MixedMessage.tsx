import { renderMarkdown } from '../../utils/markdown'

export interface MixedMessageProps {
  content: string
}

export default function MixedMessage({ content }: MixedMessageProps){
  if (!content) return null
  return <div dangerouslySetInnerHTML={{ __html: renderMarkdown(content) }} />
}

