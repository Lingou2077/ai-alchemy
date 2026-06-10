import Taro from '@tarojs/taro'

export async function ensureAlbumAuth(): Promise<boolean> {
  try {
    const setting = await Taro.getSetting()
    if (setting.authSetting?.['scope.writePhotosAlbum']) {
      return true
    }
    await Taro.authorize({ scope: 'scope.writePhotosAlbum' })
    return true
  } catch {
    const result = await Taro.showModal({
      title: '需要相册权限',
      content: '请在设置中允许保存图片到相册',
      confirmText: '去设置',
    })
    if (result.confirm) {
      await Taro.openSetting()
      const next = await Taro.getSetting()
      return Boolean(next.authSetting?.['scope.writePhotosAlbum'])
    }
    return false
  }
}

export async function savePosterToAlbum(filePath: string): Promise<void> {
  const allowed = await ensureAlbumAuth()
  if (!allowed) {
    throw new Error('未获得相册权限')
  }
  await Taro.saveImageToPhotosAlbum({ filePath })
  Taro.showToast({ title: '已保存到相册', icon: 'success' })
}

export function sharePosterImage(filePath: string): void {
  const wxApi = (globalThis as { wx?: { showShareImageMenu?: (opts: { path: string }) => void } }).wx
  if (wxApi?.showShareImageMenu) {
    wxApi.showShareImageMenu({ path: filePath })
    return
  }
  Taro.showToast({ title: '请在微信小程序中使用', icon: 'none' })
}
