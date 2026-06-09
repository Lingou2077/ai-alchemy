/**
 * 灵韵 · 炼金炉（玻璃三角瓶 · flat split-shade · 黄橙药液 + 浅蓝玻璃）
 * 对齐 prototypes/01-核心业务流程.html icon-flask-0 ~ icon-flask-3
 */
const VIEW_BOX = '0 -12 48 68'

const PATH_INNER = 'M 17.5 9 H 30.5 V 16 L 38 46 H 10 L 17.5 16 Z'
const PATH_WALL =
  'M 13 2 H 35 V 7 H 34 V 8 H 33 V 16 L 41 49 H 7 L 15 16 V 8 H 13 Z M 17.5 9 H 30.5 V 16 L 38 46 H 10 L 17.5 16 Z'
const PATH_OUTLINE =
  'M 13 2 H 35 V 7 H 34 V 8 H 33 V 16 L 41 49 H 7 L 15 16 V 8 H 13 Z'

function encodeSvg(svg: string): string {
  return `data:image/svg+xml,${encodeURIComponent(svg)}`
}

function defs(id: string): string {
  return `<defs>
<clipPath id="${id}-hl"><rect x="0" y="-12" width="24" height="68"/></clipPath>
<clipPath id="${id}-hr"><rect x="24" y="-12" width="24" height="68"/></clipPath>
<clipPath id="${id}-ic"><path d="${PATH_INNER}"/></clipPath>
</defs>`
}

function half(id: string, side: 'l' | 'r', inner: string): string {
  return `<g clip-path="url(#${id}-h${side})">${inner}</g>`
}

function wall(id: string): string {
  return `${half(id, 'l', `<path fill-rule="evenodd" d="${PATH_WALL}" fill="#E0F7FF"/>`)}${half(id, 'r', `<path fill-rule="evenodd" d="${PATH_WALL}" fill="#B3E5FC"/>`)}`
}

function outline(id: string): string {
  return `${half(id, 'l', `<path d="${PATH_OUTLINE}" fill="none" stroke="#9AD4EF" stroke-linejoin="round" stroke-width="0.85"/>`)}${half(id, 'r', `<path d="${PATH_OUTLINE}" fill="none" stroke="#7EC8E8" stroke-linejoin="round" stroke-width="0.85"/>`)}`
}

function liquid(
  id: string,
  fillPath: string,
  wavePath: string,
  bubblesL: string,
  bubblesR: string,
): string {
  return `<g clip-path="url(#${id}-ic)">
${half(id, 'l', `<path d="${fillPath}" fill="#FFD600"/>`)}${half(id, 'r', `<path d="${fillPath}" fill="#F5B800"/>`)}
${half(id, 'l', `<path d="${wavePath}" fill="none" stroke="#FF9100" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/>`)}${half(id, 'r', `<path d="${wavePath}" fill="none" stroke="#F57C00" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/>`)}
${half(id, 'l', `<g fill="#FF9100">${bubblesL}</g>`)}${half(id, 'r', `<g fill="#F57C00">${bubblesR}</g>`)}
</g>`
}

function sparklesFull(id: string): string {
  const shapes = `<circle cx="8" cy="8" r="4"/>
<circle cx="40" cy="8" r="4"/>
<rect x="22.6" y="0.2" width="2.8" height="6.5" rx="1.4"/>
<rect x="20.5" y="2.3" width="7" height="2.8" rx="1.4"/>
<rect x="15.6" y="4.8" width="2" height="4.5" rx="1" transform="rotate(-28 16.6 7.1)"/>
<rect x="29.6" y="4.8" width="2" height="4.5" rx="1" transform="rotate(28 30.6 7.1)"/>`
  return `<g transform="translate(0,-12)">${half(id, 'l', `<g fill="#FFD600">${shapes}</g>`)}${half(id, 'r', `<g fill="#F5B800">${shapes}</g>`)}</g>`
}

function sparklesMid(id: string): string {
  const shapes = `<circle cx="9" cy="9" r="3.2"/>
<circle cx="39" cy="9" r="3.2"/>
<rect x="22.6" y="1.2" width="2.8" height="5.5" rx="1.4"/>
<rect x="20.5" y="3.1" width="7" height="2.8" rx="1.4"/>`
  return `<g transform="translate(0,-12)">${half(id, 'l', `<g fill="#FFD600">${shapes}</g>`)}${half(id, 'r', `<g fill="#F5B800">${shapes}</g>`)}</g>`
}

