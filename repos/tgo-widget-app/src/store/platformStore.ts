import { create } from 'zustand'
import type { PlatformConfig } from '../services/platform'
import { fetchPlatformInfo } from '../services/platform'
import { getJSON, setJSON } from '../utils/storage'

export type PlatformState = {
  loading: boolean
  error?: string | null
  config: Required<Pick<PlatformConfig, 'position' | 'theme_color' | 'widget_title'>> & {
    welcome_message?: string
    logo_url?: string
  }
  init: (apiBase: string, platformApiKey: string) => Promise<void>
  setConfig: (cfg: Partial<PlatformConfig>) => void
  updateThemeColor: (color: string) => void
  // expanded window state
  isExpanded: boolean
  toggleExpanded: () => void
  setExpanded: (v: boolean) => void
  welcomeInjected: boolean
  markWelcomeInjected: () => void
  // for persistence keying
  _apiBase?: string
  _platformApiKey?: string
}

const defaultConfig: PlatformState['config'] = {
  position: 'bottom-right',
  theme_color: '#2f80ed',
  widget_title: 'Tgo',
  welcome_message: undefined,
  logo_url: undefined,
}

const WELCOME_KEY = (apiBase: string, platformApiKey: string) => `tgo:welcome-shown:${apiBase}:${platformApiKey}`
const EXPANDED_KEY = (apiBase: string, platformApiKey: string) => `tgo:expanded:${apiBase}:${platformApiKey}`

export const usePlatformStore = create<PlatformState>((set, get) => ({
  loading: false,
  error: null,
  config: defaultConfig,
  isExpanded: false,
  welcomeInjected: false,
  _apiBase: undefined,
  _platformApiKey: undefined,

  setConfig: (cfg) => {
    const current = get().config
    set({ config: { ...current, ...cfg } as PlatformState['config'] })
  },

  updateThemeColor: (color: string) => {
    // validate color; fallback to default
    const c = (function normalize(col: string){
      try {
        const el = document?.createElement?.('div') as HTMLDivElement | undefined
        if (!el) return '#2f80ed'
        el.style.color = ''
        el.style.color = col as any
        return el.style.color ? col : '#2f80ed'
      } catch { return '#2f80ed' }
    })(color)
    set(s => ({ config: { ...s.config, theme_color: c }}))
  },

  setExpanded: (v: boolean) => {
    set({ isExpanded: !!v })
    try {
      const apiBase = get()._apiBase
      const apiKey = get()._platformApiKey
      if (apiBase && apiKey) setJSON(EXPANDED_KEY(apiBase, apiKey), !!v)
    } catch (_) { /* ignore */ }
  },
  toggleExpanded: () => {
    const cur = get().isExpanded
    get().setExpanded(!cur)
  },

  markWelcomeInjected: () => {
    set({ welcomeInjected: true })
    try {
      const apiBase = get()._apiBase
      const apiKey = get()._platformApiKey
      if (apiBase && apiKey) setJSON(WELCOME_KEY(apiBase, apiKey), true)
    } catch (_) { /* ignore storage errors */ }
  },

  init: async (apiBase: string, platformApiKey: string) => {
    if (!apiBase || !platformApiKey) return
    if (get().loading) return
    set({ loading: true, error: null, _apiBase: apiBase, _platformApiKey: platformApiKey })
    try {
      // read welcomeInjected & expanded from storage first
      try {
        const injected = !!getJSON<boolean>(WELCOME_KEY(apiBase, platformApiKey))
        if (injected) set({ welcomeInjected: true })
        const expanded = getJSON<boolean>(EXPANDED_KEY(apiBase, platformApiKey))
        if (typeof expanded === 'boolean') set({ isExpanded: expanded })
      } catch (_) { /* ignore */ }

      const info = await fetchPlatformInfo({ apiBase, platformApiKey })
      const cfg = (info?.config ?? {}) as PlatformConfig
      set(s => ({
        config: { ...s.config, ...cfg },
      }))
    } catch (e: any) {
      set({ error: e?.message || String(e) })
    } finally {
      set({ loading: false })
    }
  },
}))

export default usePlatformStore

