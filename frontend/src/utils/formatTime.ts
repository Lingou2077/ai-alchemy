export function formatRelativeTime(iso: string): string {
  const date = new Date(iso)
  if (Number.isNaN(date.getTime())) return iso

  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24))

  if (diffDays <= 0) return '今天'
  if (diffDays === 1) return '昨天'
  if (diffDays < 7) return `${diffDays} 天前`
  return `${date.getMonth() + 1}月${date.getDate()}日`
}

export function formatDuration(seconds: number): string {
  const minutes = Math.floor(seconds / 60)
  const remain = seconds % 60
  return minutes > 0 ? `${minutes}分${remain}秒` : `${remain}秒`
}

/** 根据各题 timeSpent（毫秒）汇总实际答题用时（秒） */
export function computeAnswerDurationSec(answers: Array<{ timeSpent: number }>): number {
  if (!answers.length) return 0
  const totalMs = answers.reduce((sum, item) => sum + Math.max(0, item.timeSpent), 0)
  return Math.max(1, Math.ceil(totalMs / 1000))
}

/** 结算/分享页统一用时（秒）：仅汇总各题作答耗时 */
export function resolveQuizDurationSec(
  answers: Array<{ timeSpent: number }>,
  reportDuration: number,
): number {
  const fromAnswers = computeAnswerDurationSec(answers)
  if (fromAnswers > 0) return fromAnswers
  return Math.max(1, reportDuration)
}

export function accuracyRingClass(accuracy: number): 'good' | 'mid' | 'low' {
  if (accuracy >= 80) return 'good'
  if (accuracy >= 60) return 'mid'
  return 'low'
}

/** 分数环进度（0–360deg），用于 history-score-ring--progress */
export function accuracyRingProgressStyle(accuracy: number): Record<string, string> {
  const deg = Math.max(0, Math.min(100, accuracy)) * 3.6
  return { '--ring-deg': String(deg) }
}

/** 平均正确率卡片配色 */
export function accuracyStatClass(accuracy: number): 'good' | 'mid' | 'low' | 'neutral' {
  if (accuracy <= 0) return 'neutral'
  if (accuracy >= 80) return 'good'
  if (accuracy >= 60) return 'mid'
  return 'low'
}