function sparklesLow(id: string): string {
  const shapes = `<rect x="22.6" y="2.2" width="2.8" height="4.5" rx="1.4"/>
<rect x="20.5" y="4.1" width="7" height="2.8" rx="1.4"/>`
  return `<g transform="translate(0,-12)">${half(id, 'l', `<g fill="#FFD600">${shapes}</g>`)}${half(id, 'r', `<g fill="#F5B800">${shapes}</g>`)}</g>`
}

function buildFlaskSvg(level: 0 | 1 | 2 | 3): string {
  const id = `fl${level}`

  if (level === 0) {
    return encodeSvg(
      `<svg xmlns="http://www.w3.org/2000/svg" viewBox="${VIEW_BOX}">${defs(id)}
${half(id, 'l', `<path fill-rule="evenodd" d="${PATH_WALL}" fill="#D6ECF5"/>`)}${half(id, 'r', `<path fill-rule="evenodd" d="${PATH_WALL}" fill="#A8D4E8"/>`)}
${half(id, 'l', `<path d="${PATH_OUTLINE}" fill="none" stroke="#8EC4DC" stroke-linejoin="round" stroke-width="0.85"/>`)}${half(id, 'r', `<path d="${PATH_OUTLINE}" fill="none" stroke="#72B8D4" stroke-linejoin="round" stroke-width="0.85"/>`)}
<path d="M 18 28 L 20 34 L 18.5 40" stroke="#7EB8D4" stroke-width="1.2" fill="none" stroke-linecap="round"/>
<path d="M 30 26 L 28 33 L 29.5 39" stroke="#7EB8D4" stroke-width="1.2" fill="none" stroke-linecap="round"/>
<line x1="12" y1="44" x2="36" y2="44" stroke="#7EB8D4" stroke-width="1" opacity="0.6"/>
</svg>`,
    )
  }

  const levels = {
    3: {
      fill: 'M 13.75 31 Q 16.5 28.5 24 30 Q 31.5 31.5 34.25 31 L 37.2 46 H 10.8 Z',
      wave: 'M 13.75 31 Q 16.5 28.5 24 30 Q 31.5 31.5 34.25 31',
      bubblesL:
        '<ellipse cx="18" cy="37.5" rx="1.5" ry="2.6"/><ellipse cx="24" cy="38.5" rx="1.5" ry="2.6"/><ellipse cx="30" cy="37.5" rx="1.5" ry="2.6"/>',
      bubblesR:
        '<ellipse cx="18" cy="37.5" rx="1.5" ry="2.6"/><ellipse cx="24" cy="38.5" rx="1.5" ry="2.6"/><ellipse cx="30" cy="37.5" rx="1.5" ry="2.6"/>',
      sparkles: sparklesFull,
    },
    2: {
      fill: 'M 12.75 35 Q 15.5 33 24 34.2 Q 32.5 35.2 35.25 35 L 37.6 46 H 10.4 Z',
      wave: 'M 12.75 35 Q 15.5 33 24 34.2 Q 32.5 35.2 35.25 35',
      bubblesL: '<ellipse cx="19" cy="39" rx="1.4" ry="2.2"/><ellipse cx="29" cy="39" rx="1.4" ry="2.2"/>',
      bubblesR: '<ellipse cx="19" cy="39" rx="1.4" ry="2.2"/><ellipse cx="29" cy="39" rx="1.4" ry="2.2"/>',
      sparkles: sparklesMid,
    },
    1: {
      fill: 'M 11.75 39 Q 14.5 37.5 24 38.5 Q 33.5 39.5 36.25 39 L 38 46 H 10 Z',
      wave: 'M 11.75 39 Q 14.5 37.5 24 38.5 Q 33.5 39.5 36.25 39',
      bubblesL: '<ellipse cx="24" cy="40" rx="1.4" ry="2"/>',
      bubblesR: '<ellipse cx="24" cy="40" rx="1.4" ry="2"/>',
      sparkles: sparklesLow,
    },
  } as const

  const cfg = levels[level]
  return encodeSvg(
    `<svg xmlns="http://www.w3.org/2000/svg" viewBox="${VIEW_BOX}">${defs(id)}
${liquid(id, cfg.fill, cfg.wave, cfg.bubblesL, cfg.bubblesR)}
${wall(id)}
${outline(id)}
${cfg.sparkles(id)}
</svg>`,
  )
}

export function flaskFullDataUrl(): string {
  return buildFlaskSvg(3)
}

export const FLASK_SVG = {
  0: buildFlaskSvg(0),
  1: buildFlaskSvg(1),
  2: buildFlaskSvg(2),
  3: buildFlaskSvg(3),
} as const

export const FLASK_VIEW_WIDTH = 48
export const FLASK_VIEW_HEIGHT = 68
