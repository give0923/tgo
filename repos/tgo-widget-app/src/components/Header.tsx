import React from 'react'
import styled from '@emotion/styled'
import { Maximize2, Minimize2 } from 'lucide-react'
import { usePlatformStore } from '../store'

const Bar = styled.header`
  display:flex; align-items:center; gap:8px; height: 56px; padding: 0 16px; border-bottom: 1px solid #eef2f4; background: #fff;
`
const Title = styled.div`
  flex:1; display:flex; align-items:center; gap:8px; font-weight: 600; color:#111827; font-size: 15px;
`
const Logo = styled.img`
  width:20px; height:20px; display:block;
`;

const IconBtn = styled.button`
  width: 32px; height: 32px; border-radius: 8px; border: 0; background: transparent; color: #6b7280; cursor: pointer;
  display: inline-flex; align-items: center; justify-content: center;
  &:hover { background: #f3f4f6; }
`
const ToggleExpand = styled(IconBtn)``

export default function Header({ title, onClose }: { title: string; onClose(): void }){
  const isExpanded = usePlatformStore(s => s.isExpanded)
  const toggleExpanded = usePlatformStore(s => s.toggleExpanded)
  const cfg = usePlatformStore(s => s.config)

  const requestClose = () => {
    try { (window.parent as any)?.TGOWidget?.hide?.(); } catch {}
    onClose && onClose();
  };
  return (
    <Bar>
      <Title>
        <Logo src={cfg?.logo_url || '/logo.svg'} alt="TGO logo" width={20} height={20} />
        {title}
      </Title>
      <ToggleExpand aria-label={isExpanded ? '收起窗口' : '展开窗口'} title={isExpanded ? '收起窗口' : '展开窗口'} onClick={toggleExpanded}>
        {isExpanded ? <Minimize2 size={16} /> : <Maximize2 size={16} />}
      </ToggleExpand>
      <IconBtn aria-label="Close" onClick={requestClose}>✕</IconBtn>
    </Bar>
  )
}

