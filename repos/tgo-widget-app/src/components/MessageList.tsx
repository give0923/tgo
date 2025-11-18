import { useEffect, useMemo, useRef } from 'react'
import styled from '@emotion/styled'
import type { ChatMessage } from '../types/chat'
import { formatMessageTime } from '../utils/time'
import { useChatStore } from '../store'
import { AlertCircle, RotateCw, Trash2 } from 'lucide-react'
import { ReasonCode } from 'easyjssdk'
import { Bubble, Cursor, TextMessage, ImageMessage, FileMessage, MixedMessage, MixedImages } from './messages'



const Main = styled.main`flex:1; min-height:0; overflow:auto; padding: 12px 12px 8px; background:#fff;`
const List = styled.ul`list-style:none; margin:0; padding:0; display:flex; flex-direction:column; gap:12px;`
const Row = styled.div<{self:boolean}>`
  display:flex; ${p => p.self ? 'justify-content:flex-end;' : 'justify-content:flex-start;'}
`

const Meta = styled.div`font-size: 12px; color: #6b7280; margin-top: 6px;`
const Status = styled('div')<{ self: boolean; kind: 'sending' | 'error' }>`
  font-size: 12px; margin-top: 6px; display:flex; align-items:center; gap:6px;
  ${p => p.self ? 'justify-content:flex-end;' : 'justify-content:flex-start;'}
  color: ${p => p.kind==='error' ? '#ef4444' : '#9ca3af'};
`
const LinkBtn = styled.button`
  border:0; background:transparent; color:inherit; cursor:pointer; padding:0 2px; text-decoration: underline;
`
const TopNotice = styled.li`
  list-style:none; text-align:center; color:#6b7280; font-size:12px; padding: 4px 0 8px;
`



