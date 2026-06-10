import Taro from '@tarojs/taro'
import qrcode from 'qrcode-generator'

import { buildPosterShareUrl } from '@/config/app'
import type { ReportData, SessionData } from '@/types/session'
import { resolveQuizDurationSec } from '@/utils/formatTime'

export const POSTER_WIDTH = 750
export const POSTER_HEIGHT = 980
export const POSTER_CANVAS_ID = 'posterCanvas'

const COLORS = {
  page: '#F3F4F8',
  surface: '#FFFFFF',
  textPrimary: '#3D4A61',
  textSecondary: '#A0AEC0',
  purple: '#7B61FF',
  purpleSoft: 'rgba(123, 97, 255, 0.10)',
  greenLight: '#E8FAEC',
  greenDark: '#34C759',
  redLight: '#FFE8E8',
  red: '#FF6B6B',
  tagGood: '#E8FAEC',
  tagGoodText: '#34C759',
  tagPartial: '#FFF8E6',
  tagPartialText: '#D4920A',
  tagWeak: '#FFE8E8',
  tagWeakText: '#FF6B6B',
  divider: 'rgba(61, 74, 97, 0.08)',
  cardBorder: 'rgba(61, 74, 97, 0.10)',
  shadow: 'rgba(61, 74, 97, 0.16)',
}

const CARD = {
  x: 48,
  y: 48,
  w: 654,
  h: 884,
  radius: 32,
  padX: 36,
}

const FOOTER_HEIGHT = 156
const FOOTER_GAP = 32
const TAGS_BAR_GAP = 12
const TOPIC_FONT = 'bold 32px PingFang SC, sans-serif'
const TOPIC_LINE_HEIGHT = 40
const BRAND_FONT = 'bold 56px PingFang SC, sans-serif'
const BADGE_FONT = 'bold 32px PingFang SC, sans-serif'
const BADGE_HEIGHT = 48
const CARD_HEADER_PAD = 16
const MIN_HEADER_H = 72
const BADGE_SCORE_HEIGHT = 188
const MAIN_BLOCK_GAP = 28

interface CanvasContext {
  canvas: Taro.Canvas
  ctx: CanvasRenderingContext2D
  width: number
  height: number
}

interface TagItem {
  label: string
  tone: 'good' | 'partial' | 'weak'
}

function drawRoundedRect(
  ctx: CanvasRenderingContext2D,
  x: number,
  y: number,
  width: number,
  height: number,
  radius: number,
) {
  const r = Math.min(radius, width / 2, height / 2)
  ctx.beginPath()
  ctx.moveTo(x + r, y)
  ctx.arcTo(x + width, y, x + width, y + height, r)
  ctx.arcTo(x + width, y + height, x, y + height, r)
  ctx.arcTo(x, y + height, x, y, r)
  ctx.arcTo(x, y, x + width, y, r)
  ctx.closePath()
}

function wrapText(
  ctx: CanvasRenderingContext2D,
  text: string,
  maxWidth: number,
  maxLines: number,
): string[] {
  const lines: string[] = []
  let current = ''
  for (const char of text) {
    const next = current + char
    if (ctx.measureText(next).width > maxWidth && current) {
      lines.push(current)
      current = char
      if (lines.length >= maxLines) {
        const last = lines[lines.length - 1]
        lines[lines.length - 1] = last.length > 1 ? `${last.slice(0, -1)}…` : `${last}…`
        return lines
      }
    } else {
      current = next
    }
  }
  if (current) {
    lines.push(current)
  }
  return lines.slice(0, maxLines)
}

function truncateLabel(label: string, maxLen = 16): string {
  const trimmed = label.trim()
  if (trimmed.length <= maxLen) return trimmed
  return `${trimmed.slice(0, maxLen - 1)}…`
}

/** 微信小程序 Canvas 测量中文宽度不稳定，取整段与逐字测量的较大值 */
function measureCjkTextWidth(ctx: CanvasRenderingContext2D, text: string): number {
  ctx.textAlign = 'left'
  const wholeW = ctx.measureText(text).width
  let charW = 0
  for (const char of text) {
    charW += ctx.measureText(char).width
  }
  return Math.ceil(Math.max(wholeW, charW) + 2)
}

function drawCenteredBadgeText(
  ctx: CanvasRenderingContext2D,
  centerX: number,
  centerY: number,
  text: string,
  options: { font: string; color: string; height: number },
): number {
  ctx.save()
  ctx.font = options.font
  ctx.textAlign = 'left'
  ctx.textBaseline = 'middle'

  const textW = measureCjkTextWidth(ctx, text)
  const textX = centerX - textW / 2

  ctx.fillStyle = options.color
  ctx.fillText(text, textX, centerY)
  ctx.restore()

  return centerY + options.height / 2
}

