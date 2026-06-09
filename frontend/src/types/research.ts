export type InputKind = 'keyword' | 'url' | 'mixed' | 'text'

export type DegradedMode = 'none' | 'no_web_results' | 'partial' | 'agent_timeout'

export interface TopicCandidate {
  id: string
  title: string
  summary: string
  sourceUrls: string[]
}

export interface ResearchResponse {
  researchSessionId: string
  candidates: TopicCandidate[]
  inputKind: InputKind
  degradedMode: DegradedMode
  mockMode?: boolean
  degradedMessage?: string | null
}

export const EXPLORE_ALL_TOPIC_ID = '__all__'
