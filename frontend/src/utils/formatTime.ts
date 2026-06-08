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

export function accuracyRingClass(accuracy: number): 'good' | 'mid' | 'low' {
  if (accuracy >= 80) return 'good'
  if (accuracy >= 60) return 'mid'
  return 'low'
}
