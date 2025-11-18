import styled from '@emotion/styled'

export const Bubble = styled.div<{self:boolean}>`
  display: inline-block; max-width: 280px; width: auto; padding: 0px 14px; border-radius: 16px; line-height: 1.5;
  background: ${p => p.self ? 'var(--primary)' : '#f5f6f7'}; color: ${p => p.self ? '#fff' : '#111827'};
  border-top-${p => p.self ? 'right' : 'left'}-radius: 6px;
  pre { overflow:auto; margin:8px 0; }
  code { font-family: ui-monospace,SFMono-Regular,Menlo,Monaco,Consolas,monospace; font-size: 12px; }
  a { color: ${p => p.self ? '#fff' : '#2563eb'}; text-decoration: underline; }
`

export const Cursor = styled.span`
  display:inline-block; width:6px; height:1em; margin-left:2px; background: currentColor;
  animation: blink 1s steps(1) infinite;
  @keyframes blink { 0%{opacity:1} 50%{opacity:0} 100%{opacity:1} }
`

export const ImgBox = styled.div`
  display:inline-block; background:#f3f4f6; border-radius:12px; overflow:hidden; padding:4px; cursor:pointer;
`;
export const ImgEl = styled.img`
  display:block; width:100%; height:100%; object-fit:contain; background:#f3f4f6;
`;

export const Grid = styled.div`
  display: grid; gap: 6px; width: 100%;
`;
export const GridItem = styled.div`
  position: relative; background:#f3f4f6; border-radius:8px; overflow:hidden; aspect-ratio:1/1; cursor:pointer;
`;
export const GridImg = styled.img`
  width:100%; height:100%; object-fit:cover; display:block; background:#f3f4f6;
`;

// File message UI
export const FileCard = styled.div`
  display:flex; align-items:center; gap:12px; padding:12px; border:1px solid #e5e7eb; border-radius:12px;
  background:#fff; color:#111827; max-width:280px; cursor:pointer; transition: box-shadow .15s ease, background-color .15s ease;
  &:hover{ box-shadow: 0 6px 20px rgba(0,0,0,.08); background:#f9fafb; }
`;
export const FileIconBox = styled.div`
  width:48px; height:48px; display:grid; place-items:center; border-radius:8px; background:#f3f4f6; flex:0 0 auto;
`;
export const FileInfo = styled.div`
  flex:1; min-width:0; display:flex; flex-direction:column; gap:4px;
`;
export const FileName = styled.div`
  font-size:14px; color:#111827; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;
`;
export const FileSize = styled.div`
  font-size:12px; color:#6b7280;
`;
export const FileAction = styled.a`
  color:#6b7280; flex:0 0 auto; display:grid; place-items:center; padding:4px; border-radius:6px; text-decoration:none;
  &:hover{ background:#f3f4f6; }
`;