function drawCenteredLines(
  ctx: CanvasRenderingContext2D,
  lines: string[],
  centerX: number,
  startY: number,
  lineHeight: number,
): number {
  ctx.save()
  ctx.textAlign = 'center'
  ctx.textBaseline = 'alphabetic'
  let y = startY
  for (const line of lines) {
    ctx.fillText(line, centerX, y)
    y += lineHeight
  }
  ctx.restore()
  return y
}

function drawQrCode(
  ctx: CanvasRenderingContext2D,
  text: string,
  x: number,
  y: number,
  size: number,
) {
  const qr = qrcode(0, 'M')
  qr.addData(text)
  qr.make()
  const count = qr.getModuleCount()
  const cellSize = size / count

  ctx.save()
  ctx.fillStyle = '#FFFFFF'
  drawRoundedRect(ctx, x - 8, y - 8, size + 16, size + 16, 16)
  ctx.fill()
  ctx.strokeStyle = COLORS.divider
  ctx.lineWidth = 2
  drawRoundedRect(ctx, x - 8, y - 8, size + 16, size + 16, 16)
  ctx.stroke()

  ctx.fillStyle = '#FFFFFF'
  ctx.fillRect(x, y, size, size)
  ctx.fillStyle = '#2D3748'
  for (let row = 0; row < count; row += 1) {
    for (let col = 0; col < count; col += 1) {
      if (qr.isDark(row, col)) {
        ctx.fillRect(x + col * cellSize, y + row * cellSize, cellSize, cellSize)
      }
    }
  }
  ctx.restore()
}

function pickTags(report: ReportData): TagItem[] {
  const tags: TagItem[] = []
  for (const item of report.conceptMastery) {
    if (tags.length >= 3) break
    tags.push({
      label: truncateLabel(item.name),
      tone: item.mastery === 'mastered' ? 'good' : item.mastery === 'partial' ? 'partial' : 'weak',
    })
  }
  for (const item of report.weakPoints) {
    if (tags.length >= 3) break
    const label = truncateLabel(item.name)
    if (!tags.some((tag) => tag.label === label)) {
      tags.push({ label, tone: 'weak' })
    }
  }
  return tags
}

function tagToneColors(tone: TagItem['tone']) {
  if (tone === 'good') return { bg: COLORS.tagGood, text: COLORS.tagGoodText }
  if (tone === 'partial') return { bg: COLORS.tagPartial, text: COLORS.tagPartialText }
  return { bg: COLORS.tagWeak, text: COLORS.tagWeakText }
}

function drawTagRows(
  ctx: CanvasRenderingContext2D,
  tags: TagItem[],
  anchorX: number,
  startY: number,
  maxRowWidth: number,
  align: 'left' | 'center' = 'center',
): number {
  if (tags.length === 0) return startY

  ctx.save()
  ctx.font = '22px PingFang SC, sans-serif'

  const tagPadX = 20
  const tagH = 44
  const gap = 12
  const rowGap = 14

  const rows: TagItem[][] = []
  let row: TagItem[] = []
  let rowW = 0

  for (const tag of tags) {
    const tagW = ctx.measureText(tag.label).width + tagPadX * 2
    const nextW = row.length === 0 ? tagW : rowW + gap + tagW
    if (nextW > maxRowWidth && row.length > 0) {
      rows.push(row)
      row = [tag]
      rowW = tagW
    } else {
      row.push(tag)
      rowW = nextW
    }
  }
  if (row.length > 0) rows.push(row)

  let y = startY
  for (const tagRow of rows) {
    const widths = tagRow.map((tag) => ctx.measureText(tag.label).width + tagPadX * 2)
    const totalW = widths.reduce((sum, w, i) => sum + w + (i > 0 ? gap : 0), 0)
    let x = align === 'center' ? anchorX - totalW / 2 : anchorX

    for (let i = 0; i < tagRow.length; i += 1) {
      const tag = tagRow[i]
      const tagW = widths[i]
      const colors = tagToneColors(tag.tone)
      ctx.fillStyle = colors.bg
      drawRoundedRect(ctx, x, y, tagW, tagH, 22)
      ctx.fill()
      ctx.fillStyle = colors.text
      ctx.textAlign = 'left'
      ctx.textBaseline = 'middle'
      ctx.fillText(tag.label, x + tagPadX, y + tagH / 2)
      x += tagW + gap
    }
    y += tagH + rowGap
  }

  ctx.restore()
  return y
}

