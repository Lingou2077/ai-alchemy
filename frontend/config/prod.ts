import type { UserConfigExport } from '@tarojs/cli'

export default {
  env: {
    API_BASE_URL: '"https://your-cloudrun-domain.com"',
  },
} satisfies UserConfigExport<'webpack5'>
