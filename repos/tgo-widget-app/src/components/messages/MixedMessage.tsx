import MarkdownContent from '../MarkdownContent'

export interface MixedMessageProps {
  content: string
}

export default function MixedMessage({ content }: MixedMessageProps){
  if (!content) return null
  return <MarkdownContent content={content} />
}

