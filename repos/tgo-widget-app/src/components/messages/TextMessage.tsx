import MarkdownContent from '../MarkdownContent'

export interface TextMessageProps {
  content: string
}

export default function TextMessage({ content }: TextMessageProps){
  if (!content) return null
  return <MarkdownContent content={content} />
}

