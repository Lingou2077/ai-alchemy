export interface OptionItem {
  key: string
  text: string
}

export interface Question {
  id: string
  type: 'single' | 'multiple' | 'boolean'
  difficulty: 'easy' | 'medium' | 'hard'
  stem: string
  options: OptionItem[]
  conceptTags: string[]
}

export interface Level {
  levelIndex: number
  questions: Question[]
}

export interface AnswerRecord {
  questionId: string
  userAnswer: string[]
  isCorrect: boolean
  timeSpent: number
  answeredAt: number
}

export interface SessionData {
  sessionId: string
  topic: string
  sourceContent: string
  createdAt: number
  status: 'generating' | 'playing' | 'completed' | 'failed'
  levels: Level[]
  hearts: number
  currentQuestionIndex: number
  answers: AnswerRecord[]
  startedAt: number
  finishedAt?: number
}

export interface WeakPoint {
  name: string
  reason: string
}

export interface ConceptNode {
  name: string
  mastery: 'mastered' | 'partial' | 'weak'
  relatedQuestionCount: number
}

export interface ReportStats {
  compareLastAccuracy?: number | null
  weeklyQuizIndex?: number | null
  relatedHistory?: QuizHistoryItem[]
}

export interface ExpGain {
  amount: number
  leveledUp: boolean
  newLevel: number
  newTitle: string
  levelBefore: number
}

export interface ReportData {
  sessionId: string
  topic: string
  accuracy: number
  totalQuestions: number
  correctCount: number
  wrongCount: number
  duration: number
  weakPoints: WeakPoint[]
  summary: string
  suggestion: string
  conceptMastery: ConceptNode[]
  expGain?: ExpGain | null
  stats?: ReportStats | null
  syncFailed?: boolean
}

export interface QuizHistoryItem {
  sessionId: string
  topic: string
  accuracy: number
  questionCount: number
  durationSec: number
  status: 'completed' | 'failed'
  finishedAt: string
}

export interface QuizHistoryDetail extends QuizHistoryItem {
  summary?: string | null
  suggestion?: string | null
  weakPoints?: WeakPoint[]
}

export interface WrongQuestionItem {
  id: number
  questionId: string
  topic: string
  stem: string
  difficulty: string
  wrongCount: number
  lastWrongAt: string
}

export interface WrongQuestionDetail extends WrongQuestionItem {
  options: OptionItem[]
  correctAnswer: string[]
  explanation: string
}

export interface HistoryItem {
  sessionId: string
  topic: string
  accuracy: number
  questionCount: number
  finishedAt: number
}
