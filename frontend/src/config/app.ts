export const POSTER_SHARE_LANDING_URL =
  process.env.POSTER_SHARE_LANDING_URL || 'https://example.com/ai-alchemy'

export function buildPosterShareUrl(sessionId: string): string {
  const base = POSTER_SHARE_LANDING_URL.replace(/\/$/, '')
  return `${base}?from=poster&session_id=${encodeURIComponent(sessionId)}`
}
