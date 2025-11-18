import { useState } from 'react'
import { ImgBox, ImgEl } from './messageStyles'

export interface ImageMessageProps {
  url: string
  w: number
  h: number
}

export default function ImageMessage({ url, w, h }: ImageMessageProps){
  const [error, setError] = useState(false)
  const maxW = 280, maxH = 220
  const scale = Math.min(maxW / Math.max(1, w), maxH / Math.max(1, h), 1)
  const dw = Math.max(48, Math.round(w * scale))
  const dh = Math.max(48, Math.round(h * scale))
  return (
    <ImgBox
      style={{ width: dw, height: dh }}
      onClick={()=>{ try { window.open(url, '_blank') } catch {} }}
      title="点击查看原图"
      role="button"
      aria-label="查看原图"
    >
      {!error ? (
        <ImgEl src={url} alt="[图片]" loading="lazy" onError={()=>setError(true)} />
      ) : (
        <div style={{width:'100%',height:'100%',display:'grid',placeItems:'center', color:'#9ca3af', fontSize:12}}>图片加载失败</div>
      )}
    </ImgBox>
  )
}