function drawScoreCentered(
  ctx: CanvasRenderingContext2D,
  centerX: number,
  baselineY: number,
  accuracy: number,
) {
  ctx.save()
  const scoreText = String(Math.round(accuracy))
  ctx.font = 'bold 120px PingFang SC, sans-serif'
  const scoreW = ctx.measureText(scoreText).width
  ctx.font = 'bold 48px PingFang SC, sans-serif'
  const pctW = ctx.measureText('%').width
  const gap = 8
  const totalW = scoreW + gap + pctW
  const startX = centerX - totalW / 2

  ctx.fillStyle = COLORS.purple
  ctx.textAlign = 'left'
  ctx.textBaseline = 'alphabetic'
  ctx.font = 'bold 120px PingFang SC, sans-serif'
  ctx.fillText(scoreText, startX, baselineY)
  ctx.font = 'bold 48px PingFang SC, sans-serif'
  ctx.fillText('%', startX + scoreW + gap, baselineY - 10)
  ctx.restore()
}

function drawTopicStatsSection(
  ctx: CanvasRenderingContext2D,
  centerX: number,
  innerW: number,
  startY: number,
  topic: string,
  statsLine: string,
): number {
  ctx.save()
  ctx.fillStyle = COLORS.textPrimary
  ctx.font = TOPIC_FONT
  const topicLines = wrapText(ctx, topic, innerW, 2)
  let y = drawCenteredLines(ctx, topicLines, centerX, startY, TOPIC_LINE_HEIGHT)

  ctx.fillStyle = COLORS.textSecondary
  ctx.font = '26px PingFang SC, sans-serif'
  y = drawCenteredLines(ctx, [statsLine], centerX, y + 14, 32)
  ctx.restore()
  return y
}

function drawTagsSection(
  ctx: CanvasRenderingContext2D,
  centerX: number,
  innerW: number,
  startY: number,
  tags: TagItem[],
): number {
  if (tags.length === 0) return startY
  return drawTagRows(ctx, tags, centerX, startY, innerW, 'center')
}

function drawBrandTitle(ctx: CanvasRenderingContext2D, centerX: number, centerY: number): void {
  ctx.save()
  ctx.fillStyle = COLORS.purple
  ctx.font = BRAND_FONT
  ctx.textAlign = 'center'
  ctx.textBaseline = 'middle'
  ctx.fillText('AI炼金', centerX, centerY)
  ctx.restore()
}

function drawBadgeScoreSection(
  ctx: CanvasRenderingContext2D,
  centerX: number,
  startY: number,
  failed: boolean,
  accuracy: number,
): number {
  const badgeText = failed ? '灵韵散尽…' : '炼金成功！'
  const badgeCenterY = startY + BADGE_HEIGHT / 2

  const badgeBottom = drawCenteredBadgeText(ctx, centerX, badgeCenterY, badgeText, {
    font: BADGE_FONT,
    height: BADGE_HEIGHT,
    color: failed ? COLORS.red : COLORS.greenDark,
  })

  drawScoreCentered(ctx, centerX, badgeBottom + 100, accuracy)

  return badgeBottom + 118
}

function measureMainContentHeight(
  ctx: CanvasRenderingContext2D,
  innerW: number,
  topic: string,
  tags: TagItem[],
): number {
  const topicH = measureTopicStatsHeight(ctx, innerW, topic)
  const tagsH = measureTagsBlockHeight(ctx, tags, innerW)
  let height = BADGE_SCORE_HEIGHT + MAIN_BLOCK_GAP + topicH
  if (tags.length > 0) {
    height += MAIN_BLOCK_GAP + tagsH
  }
  return height
}

function measureAchievementBar(ctx: CanvasRenderingContext2D, innerW: number, tagline: string): number {
  const barPadX = 28
  const barPadY = 24
  ctx.save()
  ctx.font = 'bold 28px PingFang SC, sans-serif'
  const lines = wrapText(ctx, tagline, innerW - barPadX * 2, 2)
  ctx.restore()
  return lines.length * 36 + barPadY * 2
}