export default function MessageList({ messages }: { messages: ChatMessage[] }){
  const ref = useRef<HTMLDivElement>(null)
  const items = useMemo(()=> messages.map(m => ({...m, key: m.id})), [messages])

  const historyLoading = useChatStore(s => s.historyLoading)
  const historyHasMore = useChatStore(s => s.historyHasMore)
  const historyError = useChatStore(s => s.historyError)
  const loadMore = useChatStore(s => s.loadMoreHistory)

  const reasonText = (code: ReasonCode) => {
    switch(code){
      case ReasonCode.AuthFail: return '认证失败，无法发送消息'
      case ReasonCode.SubscriberNotExist: return '非订阅者，无法发送消息'
      case ReasonCode.NotAllowSend: return '无权限发送消息'
      case ReasonCode.NotInWhitelist: return '当前不在白名单，无法发送'
      case ReasonCode.RateLimit: return '发送过于频繁，请稍后再试'
      case ReasonCode.Ban:
      case ReasonCode.SendBan: return '已被禁言，无法发送消息'
      case ReasonCode.ChannelNotExist:
      case ReasonCode.ChannelIDError: return '会话不存在或已失效'
      case ReasonCode.Disband: return '会话已解散'
      case ReasonCode.SystemError: return '系统错误，请稍后重试'
      case ReasonCode.Unknown:
      default: return '网络异常或超时，请检查网络后重试'
    }
  }
  const canRetry = (code: ReasonCode) => ![
    ReasonCode.AuthFail,
    ReasonCode.NotAllowSend,
    ReasonCode.NotInWhitelist,
    ReasonCode.Ban,
    ReasonCode.SendBan,
    ReasonCode.Disband,
  ].includes(code)

  const isAtBottomRef = useRef(true)
  const preHeightRef = useRef<number | null>(null)

  useEffect(()=>{
    const el = ref.current
    if(!el) return
    const onScroll = () => {
      if (!el) return
      const nearTop = el.scrollTop <= 16
      isAtBottomRef.current = (el.scrollTop + el.clientHeight) >= (el.scrollHeight - 16)
      if (nearTop && !historyLoading && historyHasMore) {
        preHeightRef.current = el.scrollHeight
        void loadMore()
      }
    }
    el.addEventListener('scroll', onScroll)
    return () => el.removeEventListener('scroll', onScroll)
  }, [historyLoading, historyHasMore, loadMore])

  useEffect(()=>{
    const el = ref.current
    if(!el) return
    if (preHeightRef.current != null) {
      const delta = el.scrollHeight - preHeightRef.current
      el.scrollTop = delta
      preHeightRef.current = null
    } else if (isAtBottomRef.current) {
      el.scrollTop = el.scrollHeight
    }
  }, [items])

  const retry = useChatStore(s => s.retryMessage)
  const retryUpload = useChatStore(s => s.retryUpload)
  const cancelUpload = useChatStore(s => s.cancelUpload)
  const remove = useChatStore(s => s.removeMessage)
  const staffCache = useChatStore(s => s.staffInfoCache)


  return (
    <Main ref={ref} role="log" aria-live="polite">
      <List>
        {/* top status row */}
        {historyLoading && <TopNotice>加载中…</TopNotice>}
        {!historyLoading && historyError && (
          <TopNotice style={{color:'#ef4444'}}>
            加载历史消息失败
            <button onClick={()=>loadMore()} style={{marginLeft:8, border:0, background:'transparent', color:'#ef4444', textDecoration:'underline', cursor:'pointer'}}>重试</button>
          </TopNotice>
        )}
        {!historyLoading && !historyError && !historyHasMore && <TopNotice>没有更多消息</TopNotice>}
        {items.map(m => (
          <li key={m.key}>
            <Row self={m.role==='user'}>
              {m.payload.type === 3 ? (
                <FileMessage url={m.payload.url} name={m.payload.name} size={m.payload.size} />
              ) : m.payload.type === 12 ? (
                <div style={{ display:'flex', flexDirection:'column', gap: 8, alignItems: 'flex-start' }}>
                  {(m.payload.content && m.payload.content.length>0) && (
                    <Bubble self={m.role==='user'}>
                      <MixedMessage content={m.payload.content} />
                    </Bubble>
                  )}
                  {(Array.isArray(m.payload.images) && m.payload.images.length>0) && (
                    <MixedImages images={m.payload.images} />
                  )}
                  {m.payload.file && (
                    <FileMessage url={m.payload.file.url} name={m.payload.file.name} size={m.payload.file.size} />
                  )}
                </div>
              ) : m.payload.type === 2 ? (
                <ImageMessage url={m.payload.url} w={m.payload.width} h={m.payload.height} />
              ) : (
                <Bubble self={m.role==='user'}>
                  {m.streamData && m.streamData.length ? (
                    <>
                      <TextMessage content={m.streamData} />
                      <Cursor />
                    </>
                  ) : (
                    m.payload.type === 1 ? (
                      <TextMessage content={m.payload.content} />
                    ) : (
                      <div>[消息]</div>
                    )
                  )}
                </Bubble>
              )}
            </Row>
            {m.role==='agent' && (
              <Meta>{(m.fromUid && staffCache[m.fromUid]?.name) || ''} - {formatMessageTime(m.time)}</Meta>
            )}
            {m.role==='user' && (
              <Meta style={{ textAlign: 'right' }}>{formatMessageTime(m.time)}</Meta>
            )}
            {m.role==='user' && m.status === 'sending' && (
              <Status self kind="sending">发送中…</Status>
            )}
            {m.role==='user' && m.status === 'uploading' && (
              <Status self kind="sending">
                上传中… {typeof m.uploadProgress === 'number' ? `${m.uploadProgress}%` : ''}
                <span>·</span>
                <LinkBtn onClick={()=>cancelUpload(m.id)} aria-label="取消">取消</LinkBtn>
              </Status>
            )}
            {m.role==='user' && typeof m.reasonCode === 'number' && m.reasonCode !== ReasonCode.Success && (
              <Status self kind="error">
                <AlertCircle size={14} /> {reasonText(m.reasonCode as ReasonCode)}
                {canRetry(m.reasonCode as ReasonCode) && (
                  <>
                    <LinkBtn onClick={()=>retry(m.id)} aria-label="重试"><RotateCw size={14} /> 重试</LinkBtn>
                    <span>·</span>
                  </>
                )}
                <LinkBtn onClick={()=>remove(m.id)} aria-label="删除"><Trash2 size={14} /> 删除</LinkBtn>
              </Status>
            )}
            {m.role==='user' && m.uploadError && (
              <Status self kind="error">
                <AlertCircle size={14} /> {m.uploadError}
                <LinkBtn onClick={()=>retryUpload(m.id)} aria-label="重试"><RotateCw size={14} /> 重试</LinkBtn>
                <span>·</span>
                <LinkBtn onClick={()=>remove(m.id)} aria-label="删除"><Trash2 size={14} /> 删除</LinkBtn>
              </Status>
            )}

          </li>
        ))}
      </List>
    </Main>
  )
}

