type TabIconName = 'home' | 'bank' | 'profile'

const ICON_PATHS: Record<TabIconName, string> = {
  home: '<path d="M4 10.5 12 4l8 6.5V19a1.5 1.5 0 0 1-1.5 1.5H15v-5.5H9V20.5H5.5A1.5 1.5 0 0 1 4 19v-8.5z"/>',
  bank: '<path d="M6 4.5h12a1.5 1.5 0 0 1 1.5 1.5v13A1.5 1.5 0 0 1 18 20.5H6A1.5 1.5 0 0 1 4.5 19V6A1.5 1.5 0 0 1 6 4.5z"/><path d="M8 8.5h8M8 12h8M8 15.5h5"/>',
  profile:
    '<circle cx="12" cy="8.5" r="3.2"/><path d="M5.5 19.5c0-3.2 2.9-5.5 6.5-5.5s6.5 2.3 6.5 5.5"/>',
}

export function getTabIconSrc(name: TabIconName, active: boolean): string {
  const stroke = active ? '#1a1a2e' : '#9a9ab0'
  const strokeWidth = active ? 2.2 : 1.8
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="${stroke}" stroke-width="${strokeWidth}" stroke-linecap="round" stroke-linejoin="round">${ICON_PATHS[name]}</svg>`
  return `data:image/svg+xml,${encodeURIComponent(svg)}`
}