function drawAchievementBar(
  ctx: CanvasRenderingContext2D,
  innerLeft: number,
  innerW: number,
  centerX: number,
  startY: number,
  tagline: string,
): number {
  const barPadX = 28
  const barH = measureAchievementBar(ctx, innerW, tagline)

  ctx.save()
  ctx.font = 'bold 28px PingFang SC, sans-serif'
  const lines = wrapText(ctx, tagline, innerW - barPadX * 2, 2)
  ctx.restore()

  ctx.fillStyle = COLORS.purpleSoft
  drawRoundedRect(ctx, innerLeft, startY, innerW, barH, 20)
  ctx.fill()

  ctx.save()
  ctx.fillStyle = COLORS.purple
  ctx.font = 'bold 28px PingFang SC, sans-serif'
  const lineBlockH = lines.length * 36
  const textStartY = startY + (barH - lineBlockH) / 2 + 26
  drawCenteredLines(ctx, lines, centerX, textStartY, 36)
  ctx.restore()

  return startY + barH
}

function measureTopicStatsHeight(
  ctx: CanvasRenderingContext2D,
  innerW: number,
  topic: string,
): number {
  ctx.save()
  ctx.font = TOPIC_FONT
  const topicLines = wrapText(ctx, topic, innerW, 2)
  ctx.restore()
  return topicLines.length * TOPIC_LINE_HEIGHT + 46
}

function measureTagsBlockHeight(ctx: CanvasRenderingContext2D, tags: TagItem[], innerW: number): number {
  if (tags.length === 0) return 0
  ctx.save()
  ctx.font = '22px PingFang SC, sans-serif'
  const tagPadX = 20
  const tagH = 44
  const gap = 12
  const rowGap = 14
  let rowW = 0
  let rows = 1
  for (const tag of tags) {
    const tagW = ctx.measureText(tag.label).width + tagPadX * 2
    const nextW = rowW === 0 ? tagW : rowW + gap + tagW
    if (nextW > innerW && rowW > 0) {
      rows += 1
      rowW = tagW
    } else {
      rowW = nextW
    }
  }
  ctx.restore()
  return rows * tagH + (rows - 1) * rowGap
}

function drawFooter(
  ctx: CanvasRenderingContext2D,
  innerLeft: number,
  innerW: number,
  sessionId: string,
) {
  const footerTop = CARD.y + CARD.h - FOOTER_HEIGHT

  ctx.save()
  ctx.strokeStyle = COLORS.divider
  ctx.lineWidth = 1
  ctx.beginPath()
  ctx.moveTo(innerLeft, footerTop)
  ctx.lineTo(innerLeft + innerW, footerTop)
  ctx.stroke()
  ctx.restore()

  const qrSize = 120
  const qrX = innerLeft
  const qrY = footerTop + 24
  drawQrCode(ctx, buildPosterShareUrl(sessionId), qrX, qrY, qrSize)

  ctx.save()
  ctx.textAlign = 'left'
  ctx.textBaseline = 'alphabetic'
  ctx.fillStyle = COLORS.textPrimary
  ctx.font = 'bold 28px PingFang SC, sans-serif'
  ctx.fillText('扫码一起炼金', qrX + qrSize + 24, qrY + 40)
  ctx.fillStyle = COLORS.textSecondary
  ctx.font = '22px PingFang SC, sans-serif'
  ctx.fillText('长按识别二维码', qrX + qrSize + 24, qrY + 76)
  ctx.restore()

  ctx.save()
  ctx.translate(CARD.x + CARD.w - 52, qrY + qrSize - 4)
  ctx.rotate(-0.18)
  ctx.fillStyle = 'rgba(123, 97, 255, 0.18)'
  ctx.font = 'bold 36px PingFang SC, sans-serif'
  ctx.textAlign = 'center'
  ctx.textBaseline = 'middle'
  ctx.fillText('炼！', 0, 0)
  ctx.restore()
}

function drawCardBackground(ctx: CanvasRenderingContext2D, failed: boolean) {
  const { x, y, w, h, radius } = CARD

  ctx.fillStyle = COLORS.page
  ctx.fillRect(0, 0, POSTER_WIDTH, POSTER_HEIGHT)

  ctx.save()
  ctx.shadowColor = COLORS.shadow
  ctx.shadowBlur = 32
  ctx.shadowOffsetY = 10
  ctx.fillStyle = COLORS.surface
  drawRoundedRect(ctx, x, y, w, h, radius)
  ctx.fill()
  ctx.restore()

  ctx.save()
  ctx.strokeStyle = COLORS.cardBorder
  ctx.lineWidth = 1.5
  drawRoundedRect(ctx, x, y, w, h, radius)
  ctx.stroke()
  ctx.restore()

  ctx.save()
  drawRoundedRect(ctx, x, y, w, h, radius)
  ctx.clip()

  const bgGrad = ctx.createLinearGradient(x, y, x + w, y + h * 0.42)
  if (failed) {
    bgGrad.addColorStop(0, 'rgba(255, 107, 107, 0.07)')
    bgGrad.addColorStop(0.4, 'rgba(76, 217, 100, 0.04)')
    bgGrad.addColorStop(1, 'rgba(255, 255, 255, 0)')
  } else {
    bgGrad.addColorStop(0, 'rgba(123, 97, 255, 0.10)')
    bgGrad.addColorStop(0.4, 'rgba(76, 217, 100, 0.06)')
    bgGrad.addColorStop(1, 'rgba(255, 255, 255, 0)')
  }
  ctx.fillStyle = bgGrad
  ctx.fillRect(x, y, w, h)
  ctx.restore()
}

