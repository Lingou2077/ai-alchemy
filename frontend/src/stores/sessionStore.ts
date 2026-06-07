import { create } from 'zustand'

import type { ReportData, SessionData } from '@/types/session'

interface SessionState {
  session: SessionData | null
  report: ReportData | null
  failMessage: string
  setSession: (session: SessionData | null) => void
  setReport: (report: ReportData | null) => void
  setFailMessage: (message: string) => void
  resetFlow: () => void
}

export const useSessionStore = create<SessionState>((set) => ({
  session: null,
  report: null,
  failMessage: '知识解析失败，请精简内容后重试',
  setSession: (session) => set({ session }),
  setReport: (report) => set({ report }),
  setFailMessage: (failMessage) => set({ failMessage }),
  resetFlow: () => set({ session: null, report: null }),
}))
