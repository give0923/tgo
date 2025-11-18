import { renderMarkdown } from '../../utils/markdown'

export interface TextMessageProps {
  content: string
}

export default function TextMessage({ content }: TextMessageProps){
  if (!content) return null
  return <div dangerouslySetInnerHTML={{ __html: renderMarkdown(content) }} />
}