function drawPosterContent(
  ctx: CanvasRenderingContext2D,
  width: number,
  _height: number,
  report: ReportData,
  session: SessionData,
) {
  const failed = session.status === 'failed' || session.hearts <= 0
  const durationSec = resolveQuizDurationSec(session.answers, report.duration)
  const statsLine = `用时 ${durationSec} 秒 · 对 ${report.correctCount} 错 ${report.wrongCount}`
  const centerX = CARD.x + CARD.w / 2
  const innerW = CARD.w - CARD.padX * 2
  const innerLeft = CARD.x + CARD.padX
  const tags = pickTags(report)
  const tagline =
    report.shareTagline ||
    (failed ? '灵韵散尽，下次必成' : `${truncateLabel(report.topic, 10)}炼成成功！`)

  const barH = measureAchievementBar(ctx, innerW, tagline)
  const footerTop = CARD.y + CARD.h - FOOTER_HEIGHT
  const barY = footerTop - FOOTER_GAP - barH - 10
  const cardContentTop = CARD.y + CARD_HEADER_PAD
  const mainRegionBottom = barY - TAGS_BAR_GAP
  const mainBlockH = measureMainContentHeight(ctx, innerW, report.topic, tags)
  const mainRegionTop = cardContentTop + MIN_HEADER_H
  const mainStartY = mainRegionTop + Math.max(0, (mainRegionBottom - mainRegionTop - mainBlockH) / 2)
  const brandCenterY = cardContentTop + (mainStartY - cardContentTop) / 2

  ctx.clearRect(0, 0, width, POSTER_HEIGHT)
  drawCardBackground(ctx, failed)

  drawBrandTitle(ctx, centerX, brandCenterY)

  let y = mainStartY

  y = drawBadgeScoreSection(ctx, centerX, y, failed, report.accuracy)
  y += MAIN_BLOCK_GAP

  y = drawTopicStatsSection(ctx, centerX, innerW, y, report.topic, statsLine)

  if (tags.length > 0) {
    y += MAIN_BLOCK_GAP
    drawTagsSection(ctx, centerX, innerW, y, tags)
  }

  drawAchievementBar(ctx, innerLeft, innerW, centerX, barY, tagline)
  drawFooter(ctx, innerLeft, innerW, session.sessionId)
}

export function getPosterCanvasContext(canvasId = POSTER_CANVAS_ID): Promise<CanvasContext> {
  return new Promise((resolve, reject) => {
    Taro.nextTick(() => {
      const query = Taro.createSelectorQuery()
      query
        .select(`#${canvasId}`)
        .fields({ node: true, size: true })
        .exec((res) => {
          const result = res?.[0]
          if (!result?.node) {
            reject(new Error('Canvas 未就绪'))
            return
          }
          const canvas = result.node as Taro.Canvas
          const ctx = canvas.getContext('2d') as CanvasRenderingContext2D
          const dpr = Taro.getSystemInfoSync().pixelRatio || 2
          canvas.width = POSTER_WIDTH * dpr
          canvas.height = POSTER_HEIGHT * dpr
          ctx.scale(dpr, dpr)
          resolve({ canvas, ctx, width: POSTER_WIDTH, height: POSTER_HEIGHT })
        })
    })
  })
}

export async function renderPosterToTempFile(
  report: ReportData,
  session: SessionData,
  canvasId = POSTER_CANVAS_ID,
): Promise<string> {
  const { canvas, ctx, width, height } = await getPosterCanvasContext(canvasId)
  drawPosterContent(ctx, width, height, report, session)
  return exportPosterToTempFile(canvas, width, height)
}

export function exportPosterToTempFile(
  canvas: Taro.Canvas,
  width: number,
  height: number,
): Promise<string> {
  return new Promise((resolve, reject) => {
    Taro.canvasToTempFilePath({
      canvas,
      x: 0,
      y: 0,
      width,
      height,
      destWidth: width,
      destHeight: height,
      fileType: 'png',
      success: (res) => resolve(res.tempFilePath),
      fail: (err) => reject(err),
    })
  })
}
